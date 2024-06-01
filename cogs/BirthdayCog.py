import random
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
import discord.errors
import pytz
from discord import app_commands
from discord import ui
from discord.ext import commands

from src.DefaultCog import DefaultCog
import src.utils as utils


class BirthdayCog(DefaultCog, group_name='birthday'):
    """
    birthday (de)registration, calendar download and automatic notifications
    """

    def register_with_db(self, uid, name, month, day, tz, last_congrats=None):
        if uid not in self.data['dates']:
            self.data['dates'].add_row(uid=uid)
        self.data['dates'].set(uid, 'name', name)
        self.data['dates'].set(uid, 'month', month)
        self.data['dates'].set(uid, 'day', day)
        self.data['dates'].set(uid, 'timezone', tz)
        if last_congrats:
            self.data['dates'].set(uid, 'last_congrats', last_congrats)

    async def check(self):
        for uid, name, month, day, tz, last_congrats in self.data['dates'].get_rows():

            tz = pytz.timezone(tz)
            now = datetime.now(tz=tz)

            birthday = utils.get_next_date(month, day, tz)

            # check if birthday deadline has passed and user hasn't been congratulated already this year
            if last_congrats == now.year or birthday > now:
                continue

            msg = '{emoji} {intro} {emoji}\n{wishes}'.format(
                emoji=self.config['check']['emoji'],
                intro=random.choice(self.config['check']['messages']).format(
                    user=f'__{(await self.retrieve_user_info(name=name, uid=uid, mention=True))[0]}__'),
                wishes=random.choice(self.config['check']['wishes']))

            channel = await self.bot.fetch_channel(self.config['check']['channel'])

            if not (channel and channel.permissions_for(channel.guild.me).send_messages):
                self.logger.warning(f'missing permissions, could not congratulate {name} ({uid}) on his birthday.')
                return
            await channel.send(msg)
            self.logger.info(f'congratulated {name} ({uid}) on his birthday.')

            # update user to reflect congratulation
            self.data['dates'].set(uid, 'last_congrats', now.year)

    @app_commands.command(name='get')
    @app_commands.describe(user='the user you want to get the birthday of')
    async def birthday(self, interaction: discord.Interaction, user: Optional[discord.Member]):
        pass

    @app_commands.command(name='register')
    async def register(self, interaction: discord.Interaction):
        await RegisterView(interaction, self).run()

    @app_commands.command(name='delete')
    async def delete(self, interaction: discord.Interaction):
        pass

    @app_commands.command(name='download')
    async def download(self, interaction: discord.Interaction):
        pass

    def create_birthday_embed(self, name: str, month: int, day: int, tz: pytz.timezone, avatar=None):
        timestamp = utils.get_next_date(month, day, tz)
        embed = discord.Embed(title=f':birthday:  {utils.genitive(name)} birthday')
        embed.colour = discord.Colour.random()
        if avatar:
            embed.set_thumbnail(url=avatar.url)
        embed.description = self.config['birthday_embed'].format(
            day=utils.ordinal(timestamp.day),
            month=timestamp.strftime("%B"),
            timestamp=discord.utils.format_dt(timestamp, 'R')
        )
        self.logger.info(timestamp)
        self.logger.info(pytz.timezone().utcoffset())
        return embed


class RegisterView(ui.View):
    def __init__(self, interaction: discord.Interaction, cog: BirthdayCog):
        super().__init__(timeout=cog.config['registration']['timeout'] * 60)
        self.msg = None
        self.cog: BirthdayCog = cog
        self.interaction: discord.Interaction = interaction
        self.button = RegistrationButton(cog)
        self.add_item(self.button)

    async def run(self):
        self.msg = await self.interaction.response.send_message(
            self.cog.config['registration']['hint'],
            view=self)

    async def on_timeout(self):
        for element in self.children:
            element.disabled = True
        await self.msg.edit(view=self)


class RegistrationButton(discord.ui.Button):
    def __init__(self, cog: BirthdayCog):
        self.cog: BirthdayCog = cog
        self.modals = []
        super().__init__(label='Birthday Registration',
                         emoji=cog.config['registration']['unicode_emoji'])

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RegistrationModal(self.cog, interaction.user))


class RegistrationModal(ui.Modal, title='Birthday Registration Form'):
    def __init__(self, cog: BirthdayCog, user: discord.User):
        super().__init__()
        self.cog: BirthdayCog = cog
        self.user = user
        if self.user.id in self.cog.data['dates']:
            self.old_entry = self.cog.data['dates'].get_row(user.id)
            name, month, day, tz, _ = self.old_entry
        else:
            self.old_entry = None
            name, month, day, tz = (user.name, 1, 1, 'UTC')

        self.components = [
            ui.TextInput(label='Name', min_length=1, max_length=32, default=name),
            ui.TextInput(label='Month:', min_length=1, max_length=2, default=month),
            ui.TextInput(label='Day of the Month:', min_length=1, max_length=2, default=day),
            ui.TextInput(label='Timezone:', min_length=1, max_length=100, default=tz)
        ]
        for component in self.components:
            self.add_item(component)

    async def on_submit(self, interaction: discord.Interaction):
        name: str
        month: str
        day: str
        tz: str
        name, month, day, tz = (x.value for x in self.components)

        valid, msg = utils.validate_date_str(month, day)
        if not valid:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        month: int = int(month)
        day: int = int(day)

        try:
            pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            await interaction.response.send_message(
                'Timezone not valid. Choose a `TZ Identifier` from here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List',
                ephemeral=True,
                delete_after=10)
            return

        self.cog.register_with_db(self.user.id, name, month, day, tz)

        embed = self.cog.create_birthday_embed(
            name=name,
            month=month,
            day=day,
            tz=pytz.timezone(tz),
            avatar=self.user.avatar
        )

        await interaction.response.send_message(
            f'__**{self.user.name}**__ {"updated" if self.old_entry else "registered"} their birthday:',
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(BirthdayCog(bot))
