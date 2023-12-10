import discord
from discord.ui import Select, View


class SelectView(discord.ui.View):
    def __init__(self, ctx, bg_ability_list, user_id, key, title, timeout=30):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.selected_option = ""
        print(bg_ability_list)

        # Add the select dropdown
        dropdown_options = [
            discord.SelectOption(label=bg, value=bg) for bg in bg_ability_list
        ]

        select_menu = discord.ui.Select(
            placeholder=title,
            options=dropdown_options,
            custom_id=f"{key}_{user_id}"
        )
        select_menu.callback = self.select_callback
        self.add_item(select_menu)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You cannot select an option for this user.", ephemeral=True)
            return
        # Retrieve the selected option
        self.selected_option = interaction.data['values'][0]

        # Let the user know their choice was registered
        await interaction.response.send_message(f"You selected {self.selected_option}.", ephemeral=True)

        # Stop the view to allow the code to proceed
        self.stop()
