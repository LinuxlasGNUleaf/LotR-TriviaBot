import asyncio
import platform
import random
import typing
from datetime import datetime

import discord
from discord.ext import commands, tasks

import discord_utils as du
from template_cog import LotrCog


class Utils(LotrCog):
    """
    Utility commands for the Bot.
    """

    def __init__(self, bot):
        super().__init__(bot)

    async def cog_load(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())
        self.autopresence.change_interval(minutes=self.options['autopresence'])
        self.autopresence.start()

    @commands.is_owner()
    @commands.command()
    async def reload(self, ctx, cog: typing.Optional[str] = ''):
        """
        reloads all or one specific cog
        """

        if cog:
            # if cog is active, select that cog
            if cog.lower() in [x.lower() for x in self.bot.cogs.keys()]:
                cog_list = [self.bot.cog_prefix + cog.lower()]
                title = f':clock10: Reloading `{cog}`'
            else:
                await ctx.send(':x: There is no cog with that name!')
                return
        else:
            # select all cogs currently loaded
            cog_list = []
            title = ':clock10: Reloading all cogs...'

        embed = discord.Embed(title=title,
                              description='Please wait, this will take a moment...')
        embed_msg = await ctx.send(embed=embed)

        result = await self.bot.reload_cogs(cog_list)
        for cog, status in result.items():
            if status == 'OK':
                name = ':white_check_mark: Reloaded:'
            elif status == 'FAIL':
                name = ':x: Failed:'
            elif status == 'N/A':
                name = ':grey_question: Not found / available'
            elif status == 'NEW':
                name = ':new: New and loaded'
            else:
                continue
            embed.add_field(name=name,
                            value=cog,
                            inline=True)
        await embed_msg.edit(embed=embed)

    def get_random_presence(self):
        return discord.Activity(type=discord.ActivityType.watching,
                                name=random.choice(self.options['status']))

    @tasks.loop()
    async def autopresence(self):
        new_activity = self.get_random_presence()
        self.logger.info(f'Changing presence to: "Watching {new_activity.name}"')
        await self.bot.change_presence(activity=new_activity)

    @autopresence.before_loop
    async def before_autopresence(self):
        if not self.bot.is_ready():
            self.logger.info('Waiting for the bot to finish startup before changing presence...')
            await self.bot.wait_until_ready()
            self.logger.info(f'Startup complete, presence will now be updated.')

    @commands.cooldown(1, 60)
    @commands.command()
    async def stats(self, ctx):
        """
        displays misc. statistics about the bot
        """
        embed = discord.Embed(title=f'Stats for {self.bot.user.name}')
        embed.colour = random.choice(self.bot.color_list)

        uptime = datetime.now() - self.bot.start_time
        embed.add_field(name=':snake: Python Version:',
                        value=platform.python_version())
        embed.add_field(name=':robot: Discord API Version:',
                        value=discord.__version__)
        embed.add_field(name=':stopwatch: Latency:',
                        value=f'{round(self.bot.latency * 1000)}ms')
        embed.add_field(name=':alarm_clock: Uptime:', value=(
            f'{uptime.days}d,{uptime.seconds // 3600}h,{uptime.seconds % 3600 // 60}m,{uptime.seconds % 60}s'))
        embed.add_field(name=':shield: Guild Count:',
                        value=len(self.bot.guilds))
        embed.add_field(name=':technologist: Member Count:',
                        value=len(set(self.bot.get_all_members())))
        # embed.add_field(name=':jigsaw: Shard count:'
        #                 value=self.bot.shard_count)
        embed.add_field(name=':gear: Active Cogs:',
                        value=len(set(self.bot.cogs)))
        embed.add_field(name=':card_box: Github:',
                        value=self.bot.config['general']['github_repo'])
        embed.add_field(name=':floppy_disk: Developer:',
                        value=f'<@{self.bot.config["general"]["developer_id"]}>')
        await ctx.send(embed=embed)

    @commands.has_permissions(manage_roles=True)
    @commands.group(name='settings', aliases=['setting', 'config'], invoke_without_command=True)
    async def settings(self, ctx):
        """
        configures which categories are activated.
        """
        # user wants to see the config embed:
        embed = discord.Embed(
            title=f'Config for #{ctx.channel} in {ctx.guild}')

        for category in self.bot.config['discord']['settings']['categories']:

            server_setting = ':grey_question:'
            if ctx.guild.id in self.bot.settings.keys():
                if category in self.bot.settings[ctx.guild.id]:
                    server_setting = self.bot.config['discord']['indicators'][self.bot.settings[ctx.guild.id][category]]

            channel_setting = ':grey_question:'
            if ctx.channel.id in self.bot.settings.keys():
                if category in self.bot.settings[ctx.channel.id]:
                    channel_setting = self.bot.config['discord']['indicators'][
                        self.bot.settings[ctx.channel.id][category]]

            effective = self.bot.config['discord']['indicators'][du.is_category_allowed(
                ctx, category, self.bot.settings, self.bot.config['discord']['settings']['defaults'])]
            embed.add_field(name=f'**Category `{category}`:**',
                            value=f'Server: {server_setting} Channel: {channel_setting} Effective: {effective}',
                            inline=False)
        embed.set_footer(
            text=f'Tip: If you want to change the settings, you need to provide arguments. Type "{self.bot.config["discord"]["prefix"][0]} settings help" for more info.')
        await ctx.send(embed=embed)

    @commands.has_permissions(manage_roles=True)
    @settings.command(name='channel', aliases=['c', 'ch', 'local'])
    async def channel_settings(self, ctx, *args):
        """
        selects settings for the channel
        """
        await self.edit_settings(ctx, args, True)

    @commands.has_permissions(manage_roles=True)
    @settings.command(name='server', aliases=['s', 'srv', 'global'])
    async def server_settings(self, ctx, *args):
        """
        selects settings for the server
        """
        await self.edit_settings(ctx, args, False)

    @commands.has_permissions(manage_roles=True)
    @settings.command(name='info', aliases=['?'], invoke_without_command=True)
    async def help_settings(self, ctx):
        """
        displays info about the settings
        """
        text = self.bot.config['discord']['settings']['help'].format(self.bot.config['discord']['prefix'][0],
                                                                     '`' + '`, `'.join(
                                                                         self.bot.config['discord']['settings'][
                                                                             'categories']) + '`')
        await ctx.send(text, file=discord.File('assets/infographic1.png'))

    async def edit_settings(self, ctx, args, channel_mode):
        """
        edits the settings according to user input
        """
        error_str = ''
        if len(args) != 2:
            error_str = f'{self.bot.config["discord"]["indicators"][0]} You have to provide __two__ arguments!'
        elif args[0].lower() not in self.bot.config['discord']['settings']['categories']:
            error_str = f'{self.bot.config["discord"]["indicators"][0]} Invalid category!'
        elif args[1].lower() not in ['on', 'off', 'reset']:
            error_str = f'{self.bot.config["discord"]["indicators"][0]} Invalid mode!'

        if error_str:
            error_str += 'You have to provide a category and a mode to edit. The categories are:\n'
            error_str += '`' + \
                         '`, `'.join(self.bot.config['discord']['settings']['categories']) + '`\n'
            error_str += 'The modes are:\n `on`, `off`, `reset`'
            await ctx.send(error_str)
            return

        spec_id = ctx.channel.id if channel_mode else ctx.guild.id
        spec_word = 'channel' if channel_mode else 'server'
        category, mode = args

        if spec_id not in self.bot.settings.keys():
            self.bot.settings[spec_id] = {}

        if mode == 'on':
            self.bot.settings[spec_id][category] = 1
            await ctx.send(f'category `{category}` was turned **on** for this {spec_word}.')

        elif mode == 'off':
            self.bot.settings[spec_id][category] = 0
            await ctx.send(f'category `{category}` was turned **off** for this {spec_word}.')

        elif mode == 'reset':
            if category in self.bot.settings[spec_id].keys():
                del self.bot.settings[spec_id][category]
                await ctx.send(f'category `{category}` was **unset** for this {spec_word}.')
            else:
                await ctx.send(f'category `{category}`was not yet set for this {spec_word} .')

    @commands.Cog.listener('on_command_error')
    async def on_command_error(self, ctx, error):
        """
        An error handler that is called when an error is raised inside a command either through user input error, check failure, or an error in the code.
        """
        # Ignore these errors
        ignored = (commands.CommandNotFound, commands.UserInputError, commands.NoPrivateMessage)
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.CommandOnCooldown):
            # If the command is currently on cooldown trip this
            minutes, secs = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            if not hours and not minutes:
                await ctx.send(f' You must wait {round(secs)} seconds to use this command!')
            elif not hours and minutes:
                await ctx.send(
                    f' You must wait {round(minutes)} minutes and {round(secs)} seconds to use this command!')
            else:
                await ctx.send(
                    f' You must wait {round(hours)} hours, {round(minutes)} minutes and {round(secs)} seconds to use this command!')

        elif isinstance(error, du.CategoryNotAllowed):
            # if the category is not allowed in this context
            await ctx.send(
                f'{self.bot.config["discord"]["indicators"][0]} The category `{error.category}` is disabled in this context.',
                delete_after=15)

        elif isinstance(error, (commands.MissingPermissions, commands.NotOwner)):
            await ctx.send(
                '*\'You cannot wield it. None of us can.\'* ~Aragorn\nYou lack permission to use this command!')

        elif isinstance(error, du.ChannelBusy):
            if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                await error.orig_message.delete()
            await ctx.send(
                f'{self.bot.config["discord"]["indicators"][0]} This channel is currently busy. Try again when no event is currently taking place.',
                delete_after=10)

        elif isinstance(error, commands.CheckFailure):
            await ctx.send(
                f'{self.bot.config["discord"]["indicators"][0]} An internal error occurred while parsing this command. Please contact the developer.')
            self.logger.warning('Unknown CheckFailure occurred, type is: %s', type(error))

        else:
            raise error


async def setup(bot):
    await bot.add_cog(Utils(bot))
