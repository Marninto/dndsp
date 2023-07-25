import asyncio
import traceback

import discord
from discord.ui import View

from constants import tag_marn
from discord.ext import commands
import random

from env import BOT_TOKEN
from intent_interface import PageIntent
from langchains import gpt_ask
from middleware import enrolled_required, normal_build_char_id
from model import enroll
from player_char import PlayerChar
from utilities import dice_roll, discord_logger

intents = discord.Intents.all()
client = discord.Client(intents=intents)


bot = commands.Bot(command_prefix='!', intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')


@bot.command(name='enroll')
async def user_enroll(ctx):
    user_id = ctx.author.id
    success, status = enroll(user_id)
    if not success:
        await ctx.send(f'Enrolling failed. please connect to {tag_marn}')
    elif success and status == 'exists':
        await ctx.send('Already enrolled')
    else:
        await ctx.send('Enrolled successfully - you can start creating character with create command')


@bot.command(name='create')
@enrolled_required
@normal_build_char_id
async def create_char(ctx, build_type='normal', char_id=0, creation_stage=0):
    try:
        if build_type == 'quick':
            confirmation_message = await ctx.send('Are you sure you want to proceed with quick build? You cannot reroll '
                                                  'the ability scores if you proceed with it. Type "confirm" within '
                                                  '30 seconds to proceed.')
            try:
                # Wait for the user to confirm within 30 seconds
                await bot.wait_for(
                    'message', timeout=30.0, check=lambda m: m.author == ctx.author and m.content.lower() == 'confirm')

                # If the user confirms, execute the process
                await ctx.send('Executing process...')
                success = PlayerChar(ctx).quick_build_char()
                await ctx.send('Character created, access it by !charinfo or !ci' if success else 'Character creation failed')

            except asyncio.TimeoutError:
                # If the user doesn't confirm within 30 seconds, terminate the process
                await confirmation_message.edit(content='Confirmation not received within 30 seconds. Process terminated.')
        elif build_type == 'normal':
            await PlayerChar(ctx).roll_build_char(bot, char_id, creation_stage)
        else:
            await ctx.send('Please use !create for normal build and !create quick for quick build')
    except Exception as e:
        tb = traceback.format_exc()
        await discord_logger(ctx, e, tb, 'ERROR')


@bot.command(name='charinfo', aliases=['ci'])
@enrolled_required
async def user_charinfo(ctx, char_id=None):
    try:
        discord_id = ctx.author.id
        player_char = PlayerChar(ctx)
        functions = [
            player_char.char_sheet_ability,
            player_char.char_skill_data,
        ]
        view = PageIntent(functions, char_id, discord_id, ctx)
        await view.send_initial_message(ctx)
    except Exception as e:
        tb = traceback.format_exc()
        await discord_logger(ctx, e, tb, 'ERROR')


@bot.command(name='test')
async def test(ctx):
    embed = discord.Embed(title='Test')
    embed.add_field(name='AC', value=f'', inline=False)


bot.run(BOT_TOKEN)
