import asyncio
import os

import discord
from html2image import Html2Image
from jinja2 import Template

from env import DISCORD_CDN_CHANNEL
from model import query_database_for_image, insert_image_to_database


def render_and_capture_html(data, cache, image_path, template_path, size, db_image_link=None):
    if not cache and db_image_link:
        # If cache is False and a db_image_link is provided, return the link directly
        return db_image_link

    hti = Html2Image()

    # Load and render the HTML template
    with open(template_path, 'r') as file:
        template = Template(file.read())
        html_content = template.render(data=data)

    # Save the HTML to an image
    hti.screenshot(html_str=html_content, save_as=image_path, size=size)

    # Returning the path to the new image
    return image_path


async def render_and_capture_html_with_cache(bot, data, cache, image_path, template_path, size, cache_name):
    # Check the database for an existing image
    db_image = query_database_for_image(cache_name)
    if db_image:
        return db_image  # Return the existing image link from the database

    # If not cached, generate the image
    hti = Html2Image()
    with open(template_path, 'r') as file:
        template = Template(file.read())
    html_content = template.render(data=data)
    hti.screenshot(html_str=html_content, save_as=image_path, size=size)

    # Send the image to Discord and get the link
    image_link, message_id = await send_image_to_discord_channel(bot, image_path, DISCORD_CDN_CHANNEL)

    if cache:
        # Insert the new image link into the database
        insert_image_to_database(cache_name, image_link, message_id)
    if os.path.exists(image_path):
        os.remove(image_path)

    # Return the new image link
    return image_link


async def send_image_to_discord_channel(bot, image_path, channel_id):
    channel = bot.get_channel(int(channel_id))
    file = discord.File(image_path)
    message = await channel.send(file=file)
    return message.attachments[0].url, str(message.id)
