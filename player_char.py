import ast
import asyncio
import json
import math
import random
from copy import deepcopy

import discord

from embed_wrapper import EmbedMsg
from constants import dnd_ability_map, skill_ability_map, dnd_class_proficiency_map
from model import check_onboard_status, check_player_chars, generate_quickbuild_character, get_score_modifier, \
    get_class_id_from_name, get_char_ability_details, fetch_race_ability_and_id_map, generate_custom_char, update_char_gen_progress
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
        await self.ctx.send("Pick your race:")
        race_ability_map, race_id_map = fetch_race_ability_and_id_map()
        race_modifier_str = "\n".join(
            f"{', '.join(f'{k}:+{v}' for k, v in json.loads(value).items())}" for key, value in race_ability_map.items())

        race_embed = discord.Embed(title="Races", color=0x00FF00)
        race_embed.add_field(name="Available Races", value='\n'.join(race_ability_map.keys()), inline=True)
        race_embed.add_field(name="Score Modifiers", value=race_modifier_str, inline=True)
        race_embed.add_field(name="Selected Race", value="None", inline=True)

        race_message = await self.ctx.send(embed=race_embed)

        while True:
            try:
                race_msg = await bot.wait_for('message', check=self.check, timeout=60)
                user_race = race_msg.content.strip().lower()
                matched_race = next((race for race in race_ability_map.keys() if race.lower() == user_race), None)

                if matched_race:
                    self.character_data['race'] = matched_race
                    race_embed.set_field_at(2, name="Selected Race", value=matched_race, inline=True)
                    await race_message.edit(embed=race_embed)
                    break
                else:
                    await self.ctx.send('Invalid input, please type a valid race.')
            except asyncio.TimeoutError:
                await self.ctx.send('No input received. Please try again')

        update_char_gen_progress(self.char_id, "race_id", race_id_map[self.character_data['race']], self.creation_stage + 1)
        await self.ctx.send(f'Race Selected: {self.character_data["race"]}')
        await self.ctx.send('Bg and proficiency left')

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
        print(char_data)

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

        picked_proficiencies = char_data['picked_proficiencies'].split(', ') if char_data['picked_proficiencies'] else []
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

        picked_proficiencies = char_data['picked_proficiencies'].split(', ') if char_data['picked_proficiencies'] else []
        proficiency_list = ast.literal_eval(char_data['proficiency_list']) if char_data['proficiency_list'] else []

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



