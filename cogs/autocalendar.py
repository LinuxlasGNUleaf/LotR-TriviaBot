import random
import secrets
from datetime import datetime, timedelta
from io import BytesIO

import discord.errors
from discord.ext import tasks, commands

import discord_utils as du
import backend_utils as bu
from template_cog import LotrCog


class AutoCalendar(LotrCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.check.change_interval(minutes=self.options['check_interval'])
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

        mention = f'__{await self.retrieve_name(name=name, uid=uid, mention=True)}__'

        intro = random.choice(self.options["core_messages"]).format(user=mention)
        wishes = random.choice(self.options["birthday_wishes"])
        msg = f'{self.options["emoji"]} {intro} {self.options["emoji"]}\n{wishes}'
        channel = await self.bot.fetch_channel(self.options['announcement_channel'])
        await channel.send(msg)

    @du.category_check('privileged')
    @commands.group(invoke_without_command=True)
    async def birthday(self, ctx):
        await ctx.send("The following subcommands are available:\n`register`, `upcoming`, `delete`")

    @du.category_check('privileged')
    @birthday.command(aliases=['list', 'download', 'get'])
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
            description=f'This calendar contains the birthdays of {len(self.caches["birthdays"])} people!\nCreated on: **{datetime.now().strftime("%d/%m/%Y")}**',
            color=discord.Color.random())
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)
        with BytesIO() as buffer:
            buffer.write(cal_str.encode('utf-8'))
            buffer.seek(0)
            filename = f'{ctx.guild.name.title().replace(" ", "_")}.ics'
            await ctx.send(file=discord.File(fp=buffer, filename=filename))

    @du.category_check('privileged')
    @birthday.command(aliases=['next'])
    async def upcoming(self, ctx):
        now = datetime.now()
        dates = []
        for i, [month, day, name, uid] in enumerate(self.caches['birthdays']):
            birthday = datetime(year=now.year, month=month, day=day)
            if birthday < now:
                birthday = datetime(year=now.year+1, month=month, day=day)
            dates.append((birthday, name, uid))
        next_birthday = sorted(dates, key=lambda x: x[0])[0]
        name = await self.retrieve_name(next_birthday[1], next_birthday[2])
        await ctx.send(self.options['next_birthday_msg'].format(
            name=name,
            day=bu.ordinal(next_birthday[0].day),
            month=next_birthday[0].strftime("%B"),
            timestamp=int(next_birthday[0].timestamp())
        ))

    async def retrieve_name(self, name, uid, mention=False):
        if uid:
            try:
                user = await self.bot.fetch_user(uid)
                return user.mention if mention else user.name
            except (discord.errors.NotFound, discord.errors.HTTPException):
                self.logger.warning('Could not resolve UID, reverting to name.')
        return name


async def setup(bot):
    await bot.add_cog(AutoCalendar(bot))
