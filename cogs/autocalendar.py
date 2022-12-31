import random
import secrets
import typing
from datetime import datetime, timedelta
from io import BytesIO

import discord.errors
from discord.ext import tasks, commands

import discord_utils as du
import backend_utils as bu
from template_cog import LotrCog


def get_next_date(month, day):
    now = datetime.now()
    birthday = datetime(year=now.year, month=month, day=day)
    if birthday < now:
        birthday = datetime(year=now.year + 1, month=month, day=day)
    return birthday


class AutoCalendar(LotrCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.check.change_interval(minutes=self.options['check_interval'])
        self.check.start()
        for i, [month, day, name, uid] in enumerate(self.caches['birthdays']):
            self.caches['birthdays'][i] = [month, day, name, int(uid) if uid else uid]

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

    def create_birthday_embed(self, name: str, month: int, day: int, thumbnail_url: str = None):
        timestamp = get_next_date(month, day)
        embed = discord.Embed(title=f':birthday:  {bu.genitive(name)} birthday')
        embed.colour = discord.Colour.random()
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        embed.description = self.options['birthday_embed'].format(
            day=bu.ordinal(timestamp.day),
            month=timestamp.strftime("%B"),
            timestamp=discord.utils.format_dt(timestamp, 'R')
        )
        return embed

    async def retrieve_user_info(self, name, uid, mention=False):
        """
        retrieves username / mention and their avatar url
        """
        if uid:
            try:
                user = await self.bot.fetch_user(uid)
                return user.mention if mention else user.name, user.avatar.url
            except (discord.errors.NotFound, discord.errors.HTTPException):
                self.logger.warning('Could not resolve UID, reverting to name.')
        return name, None

    @tasks.loop()
    async def check(self):
        result = self.check_for_birthday()
        if not result:
            return
        name, uid = result

        mention = f'__{(await self.retrieve_user_info(name=name, uid=uid, mention=True))[0]}__'

        intro = random.choice(self.options["core_messages"]).format(user=mention)
        wishes = random.choice(self.options["birthday_wishes"])
        msg = f'{self.options["emoji"]} {intro} {self.options["emoji"]}\n{wishes}'
        channel = await self.bot.fetch_channel(self.options['announcement_channel'])
        await channel.send(msg)

    @du.category_check('privileged')
    @commands.group(invoke_without_command=True)
    async def birthday(self, ctx, member: typing.Optional[discord.Member]):
        if member:
            entry = list(filter(lambda x: x[3] == member.id, self.caches['birthdays']))
            if not entry:
                await ctx.send(
                    f'{self.bot.options["discord"]["indicators"][0]} This member has not registered their birthday yet.')
                return
            month, day, name, uid = entry[0]
            embed = self.create_birthday_embed(
                name=member.name,
                month=month,
                day=day,
                thumbnail_url=member.avatar.url
            )
            await ctx.send(embed=embed)
            return
        cmds = f'`{"`, `".join(self.options["subcommands"])}`'
        await ctx.send(f"If you want to fetch the birthday of someone, use `birthday @user` with a user __from this server__.\nThe following subcommands are available:\n{cmds}")

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
        # calculate the next birthday dates for each registered user
        dates = [(get_next_date(month, day), name, uid) for month, day, name, uid in self.caches['birthdays']]

        # sort the datetime objects and grab the "nearest"
        date, name, uid = sorted(dates, key=lambda x: x[0])[0]

        # retrieve info about the user
        username, avatar_url = await self.retrieve_user_info(name, uid)

        # create embed
        embed = self.create_birthday_embed(
            name=username,
            month=date.month,
            day=date.day,
            thumbnail_url=avatar_url
        )
        await ctx.send("The next birthday is:",
                       embed=embed)


async def setup(bot):
    await bot.add_cog(AutoCalendar(bot))
