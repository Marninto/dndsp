import ast
import asyncio
import json
import math
import os
import random
from copy import deepcopy

import discord

from embed_wrapper import EmbedMsg
from constants import dnd_ability_map, skill_ability_map, dnd_class_proficiency_map
from html_img_converter import render_and_capture_html, render_and_capture_html_with_cache
from intent_interface import PageIntent
from mapping import proficiency_map
from model import check_onboard_status, check_player_chars, generate_quickbuild_character, get_score_modifier, \
    get_class_id_from_name, get_char_ability_details, fetch_race_ability_and_id_map, generate_custom_char, \
    update_char_gen_progress, fetch_bg_ability_and_id_map
from utilities import generate_name_local, dice_roll


class PlayerChar:
    def __init__(self, ctx):
        self.ctx = ctx
        self.enrolled = self.check_enroll()
        if not self.enrolled:
            self.ctx.send('Please enroll with !enroll command first')
        self.char_id = 0
        self.creation_stage = 0
        self.character_data = {}

    def check_enroll(self):
        return check_onboard_status(self.ctx.author.id)

    def check(self, msg):
        return msg.author == self.ctx.author and msg.channel == self.ctx.channel

    async def roll_build_char(self, bot, char_id, creation_stage):
        if not self.character_data and char_id:
            char_data = get_char_ability_details(char_id)
            self.character_data = json.loads(char_data) if char_data else {}
        if char_id:
            self.char_id = char_id
        if creation_stage:
            self.creation_stage = creation_stage
        if not self.creation_stage:
            await self.generate_char_phase_one(bot)
        if self.creation_stage == 1:
            await self.generate_char_race(bot)
        if self.creation_stage == 2:
            await self.generate_char_bg(bot)
        if self.creation_stage == 3:
            await self.generate_char_proficiency(bot)
        if self.creation_stage == 4:
            async def char_sheet_ability_coro():
                return await self.char_sheet_ability(bot=bot, char_id=char_id, user_id=self.ctx.author.id)

            async def char_skill_data_coro():
                return await self.char_skill_data(bot=bot, char_id=char_id, user_id=self.ctx.author.id)

            # Use the defined coroutines in a list
            functions = [char_sheet_ability_coro, char_skill_data_coro]
            view = PageIntent(bot, functions, char_id, self.ctx.author.id)
            await view.send_initial_message(self.ctx)

    # phase one makes the first entry in db. no update before this is permanent
    async def generate_char_phase_one(self, bot):
        def check(msg):
            return msg.author == self.ctx.author and msg.channel == self.ctx.channel

        # Ask for character name
        await self.ctx.send('Please enter character name:')
        name = await bot.wait_for('message', check=check)
        character_name = name.content

        character_data = {'name': character_name, 'char_name': character_name}
        ability_list = list(dnd_ability_map.keys())
        ability_list.append('HP')
        # Rolling for abilities
        roll_view = CharacterRollView(character_data, ability_list, self.ctx.author)
        await self.ctx.send('Roll for abilities:', view=roll_view)

        # Wait for all buttons to be disabled (i.e., all abilities rolled)
        await roll_view.wait_until_all_disabled()
        custom_ability_map = {}
        for ability, value in dnd_ability_map.items():
            custom_ability_map[ability] = character_data.get(ability)
        self.character_data = character_data

        char_id = generate_custom_char(custom_ability_map, character_data['name'], character_data['HP'], self.enrolled)
        self.creation_stage = 1
        self.char_id = char_id
        await self.ctx.send(f"Character base generated\nName: {character_data['name']}\nCharacter ID: {char_id}")
        return char_id

    async def generate_char_race(self, bot):
        race_ability_map, race_id_map = fetch_race_ability_and_id_map()
        data = self.categorize_races('INT', race_ability_map)

        image_link = await render_and_capture_html_with_cache(bot=bot, data=data, cache=True,
                                                              image_path=f'INT_RACE_IMG.png',
                                                              template_path='html_templates/char_race.html',
                                                              size=(600, 715), cache_name="INT_RACE_IMG")

        # Sending the image in Discord embed
        embed = discord.Embed(title="Race Selection")
        embed.set_image(url=image_link)
        await self.ctx.send(embed=embed)

        while True:
            try:
                race_msg = await bot.wait_for('message', check=self.check, timeout=60)
                user_race = race_msg.content.strip().lower()
                if user_race == "random":
                    matched_race = random.choice(list(race_ability_map.keys()))
                else:
                    matched_race = next((race for race in race_ability_map.keys() if race.lower() == user_race), None)

                if matched_race:
                    self.character_data['race'] = matched_race
                    break
                else:
                    await self.ctx.send(f'{self.ctx.author.mention} Invalid input, please type a valid race.')
            except asyncio.TimeoutError:
                await self.ctx.send(f'{self.ctx.author.mention} No input received. Please try again')
                return

        update_char_gen_progress(self.char_id, "race_id", race_id_map[self.character_data['race']],
                                 self.creation_stage)
        update_char_gen_progress(self.char_id, "ability_score_improve",
                                 json.loads(race_ability_map[self.character_data['race']]), self.creation_stage + 1)
        self.creation_stage += 1
        await self.ctx.send(f'Race Selected: {self.character_data["race"]}')

    @classmethod
    def categorize_races(cls, ability, race_ability_map):
        recommended_races = {}
        other_races = {}

        for race, abilities_json in race_ability_map.items():
            abilities = json.loads(abilities_json)

            # Title casing the race and formatting abilities
            formatted_race = race.title()
            formatted_abilities = ', '.join(f'{k}: +{v}' for k, v in abilities.items())

            # Check if the specified ability has an improvement of more than +1
            if abilities.get(ability, 0) > 1:
                recommended_races[formatted_race] = formatted_abilities
            else:
                other_races[formatted_race] = formatted_abilities

        return {
            "race_map": recommended_races,
            "other_race_map": other_races
        }

    async def generate_char_bg(self, bot):
        bg_ability_map, bg_id_map = fetch_bg_ability_and_id_map()
        data = self.categorize_backgrounds('INT', bg_ability_map)

        image_link = await render_and_capture_html_with_cache(bot=bot, data=data, cache=True,
                                                              image_path=f'INT_BG_IMG.png',
                                                              template_path='html_templates/char_bg.html',
                                                              size=(600, 645), cache_name="INT_BG_IMG")

        # Sending the image in Discord embed
        embed = discord.Embed(title="Background Selection")
        embed.set_image(url=image_link)
        await self.ctx.send(embed=embed)
        try:
            bg_msg = await bot.wait_for('message', check=self.check, timeout=30)

            user_bg = bg_msg.content.strip().lower()
            if user_bg == "random":
                matched_bg = random.choice(list(bg_ability_map.keys()))
            else:
                matched_bg = next((race for race in bg_ability_map.keys() if race.lower() == user_bg), None)

            if matched_bg:
                self.character_data['background'] = matched_bg
                update_char_gen_progress(self.char_id, "background_id", bg_id_map[matched_bg], self.creation_stage)
                update_char_gen_progress(self.char_id, "picked_proficiencies", json.dumps(bg_ability_map[matched_bg]),
                                         self.creation_stage + 1)
                self.creation_stage += 1

                await self.ctx.send(f'Background selected for {self.character_data.get("char_name")}: {matched_bg}')
        except asyncio.TimeoutError:
            await self.ctx.send(f'{self.ctx.author.mention} No input received. Please try again.')
        return

    async def generate_char_proficiency(self, bot):
        picked_proficiencies = []  # To store the picked proficiencies
        char_data_str = get_char_ability_details(self.char_id)
        char_data = json.loads(char_data_str)
        proficiencies = json.loads(char_data['picked_proficiencies'])
        picked_proficiencies.extend(proficiencies)

        while len(picked_proficiencies) < 4:
            data = self.categorize_proficiencies(picked_proficiencies)
            picked_proficiencies_str = '_'.join(picked_proficiencies)

            image_link = await render_and_capture_html_with_cache(bot=bot, data=data, cache=True,
                                                                  image_path=f'{picked_proficiencies_str}_proficiency.png',
                                                                  template_path='html_templates/char_prof.html',
                                                                  size=(600, 520),
                                                                  cache_name=picked_proficiencies_str + '_proficiency')

            # Sending the image in Discord embed
            embed = discord.Embed(title="Proficiency Selection")
            embed.set_image(url=image_link)
            await self.ctx.send(embed=embed)

            try:
                prof_msg = await bot.wait_for('message', check=self.check, timeout=30)
                user_prof = prof_msg.content.strip().title()

                if user_prof == "Random":
                    new_proficiencies = random.sample(proficiency_map, 2 - len(picked_proficiencies))
                    picked_proficiencies.extend(new_proficiencies)
                else:

                    matched_prof = next(
                        (prof for prof in (data['recommended_proficiencies'] + data['other_proficiencies']) if
                         prof == user_prof), None)
                    if matched_prof and (matched_prof.title() not in picked_proficiencies):
                        picked_proficiencies.append(matched_prof)
                        data['recommended_proficiencies'] = [prof for prof in data['recommended_proficiencies'] if
                                                             prof.title() != matched_prof.title()]
                        data['other_proficiencies'] = [prof for prof in data['other_proficiencies'] if
                                                       prof.title() != matched_prof.title()]
                    elif not matched_prof:
                        await self.ctx.send(
                            f"{self.ctx.author.mention} The proficiency {user_prof} has already been picked. Please choose another.")
                        continue
                    else:
                        await self.ctx.send(f'{self.ctx.author.mention} Please choose valid option')
                        continue

            except asyncio.TimeoutError:
                await self.ctx.send(f'{self.ctx.author.mention} No input received. Please try again.')
                return

        update_char_gen_progress(self.char_id, "picked_proficiencies", json.dumps(picked_proficiencies),
                                 self.creation_stage + 1)
        self.creation_stage += 1
        await self.ctx.send('Final Proficiencies: ' + ', '.join(picked_proficiencies))

    @classmethod
    def categorize_proficiencies(cls, picked_proficiencies, recommended_ability='INT'):
        recommended_proficiencies = []
        other_proficiencies = []
        picked = []

        for proficiency in proficiency_map.keys():
            formatted_proficiency = proficiency.title()  # Title casing the proficiency

            if proficiency in picked_proficiencies:
                picked.append(formatted_proficiency)
            elif proficiency_map[proficiency] == recommended_ability:
                recommended_proficiencies.append(formatted_proficiency)
            else:
                other_proficiencies.append(formatted_proficiency)

        return {
            "recommended_proficiencies": recommended_proficiencies,
            "other_proficiencies": other_proficiencies,
            "picked_proficiencies": picked
        }

    @classmethod
    def categorize_backgrounds(cls, ability, bg_ability_map):
        background_map = {}
        other_background_map = {}

        # Define which abilities are related to each attribute for categorization
        ability_related_skills = {
            'INT': ['Arcana', 'History', 'Investigation', 'Nature', 'Religion'],
            'WIS': ['Animal Handling', 'Insight', 'Medicine', 'Perception', 'Survival'],
        }

        for background, abilities in bg_ability_map.items():
            # Title casing the background and abilities
            formatted_background = background.title()
            formatted_abilities = ', '.join([a.title() for a in abilities])

            # Check if any ability related to the chosen attribute is in the abilities list
            if any(skill in abilities for skill in ability_related_skills.get(ability, [])):
                background_map[formatted_background] = formatted_abilities
            else:
                other_background_map[formatted_background] = formatted_abilities

        return {
            "background_map": background_map,
            "other_background_map": other_background_map
        }

    def quick_build_char(self):
        try:
            name = generate_name_local()
            ability_map = deepcopy(dnd_ability_map)
            for ability, score in ability_map.items():
                ability_rolls = dice_roll(4, 6, 0, 3, 0)
                ability_map[ability] = sum(ability_rolls)
            class_name = 'Wizard'
            class_id = get_class_id_from_name(class_name)
            race_id = random.randint(1, 18)
            background_id = random.randint(1, 13)
            player_id = self.enrolled
            proficiencies = dnd_class_proficiency_map[class_name]['skill_proficiencies']
            if type(proficiencies) == str:
                proficiencies = list(skill_ability_map.keys())
            random.shuffle(proficiencies)
            picked_proficiency = ', '.join(proficiencies[:dnd_class_proficiency_map[class_name]['pick_options']])
            race_ability_score = get_score_modifier(race_id)
            ability_score = {}
            for ability, score in race_ability_score.items():
                if ability in ['ANY1', 'ANY2']:
                    picked_ability = list(dnd_ability_map.keys())[random.randint(0, 5)]
                    ability_score[picked_ability] = score
                else:
                    ability_score[ability] = score
            max_hp = dice_roll(1, 6, 0, 0, 0)[0]
            generate_quickbuild_character(ability_map, ability_score, picked_proficiency, player_id, race_id, class_id,
                                          background_id, name, max_hp)
            return True
        except Exception as e:
            return False

    def fetch_latest_char_id(self, user_id):
        player_data = json.loads(check_player_chars(user_id))
        if not player_data['success']:
            if 'player_id' in player_data and player_data['player_id'] == 0:
                return 0, 0
            else:
                char_id = player_data.get('player_id')
        else:
            char_id = player_data['player_id']
        return char_id, player_data.get('creation_stage', 0)

    async def char_skill_data(self, bot, char_id=None, user_id=None):
        if char_id is None:
            char_id, _ = self.fetch_latest_char_id(user_id=user_id)
            if not char_id:
                return "No character found"
        char_data = json.loads(get_char_ability_details(char_id))

        ability_map = json.loads(char_data['ability_map'])
        ability_score_improve = json.loads(char_data['ability_score_improve']) if char_data['ability_score_improve'] and \
                                                                                  char_data[
                                                                                      'ability_score_improve'] != "None" else {}
        ability_map_modifier = deepcopy(ability_map)
        for ability, modifier in ability_score_improve.items():
            ability_map_modifier[ability] += modifier

        for ability, score in ability_map_modifier.items():
            ability_map_modifier[ability] = math.floor(score / 2) - 5
        skill_modifier_map = deepcopy(skill_ability_map)
        for skill, ability in skill_modifier_map.items():
            skill_modifier_map[skill] = ability_map_modifier[ability]

        picked_proficiencies = json.loads(char_data['picked_proficiencies']) if char_data[
            'picked_proficiencies'] else []
        proficiency_list = []
        if picked_proficiencies:
            proficiency_list = ast.literal_eval(char_data['proficiency_list'])

        for skill in (picked_proficiencies + proficiency_list):
            skill_modifier_map[skill] += 2
        saving_modifier_map = deepcopy(ability_map_modifier)
        for ability in ast.literal_eval(char_data['saving_throw_proficiency']):
            saving_modifier_map[ability] += 2
        char_sheet_data = {
            'name': char_data['char_name'],
            'skill_modifier_map': skill_modifier_map,
            'class_name': char_data['class_name'],
            'race_name': char_data['race_name']
        }
        char_sheet = EmbedMsg().char_skill_info(**char_sheet_data)
        return char_sheet

    async def char_sheet_ability(self, bot, char_id=None, user_id=None):
        if char_id is None:
            char_id, _ = self.fetch_latest_char_id(user_id=user_id)
            if not char_id:
                return discord.Embed(
                    title=f'Create character using !create or view others char using !ci <char_id>')
        char_data = get_char_ability_details(char_id)
        if not char_data:
            return discord.Embed(title=f'Character id selected does not exist. Use !ci instead')
        char_data = json.loads(char_data)
        ability_map = json.loads(char_data['ability_map'])
        ability_score_improve = json.loads(char_data['ability_score_improve']) if char_data.get(
            'ability_score_improve') else {}
        ability_map_modifier = deepcopy(ability_map)
        for ability, modifier in ability_score_improve.items():
            ability_map_modifier[ability] += modifier

        for ability, score in ability_map_modifier.items():
            ability_map_modifier[ability] = math.floor(score / 2) - 5
        skill_modifier_map = deepcopy(skill_ability_map)
        for skill, ability in skill_modifier_map.items():
            skill_modifier_map[skill] = ability_map_modifier[ability]

        picked_proficiencies = json.loads(char_data['picked_proficiencies']) if char_data[
            'picked_proficiencies'] else []
        proficiency_list = ast.literal_eval(char_data['proficiency_list']) if char_data['proficiency_list'] else []

        for skill in (picked_proficiencies + proficiency_list):
            skill_modifier_map[skill] += 2
        saving_modifier_map = deepcopy(ability_map_modifier)
        for ability in ast.literal_eval(char_data['saving_throw_proficiency']):
            saving_modifier_map[ability] += 2
        template_data = {
            'Character_Name': char_data['char_name'].title(),
            'Race_Class': f"{char_data['race_name']} {char_data['class_name']}",
            'Background': char_data['bg_name'],
            'AC': 10 + ability_map_modifier['DEX'],
            'Max_HP': char_data['max_hp'],
            'Initiative': ability_map_modifier['DEX'],  # Assuming DEX modifier is used for initiative
            'ability_map': ability_map_modifier,
            'save_ability_map': saving_modifier_map,
            'PATH_TO_IMAGE': "https://media.discordapp.net/attachments/1072097225058037782/1102567866869489674/fizban.jpg?width=330&height=520"
        }
        image_link = await render_and_capture_html_with_cache(bot=bot, data=template_data, cache=True,
                                                              image_path=f'char_sheet_{char_id}.png',
                                                              template_path='html_templates/char_sheet.html',
                                                              size=(600, 550),
                                                              cache_name=f'char_sheet_{char_id}')

        embed = discord.Embed()
        embed.set_image(url=image_link)
        return embed


class CharacterRollButton(discord.ui.Button):
    def __init__(self, ability, character_data, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.ability = ability
        self.character_data = character_data

    async def callback(self, interaction):
        if interaction.user != self.user:
            return
        if self.ability == 'HP':
            roll_value = dice_roll(1, 6, math.floor(self.character_data['CON'] / 2) - 5, 0, 0)[0]
        else:
            dice_roll_value = dice_roll(4, 6, 0, 3, 0)
            roll_value = 0
            for roll in dice_roll_value:
                roll_value += roll
            if self.ability == 'CON':
                hp_button = next((item for item in self.view.children if item.custom_id == "HP"), None)
                hp_button.disabled = False
        self.character_data[self.ability] = roll_value
        self.label = f"Rolled {self.ability}: {roll_value}"
        self.disabled = True
        self.style = discord.ButtonStyle.success
        await interaction.response.defer()
        await interaction.message.edit(view=self.view)


class CharacterRollView(discord.ui.View):
    def __init__(self, character_data, abilities, user):
        super().__init__(timeout=120)
        self.user = user
        for ability in abilities:
            self.add_item(
                CharacterRollButton(ability=ability, character_data=character_data, user=user, custom_id=ability,
                                    label=f"Roll for {ability}", disabled=True if ability == 'HP' else False))

    async def wait_until_all_disabled(self):
        while not all(item.disabled for item in self.children):
            await asyncio.sleep(1)
