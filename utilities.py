import random

from env import LOG_CHANNEL


def generate_name_local():
    first_names = ['Aldor', 'Brienne', 'Cassius', 'Darian', 'Eleanora', 'Felix', 'Gwen', 'Hugo', 'Isadora', 'Jareth', 'Kael', 'Lysandra', 'Magnus', 'Niamh', 'Ophelia', 'Percival', 'Quentin', 'Rhiannon', 'Soren', 'Thalia', 'Ursula', 'Vesper', 'Wren', 'Xander', 'Yara', 'Zephyr', 'Ludmila', 'Sylvia', 'Alleria']
    last_names = ['Ambershield', 'Bridgerunner', 'Cloudwatcher', 'Doombringer', 'Eaglesight', 'Fireforge', 'Goldweaver', 'Hawkflight', 'Ironheart', 'Jadewalker', 'Kingslayer', 'Lionheart', 'Moonwhisper', 'Nightshade', 'Oakenshield', 'Proudwing', 'Greyrat', 'Ravenstorm', 'Silverhand', 'Thornbloom', 'Umbercoat', 'Violetclaw', 'Whitewind', 'Xenonblade', 'Yellowbrook', 'Proudmore']
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    return f'{first_name} {last_name}'


def dice_roll(dice_count, dice_sides, modifier, best_of, worst_of):
    dice_result = []
    for dice in range(1, dice_count+1):
        dice_result.append(random.randint(1, dice_sides) + modifier)
    if best_of:
        modified_result = sorted(dice_result)
        modified_result = modified_result[dice_count-best_of:]
    elif worst_of:
        modified_result = sorted(dice_result)
        modified_result = modified_result[:best_of]
    else:
        modified_result = dice_result
    return modified_result


async def discord_logger(ctx, e, tb, log_type):
    # Extract relevant information from the context and error
    server_id = ctx.guild.id if ctx.guild else None
    server_name = ctx.guild.name if ctx.guild else "Direct Message"  # If it's a direct message, use "Direct Message" as server name
    channel_id = ctx.channel.id
    channel_name = ctx.channel.name

    # Get the Discord ID of the user who triggered the error
    discord_id = ctx.author.id if ctx.author else None
    error_log = f"**Error occurred in bot: {discord_id}**\n" \
                f"**Log type:**{log_type}\n" \
                f"**Server ID:** {server_id}\n" \
                f"**Server Name:** {server_name}\n" \
                f"**Channel ID:** {channel_id}\n" \
                f"**Channel Name:** {channel_name}\n" \
                f"**Error Message:** {str(e)}\n" \
                f"**Traceback:**\n```{str(tb)[:600]}```"

    # Replace 'YOUR_LOG_CHANNEL_ID' with the actual channel ID where you want to log the errors
    log_channel_id = LOG_CHANNEL

    # Fetch the TextChannel using the channel ID
    log_channel = ctx.bot.get_channel(log_channel_id)

    if log_channel:
        await log_channel.send(error_log)


