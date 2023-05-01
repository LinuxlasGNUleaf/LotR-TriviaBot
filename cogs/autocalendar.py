import random
import secrets
import typing
from datetime import datetime, timedelta
from io import BytesIO

import discord.errors
from discord import ui
from discord.ext import tasks, commands

import backend_utils as bu
import discord_utils as du
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
        self.check.change_interval(minutes=self.options['check']['interval'])
        self.check.start()

        self.views = []

        if not self.caches['birthdays']:
            self.caches['birthdays'] = []
        for i, [month, day, name, uid] in enumerate(self.caches['birthdays']):
            self.caches['birthdays'][i] = [month, day, name, int(uid) if uid else uid]

    def register_birthday(self, month: int, day: int, name: str, uid: int = None):
        entry = self.get_birthday_by_uid(uid)
        new_entry = [month, day, name, uid]

        # is user already registered?
        if entry:
            index = self.caches['birthdays'].index(entry)
            self.caches['birthdays'][index] = new_entry
        else:
            self.caches['birthdays'].append(new_entry)

        self.logger.info(f'{"Updated" if entry else "Registered"} {bu.genitive(name)} birthday to be: {day}.{month}.')

    def get_birthday_by_uid(self, uid):
        if uid not in [x[3] for x in self.caches['birthdays']]:
            return None
        return list(filter(lambda x: x[3] == uid, self.caches['birthdays']))[0]

    def check_for_birthday(self):
        now = datetime.now()
        for month, day, name, uid in self.caches['birthdays']:
            # check if date fits
            if month != now.month or day != now.day:
                continue

            # determine key and check if user has been congratulated this year already
            key = uid if uid else name
            entry = self.caches['congrats'].setdefault(key, [])
            if now.year in entry:
                continue

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
                self.logger.warning('could not resolve UID, reverting to name.')
        return name, None

    @tasks.loop()
    async def check(self):
        result = self.check_for_birthday()
        if not result:
            return
        name, uid = result

        mention = f'__{(await self.retrieve_user_info(name=name, uid=uid, mention=True))[0]}__'

        msg = '{emoji} {intro} {emoji}\n{wishes}'.format(
            emoji=self.options['check']['emoji'],
            intro=random.choice(self.options['check']['messages']).format(user=mention),
            wishes=random.choice(self.options['check']['wishes']))

        channel = await self.bot.fetch_channel(self.options['check']['channel'])

        if not (channel and channel.permissions_for(channel.guild.me).send_messages):
            self.logger.warning(f'missing permissions, could not congratulate {name} ({uid}) on his birthday.')
            return
        await channel.send(msg)
        self.logger.info(f'congratulated {name} ({uid}) on his birthday.')

        # add user to congrats_log
        self.caches['congrats'][uid if uid else name].append(datetime.now().year)

    @check.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @du.category_check('privileged')
    @commands.group(invoke_without_command=True)
    async def birthday(self, ctx, member: typing.Optional[discord.Member]):
        if member:
            entry = self.get_birthday_by_uid(member.id)
            if not entry:
                await ctx.send(
                    f'{self.bot.options["discord"]["indicators"][0]} This member has not registered their birthday yet.')
                return
            month, day, name, uid = entry
            embed = self.create_birthday_embed(
                name=member.name,
                month=month,
                day=day,
                thumbnail_url=member.avatar.url
            )
            await ctx.send(embed=embed)
            return
        cmds = f'`{"`, `".join(self.options["subcommands"])}`'
        await ctx.send(
            f"If you want to fetch the birthday of someone, use `birthday @user` with a user __from this server__.\nThe following subcommands are available:\n{cmds}")

    @du.category_check('privileged')
    @birthday.command(aliases=['list', 'download', 'get'])
    async def calendar(self, ctx):
        now = datetime.now()
        event_str = ""
        for month, day, name, _ in self.caches['birthdays']:
            start = datetime(year=now.year, month=month, day=day)
            end = start + timedelta(days=1)
            event_str += self.options['ics']['event'].format(
                uid=secrets.token_hex(8),
                name=f'{name.strip()} - Birthday',
                start=start.strftime('%Y%m%d'),
                end=end.strftime('%Y%m%d')
            )

        cal_str = self.options['ics']['wrapper'].format(event_str)
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

        if not dates:
            await ctx.send(
                f'{self.bot.options["discord"]["indicators"][0]} You have to register some birthdays before using this command!')
            return

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

    @du.category_check('privileged')
    @birthday.command(aliases=['update'])
    @commands.cooldown(1, 180)
    async def register(self, ctx):
        await RegisterView(ctx, self).run()


class RegisterView(ui.View):
    def __init__(self, context: commands.Context, cog: AutoCalendar):
        super().__init__(timeout=cog.options['registration']['timeout'] * 60)
        self.msg = None
        self.cog: AutoCalendar = cog
        self.ctx: commands.Context = context
        self.button = RegistrationButton(cog)
        self.add_item(self.button)

    async def run(self):
        self.msg = await self.ctx.send(
            self.cog.options['registration']['hint'],
            view=self)

    async def on_timeout(self):
        print(2)
        for element in self.children:
            element.disabled = True
        await self.msg.edit(view=self)


class RegistrationButton(discord.ui.Button):
    def __init__(self, cog: AutoCalendar):
        self.cog: AutoCalendar = cog
        self.modals = []
        super().__init__(label='Birthday Registration',
                         emoji=cog.options['registration']['unicode_emoji'])

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RegistrationModal(self.cog, interaction.user))


class RegistrationModal(ui.Modal, title='Birthday Registration Form'):
    def __init__(self, cog: AutoCalendar, user: discord.User):
        super().__init__()
        self.cog: AutoCalendar = cog
        self.user = user
        self.old_entry = self.cog.get_birthday_by_uid(user.id)
        if self.old_entry:
            month, day, name, _ = self.old_entry
        else:
            month, day, name = (1, 1, user.name)
        self.components = [
            ui.TextInput(label='Name', min_length=1, max_length=32, default=name),
            ui.TextInput(label='Month:', min_length=1, max_length=2, default=month),
            ui.TextInput(label='Day of the Month:', min_length=1, max_length=2, default=day)
        ]
        for component in self.components:
            self.add_item(component)

    async def on_submit(self, interaction: discord.Interaction):
        name: str
        month: str
        day: str
        name, month, day = (x.value for x in self.components)

        if not month.isdigit() or int(month) not in range(12):
            await interaction.response.send_message('Month not valid.', ephemeral=True)
            return

        if not month.isdigit()
            await interaction.response.send_message('Month not valid.', ephemeral=True)
            return

        month: int = int(month)

        if not month in range(13):
            await interaction.response.send_message('Month not valid.', ephemeral=True)
            return

        if not day.isdigit() or int(day) - 1 not in range(self.cog.options['days_in_a_month'][month]):
            await interaction.response.send_message('Day not valid.',
                                                    ephemeral=True,
                                                    delete_after=10)
            return
        day: int = int(day)

        if self.old_entry and [month, day, name, self.old_entry[-1]] == self.old_entry:
            await interaction.response.send_message('No info was changed.',
                                                    ephemeral=True,
                                                    delete_after=10)
            return

        self.cog.register_birthday(name=name, month=month, day=day, uid=self.user.id)

        embed = self.cog.create_birthday_embed(
            name=name,
            month=month,
            day=day,
            thumbnail_url=self.user.avatar.url
        )

        await interaction.response.send_message(
            f'__**{self.user.name}**__ {"updated" if self.old_entry else "registered"} their birthday:',
            embed=embed
            )

async def setup(bot):
    await bot.add_cog(AutoCalendar(bot))
