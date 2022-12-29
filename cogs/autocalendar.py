import random
from datetime import datetime, timedelta
from io import BytesIO

import discord.errors
from discord.ext import tasks, commands
import secrets

from template_cog import LotrCog


class AutoCalendar(LotrCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.check.change_interval(seconds=self.options['check_interval'])
        self.check.start()

    def check_for_birthday(self):
        now = datetime.now()
        for day, month, name, uid in self.caches['birthdays']:
            # check if date fits
            if month != now.month or day != now.day:
                continue

            # determine key and check if user has been congratulated this year already
            key = uid if uid else name
            entry = self.caches['congrats'].setdefault(key, [])
            if now.year in entry:
                continue

            # add user to congrats_log
            entry.append(now.year)
            self.caches['congrats'][key] = entry

            # return the found pair
            return name, uid

    @tasks.loop()
    async def check(self):
        result = self.check_for_birthday()
        if not result:
            return
        name, uid = result

        user = ''
        if uid:
            try:
                user = f'__{(await self.bot.fetch_user(uid)).mention}__'
            except (discord.errors.NotFound, discord.errors.HTTPException):
                self.logger.warning('Could not resolve UID, reverting to name.')
                pass
        if not user:
            user = f'__{name}__'

        intro = random.choice(self.options["core_messages"]).format(user=user)
        wishes = random.choice(self.options["birthday_wishes"])
        msg = f'{self.options["emoji"]} {intro} {self.options["emoji"]}\n{wishes}'
        channel = await self.bot.fetch_channel(self.options['announcement_channel'])
        await channel.send(msg)

    @commands.command()
    async def calendar(self, ctx):
        now = datetime.now()
        event_str = ""
        for month, day, name, _ in self.caches['birthdays']:
            start = datetime(year=now.year, month=month, day=day)
            end = start + timedelta(days=1)
            event_str += self.options['ics_event'].format(
                uid=secrets.token_hex(8),
                name=f'{name.strip()} - Birthday',
                start=start.strftime('%Y%m%d'),
                end=end.strftime('%Y%m%d')
            )

        cal_str = self.options['ics_wrapper'].format(event_str)
        embed = discord.Embed(
            title=f'Birthday Calendar for {ctx.guild.name.title()}',
            color=discord.Color.random())
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)
        with BytesIO() as buffer:
            buffer.write(cal_str.encode('utf-8'))
            buffer.seek(0)
            filename = f'{ctx.guild.name.title().replace(" ", "_")}.ics'
            await ctx.send(file=discord.File(fp=buffer, filename=filename))


async def setup(bot):
    await bot.add_cog(AutoCalendar(bot))
