"""
Hangman cog for the LotR-Trivia Bot
"""
import asyncio
import random
import string

import discord
from discord.ext import commands

import backend_utils as bu
import discord_utils as du
from template_cog import LotrCog


class Hangman(LotrCog):
    """
    Cog for the ME-related hangman game
    """

    def __init__(self, bot):
        super().__init__(bot)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.',
                         self.__class__.__name__.title())

    @du.category_check('minigames')
    @commands.command(name='hangman')
    async def create_hangman_game(self, ctx):
        """
        hangman game with ME-related characters and places
        """

        with open(self.assets['words'], 'r') as csvfile:
            word = random.choice(csvfile.readlines()).strip()
        word_condensed = word.lower().replace(' ', '')

        steps = 2 if len(word_condensed) <= 6 else 1

        game_states = self.options['ongoing_states']
        end_states = self.options['end_states']

        used_chars = []  # used characters array
        max_ind = len(game_states) - 1  # max index
        ind = 0

        h_embed = create_hangman_embed(
            ctx.message.author, word, game_states[0], 0, [], True)
        hangman = await ctx.send(embed=h_embed)

        def check(chk_msg):
            return chk_msg.author == ctx.message.author and chk_msg.channel == ctx.channel

        self.bot.blocked_users.append(ctx.message.author.id)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check,
                                              timeout=self.options['timeout'])
                msg = msg.content.lower()

            except asyncio.TimeoutError:
                h_embed = create_hangman_embed(
                    ctx.message.author, word, end_states[0], 8, used_chars, False)
                await hangman.edit(embed=h_embed)
                await ctx.send('Game over! You took too long to answer!')
                break

            for char in msg:
                if char not in used_chars and char in string.ascii_lowercase:
                    used_chars.append(char)
                    if char not in word_condensed:
                        ind += steps
            used_chars.sort()

            if ind > max_ind:
                h_embed = create_hangman_embed(
                    ctx.message.author, word, end_states[0], 8, used_chars, False)
                await hangman.edit(embed=h_embed)
                await ctx.send('Game over! You lost all your lives!')
                break

            for char in word_condensed:
                if char not in used_chars and char.isalpha():
                    break
            else:
                h_embed = create_hangman_embed(
                    ctx.message.author, word, end_states[1], 0, used_chars, False)
                await hangman.edit(embed=h_embed)
                await ctx.send('Congratulations! You won the game!')
                break

            h_embed = create_hangman_embed(
                ctx.author, word, game_states[ind], ind, used_chars, True)
            await hangman.edit(embed=h_embed)

        self.bot.blocked_users.remove(ctx.author.id)


def create_hangman_embed(user: discord.Member, word, state, ind, used_chars, ongoing):
    """
    creates Hangman embed
    """
    hangman = ''
    for char in word:
        if char == ' ':
            hangman += '  '
            continue
        if not char.isalpha():
            hangman += char + ' '
        elif char.lower() in used_chars or not ongoing:
            hangman += '__{}__ '.format(char)
        else:
            hangman += r'\_ '
    hangman = hangman.strip()

    if used_chars:
        used = 'Used letters:\n '
        for char in used_chars:
            used += ':regional_indicator_{}: '.format(char)
        used = used.strip()
    else:
        used = ''

    author_field = (f'{user.display_name}\'s hangman game', (user.avatar if user.avatar else user.default_avatar).url)

    color = discord.Color.from_rgb(bu.map_values(ind, 0, 8, 0, 255),
                                   bu.map_values(ind, 0, 8, 255, 0), 0)

    return du.create_embed(hangman, content=used + state, color=color, author_field=author_field)


async def setup(bot):
    await bot.add_cog(Hangman(bot))
