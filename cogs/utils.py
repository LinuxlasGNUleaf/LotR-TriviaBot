from datetime import datetime
import logging
import os
import platform
import random
import typing
from discord.ext import commands
import discord

class Utils(commands.Cog):
    '''
    Utilities commands for the Bot.
    '''
    def __init__(self,bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.', self.__class__.__name__.title())

    @commands.is_owner()
    @commands.command()
    async def reload(self, ctx, cog: typing.Optional[str] = ''):
        '''
        reloads all or one specific cog
        '''
        if cog:
            if os.path.isfile(f'./cogs/{cog}.py'):
                cogs = [f'{cog}.py']
                title = f':clock10: Reloading `{cog}`'
            else:
                await ctx.send(':x: There is no cog with that name!')
                return
        else:
            cogs = os.listdir('./cogs/')
            title = ':clock10: Reloading all cogs...'

        embed = discord.Embed(title=title,description='Please wait, this can take a moment...')
        embed_msg = await ctx.send(embed=embed)

        for ext in cogs:
            try:
                if ext.endswith('.py') and not ext.startswith('_'):
                    self.bot.unload_extension(f'cogs.{ext[:-3]}')
                    self.bot.load_extension(f'cogs.{ext[:-3]}')
                    embed.add_field(name=':white_check_mark: Reloaded:',value=ext[:-3],inline=True)
            except commands.errors.ExtensionFailed as exc:
                embed.add_field(name=':x: Failed:',value=ext[:-3],inline=True)
                print(exc)
        await embed_msg.edit(embed=embed)

    @commands.Cog.listener('on_command_error')
    async def on_command_error(self, ctx, error):
        #Ignore these errors
        ignored = (commands.CommandNotFound, commands.UserInputError)
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.CommandOnCooldown):
            # If the command is currently on cooldown trip this
            minutes, secs = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            if not hours and not minutes:
                await ctx.send(f' You must wait {secs} seconds to use this command!')
            elif not hours and minutes:
                await ctx.send(f' You must wait {minutes} minutes and {secs} seconds to use this command!')
            else:
                await ctx.send(f' You must wait {hours} hours, {minutes} minutes and {secs} seconds to use this command!')
        elif isinstance(error, (commands.CheckFailure, commands.NotOwner)):
            # If the command has failed a check, trip this
            await ctx.send('*\'You cannot wield it. None of us can.\'* ~Aragorn\nYou lack permission to use this command!')
        else:
            raise error

    @commands.cooldown(1,60)
    @commands.command()
    async def stats(self, ctx):
        '''
        displays misc. statistics about the bot
        '''
        embed = discord.Embed(title=f'Stats for {self.bot.user.name}')
        embed.colour = random.choice(self.bot.color_list)

        dtime = datetime.now() - self.bot.start_time
        embed.add_field(name=':snake: Python Version:',value=platform.python_version())
        embed.add_field(name=':robot: Discord API Version:',value=discord.__version__)
        embed.add_field(name=':stopwatch: Latency:',value=f'{round(self.bot.latency*1000)}ms')
        embed.add_field(name=':alarm_clock: Uptime:',value=(f'{dtime.days}d,{dtime.seconds//3600}h,{dtime.seconds%3600//60}m,{dtime.seconds % 60}s'))
        embed.add_field(name=':shield: Guild Count:',value=len(self.bot.guilds))
        embed.add_field(name=':technologist: Member Count:',value=len(set(self.bot.get_all_members())))
        # embed.add_field(name=':jigsaw: Shard count:',value=self.bot.shard_count)
        embed.add_field(name=':gear: Active Cogs:',value=len(set(self.bot.cogs)))
        embed.add_field(name=':card_box: Github:',value=self.bot.config['general']['github_repo'])
        embed.add_field(name=':floppy_disk: Developer:',value='<@{}>'.format(self.bot.config['general']['developer_id']))
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Utils(bot))
