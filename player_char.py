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
from html_img_converter import render_and_capture_html
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
            self.char_sheet_ability(self.char_id)

    # phase one makes the first entry in db. no update before this is permanent
    async def generate_char_phase_one(self, bot):
        def check(msg):
            return msg.author == self.ctx.author and msg.channel == self.ctx.channel

        # Ask for character name
        await self.ctx.send('Please enter character name:')
        name = await bot.wait_for('message', check=check)
        character_name = name.content

        character_data = {'name': character_name}
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

        image_link_or_path = render_and_capture_html(data=data,
                                                     cache=False, image_path=f'race_selection_{self.char_id}.png',
                                                     template_path='html_templates/char_race.html', size=(600, 715))

        # Sending the image in Discord embed
        embed = discord.Embed(title="Race Selection")
        if os.path.exists(image_link_or_path):
            file = discord.File(image_link_or_path, filename=f"background_selection_{self.char_id}.png")
            embed.set_image(url=f"attachment://background_selection_{self.char_id}.png")
            await self.ctx.send(file=file, embed=embed)
            os.remove(image_link_or_path)
        else:  # If it's a URL
            embed.set_image(url=image_link_or_path)
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
                    await self.ctx.send('Invalid input, please type a valid race.')
            except asyncio.TimeoutError:
                await self.ctx.send('No input received. Please try again')
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

        image_link_or_path = render_and_capture_html(data=data,
                                                     cache=False, image_path=f'background_selection_{self.char_id}.png',
                                                     template_path='html_templates/char_bg.html', size=(600, 645))

        # Sending the image in Discord embed
        embed = discord.Embed(title="Background Selection")
        if os.path.exists(image_link_or_path):
            file = discord.File(image_link_or_path, filename=f"background_selection_{self.char_id}.png")
            embed.set_image(url=f"attachment://background_selection_{self.char_id}.png")
            await self.ctx.send(file=file, embed=embed)
            os.remove(image_link_or_path)
        else:  # If it's a URL
            embed.set_image(url=image_link_or_path)
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

                await self.ctx.send(f'Background Selected: {matched_bg}')
        except asyncio.TimeoutError:
            await self.ctx.send('No input received. Please try again.')
        return

    async def generate_char_proficiency(self, bot):

        picked_proficiencies = []  # To store the picked proficiencies

        while len(picked_proficiencies) < 2:
            data = self.categorize_proficiencies(proficiency_map, picked_proficiencies)
            data['picked_proficiencies'] = picked_proficiencies

            image_path = render_and_capture_html(data=data, cache=False,
                                                 image_path=f'prof_selection_{self.char_id}.png',
                                                 template_path='html_templates/char_prof.html', size=(600, 645))

            # Sending the image in Discord embed
            embed = discord.Embed(title="Proficiency Selection")
            file = discord.File(image_path, filename=f'prof_selection_{self.char_id}.png')
            embed.set_image(url=f'attachment://prof_selection_{self.char_id}.png')
            await self.ctx.send(file=file, embed=embed)

            # Delete the image
            os.remove(image_path)

            try:
                prof_msg = await bot.wait_for('message', check=self.check, timeout=30)
                user_prof = prof_msg.content.strip().lower()

                if user_prof == "random":
                    new_proficiencies = random.sample(proficiency_map, 2 - len(picked_proficiencies))
                    picked_proficiencies.extend(new_proficiencies)
                else:
                    matched_prof = next((prof for prof in proficiency_map.keys() if prof.lower() == user_prof), None)
                    if matched_prof:
                        picked_proficiencies.append(matched_prof)

            except asyncio.TimeoutError:
                await self.ctx.send('No input received. Please try again.')
                return
        char_data_str = get_char_ability_details(self.char_id)
        char_data = json.loads(char_data_str)
        proficiencies = json.loads(char_data['picked_proficiencies'])
        picked_proficiencies.extend(proficiencies)
        update_char_gen_progress(self.char_id, "picked_proficiencies", json.dumps(picked_proficiencies),
                                 self.creation_stage + 1)
        self.creation_stage += 1
        await self.ctx.send('Final Proficiencies: ', ', '.join(picked_proficiencies))

    @classmethod
    def categorize_proficiencies(cls, proficiency_map, picked_proficiencies, recommended_ability='INT'):
        recommended_proficiencies = []
        other_proficiencies = []
        picked = []

        for proficiency in proficiency_map.keys():
            formatted_proficiency = proficiency.title()  # Title casing the proficiency

            if proficiency.lower() in picked_proficiencies:
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

    def char_skill_data(self, char_id=None, user_id=None):
        if char_id is None:
            char_id, _ = self.fetch_latest_char_id(user_id=user_id)
            if not char_id:
                return "No character found", False
        char_data = json.loads(get_char_ability_details(char_id))

        ability_map = json.loads(char_data['ability_map'])
        ability_score_improve = json.loads(char_data['ability_score_improve']) if char_data['ability_score_improve'] and char_data['ability_score_improve']!="None" else {}
        ability_map_modifier = deepcopy(ability_map)
        for ability, modifier in ability_score_improve.items():
            ability_map_modifier[ability] += modifier

        for ability, score in ability_map_modifier.items():
            ability_map_modifier[ability] = math.floor(score / 2) - 5
        skill_modifier_map = deepcopy(skill_ability_map)
        for skill, ability in skill_modifier_map.items():
            skill_modifier_map[skill] = ability_map_modifier[ability]

        picked_proficiencies = json.loads(char_data['picked_proficiencies']) if char_data['picked_proficiencies'] else []
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
        return char_sheet, True

    def char_sheet_ability(self, char_id=None, user_id=None):
        if char_id is None:
            char_id, _ = self.fetch_latest_char_id(user_id=user_id)
            if not char_id:
                return discord.Embed(title=f'Create character using !create or view others char using !ci <char_id>'), False
        char_data = get_char_ability_details(char_id)
        if not char_data:
            return discord.Embed(title=f'Character id selected does not exist. Use !ci instead'), False
        char_data = json.loads(char_data)
        ability_map = json.loads(char_data['ability_map'])
        ability_score_improve = json.loads(char_data['ability_score_improve']) if char_data.get('ability_score_improve') else {}
        ability_map_modifier = deepcopy(ability_map)
        for ability, modifier in ability_score_improve.items():
            ability_map_modifier[ability] += modifier

        for ability, score in ability_map_modifier.items():
            ability_map_modifier[ability] = math.floor(score / 2) - 5
        skill_modifier_map = deepcopy(skill_ability_map)
        for skill, ability in skill_modifier_map.items():
            skill_modifier_map[skill] = ability_map_modifier[ability]

        picked_proficiencies = json.loads(char_data['picked_proficiencies']) if char_data['picked_proficiencies'] else []
        proficiency_list = ast.literal_eval(char_data['proficiency_list']) if char_data['proficiency_list'] else []
        print(picked_proficiencies, proficiency_list)

        for skill in (picked_proficiencies + proficiency_list):
            skill_modifier_map[skill] += 2
        saving_modifier_map = deepcopy(ability_map_modifier)
        for ability in ast.literal_eval(char_data['saving_throw_proficiency']):
            saving_modifier_map[ability] += 2
        char_sheet_data = {
            'AC': 10 + ability_map_modifier['DEX'],
            'name': char_data['char_name'],
            'ability_map_modifier': ability_map_modifier,
            'generation_type': 'Quick Build',
            'saving_modifier_map': saving_modifier_map,
            'bg_name': char_data['bg_name'],
            'class_name': char_data['class_name'],
            'pp': 10 + skill_modifier_map['Perception'],
            'max_hp': char_data['max_hp'],
            'race_name': char_data['race_name']
        }
        char_sheet = EmbedMsg().char_ability_info(**char_sheet_data)
        return char_sheet, True


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
            roll_value = dice_roll(1, 6, self.character_data['CON'], 0, 0)[0]
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
            self.add_item(CharacterRollButton(ability=ability, character_data=character_data, user=user, custom_id=ability, label=f"Roll for {ability}", disabled=True if ability == 'HP' else False))

    async def wait_until_all_disabled(self):
        while not all(item.disabled for item in self.children):
            await asyncio.sleep(1)



