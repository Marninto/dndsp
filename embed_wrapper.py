import discord


class EmbedMsg:
    def __init__(self):
        self.verify_action = True  # verify_action() to determine action is allowed or not

    def char_ability_info(self, **kwargs):
        embed = discord.Embed(title=kwargs['name'])
        embed.set_author(name=f'{kwargs.get("race_name")} {kwargs.get("class_name")}')
        embed.set_thumbnail(
            url='https://media.discordapp.net/attachments/1072097225058037782/1102567866869489674/fizban.jpg?width=330&height=520')
        embed.add_field(name='AC', value=f'{kwargs["AC"]}', inline=True)
        embed.add_field(name='Max HP', value=f'{kwargs["max_hp"]}', inline=True)
        embed.add_field(name='Passive Perception', value=f'{kwargs["pp"]}', inline=True)
        embed.add_field(name='Speed', value=f'30', inline=True)
        embed.add_field(name='Initiative', value=f'{"+" if kwargs["ability_map_modifier"]["DEX"]>0 else ""}{kwargs["ability_map_modifier"]["DEX"]}', inline=True)
        embed.add_field(name='Proficieny Bonus', value=f'+2', inline=True)
        embed.add_field(name='ABILITIES', value='', inline=False)
        for key, value in kwargs['ability_map_modifier'].items():
            embed.add_field(name=f'{key}: {"+" if value>0 else ""}{value}', value='', inline=True)
        embed.add_field(name='SAVING THROWS', value='', inline=False)
        for key, value in kwargs['saving_modifier_map'].items():
            embed.add_field(name=f'{key}: {"+" if value>0 else ""} {value}', value='', inline=True)
        embed.add_field(name=f'{kwargs["generation_type"]}', value='')
        embed.add_field(name=f'Background: {kwargs["bg_name"]}', value='')
        return embed

    def char_skill_info(self, **kwargs):
        embed = discord.Embed(title=kwargs['name'])
        embed.set_author(name=f'{kwargs.get("race_name")} {kwargs.get("class_name")}')
        embed.set_thumbnail(
            url='https://media.discordapp.net/attachments/1072097225058037782/1102567866869489674/fizban.jpg?width=330&height=520')
        count = 0
        for key, value in kwargs['skill_modifier_map'].items():
            embed.add_field(name=f'{key}: {"+" if value>0 else ""}{value}', value='', inline=True)
            count += 1
        return embed

    def msg_embed(self, **kwargs):
        """
        title='test_title', subtitle='test_sub', attachment_url='https://i.imgur.com/uITXIaz.jpg',
                     description='well lets see', footer="", thumbnail_url="", fields=""):
        :param kwargs:
        :return:
        """
        embed = discord.Embed(title=kwargs['title'], description=kwargs['description'])
        if kwargs.get('subtitle'):
            embed.set_author(name=kwargs.get('subtitle'))
        if kwargs.get('image_url'):
            embed.set_image(url=kwargs.get('image_url'))
        if kwargs.get('footer'):
            embed.set_footer(text=kwargs.get('footer'))
        if kwargs.get('thumbnail_url'):
            embed.set_thumbnail(url=kwargs.get('thumbnail_url'))
        if kwargs.get('fields'):
            fields = kwargs.get('fields').split(";")
            for field in fields:
                name, value, inline = field.split(",")
                if kwargs.get('inline'):
                    embed.add_field(name=name, value=value, inline=(inline.lower() == "true"))
                else:
                    embed.add_field(name=name, value=value)
        return embed
