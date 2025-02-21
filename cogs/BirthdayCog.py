import random
from datetime import datetime, timezone, timedelta
from typing import Optional
from io import BytesIO

import discord
import discord.errors
import pytz
import secrets
from discord import app_commands

from src.DefaultCog import DefaultCog
from src.CustomUIs import BirthdayRegistrationView
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
        if user is None:
            user = interaction.user

        if user.id not in self.data['dates']:
            await interaction.response.send_message(
                f'{"You have" if user.id == interaction.user.id else "This user has"} not registered their birthday yet.',
                ephemeral=True)
            return
        name, month, day, tz = self.data['dates'].get(user.id, ['name','month', 'day', 'timezone'])
        tz = pytz.timezone(tz)
        await interaction.response.send_message(
            f"{utils.genitive(name)} birthday:",
            embed=self.create_birthday_embed(name, month, day, tz, avatar=user.avatar)
        )

    @app_commands.command(name='register')
    async def register(self, interaction: discord.Interaction):
        await BirthdayRegistrationView(interaction, self).run()

    @app_commands.command(name='delete')
    async def delete(self, interaction: discord.Interaction):
        if interaction.user.id in self.data['dates']:
            self.data['dates'].delete_row(interaction.user.id)
            await interaction.response.send_message('Your birthday has been deleted from the register.', ephemeral=True)
            return
        await interaction.response.send_message('Your birthday was not yet registered, so it was not deleted either.',
                                                ephemeral=True)

    @app_commands.command(name='download')
    async def download(self, interaction: discord.Interaction):
        now = datetime.now()
        event_str = ""
        entries = 0
        for uid, name, month, day, tz, last_congrats in self.data['dates'].get_rows():
            entries += 1
            start = datetime(year=2020, month=month, day=day)
            end = start + timedelta(days=1)
            event_str += self.config['ics']['event'].format(
                uid=secrets.token_hex(8),
                name=f'{name.strip()} - Birthday',
                start=f'{now.year}{start.month:02}{start.day:02}',
                end=f'{now.year}{end.month:02}{end.day:02}' if end.year == start.year else f'{now.year+1}0101'
            )

        cal_str = self.config['ics']['wrapper'].format(event_str)
        embed = discord.Embed(
            title=f'Birthday Calendar for {interaction.guild.name.title()}',
            description=f'This calendar contains the birthdays of {entries} people!\nCreated on: **{datetime.now().strftime("%d/%m/%Y")}**',
            color=discord.Color.random())
        embed.set_thumbnail(url=interaction.guild.icon.url)
        with BytesIO() as buffer:
            buffer.write(cal_str.encode('utf-8'))
            buffer.seek(0)
            filename = f'{interaction.guild.name.title().replace(" ", "_")}.ics'
            await interaction.response.send_message(embed=embed, file=discord.File(fp=buffer, filename=filename))

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
        return embed


async def setup(bot):
    await bot.add_cog(BirthdayCog(bot))
