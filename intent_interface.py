
import discord
from discord.ui import View

from player_char import PlayerChar


class PageIntent(View):
    def __init__(self, functions, char_id, user_id, ctx):
        super().__init__(timeout=60.0)
        self.functions = functions
        self.char_id = char_id
        self.user_id = user_id
        self.page = 0
        self.message = None
        if not self.char_id:
            self.char_id, _ = PlayerChar(ctx).fetch_latest_char_id(user_id=user_id)

    async def send_initial_message(self, ctx):
        self.message = await ctx.send(embed=self.current_page(), view=self)

    def current_page(self):
        current_page_embed, status = self.functions[self.page](self.char_id, self.user_id)
        if not status or not bool(self.char_id):
            self.children[0].disabled = True
            self.children[1].disabled = True
        return current_page_embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def on_previous_page(self, interaction, button):
        if interaction.user.id != self.user_id:
            return
        self.page = max(self.page - 1, 0)
        await interaction.response.edit_message(embed=self.current_page())

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def on_next_page(self, interaction, button):
        if interaction.user.id != self.user_id:
            return
        self.page = min(self.page + 1, len(self.functions) - 1)
        await interaction.response.edit_message(embed=self.current_page())

