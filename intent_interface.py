import os

import discord
from discord.ui import View


class PageIntent(View):
    def __init__(self, bot, functions, char_id, user_id):
        super().__init__(timeout=60.0)
        self.functions = functions
        self.char_id = char_id
        self.user_id = user_id
        self.bot = bot
        self.page = 0
        self.message = None

    async def send_initial_message(self, ctx):
        current_page = await self.current_page()
        self.message = await ctx.send(embed=current_page, view=self)

    async def current_page(self):
        current_page_embed = await self.functions[self.page]()
        if not bool(self.char_id):
            self.children[0].disabled = True
            self.children[1].disabled = True
        return current_page_embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def on_previous_page(self, interaction, button):
        if interaction.user.id != self.user_id:
            return
        self.page = max(self.page - 1, 0)
        current_page = await self.current_page()
        await interaction.response.edit_message(embed=current_page)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def on_next_page(self, interaction, button):
        if interaction.user.id != self.user_id:
            return
        self.page = min(self.page + 1, len(self.functions) - 1)
        current_page = await self.current_page()
        await interaction.response.edit_message(embed=current_page)

