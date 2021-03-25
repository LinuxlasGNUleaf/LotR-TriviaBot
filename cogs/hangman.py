'''
Hangman cog for the LotR-Trivia Bot
'''
import random
import string
import asyncio
from discord.ext import commands
import cogs._dcutils


class Hangman(commands.Cog):
    '''
    Cog for the ME-related hangman game
    '''
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.__class__.__name__} Cog has been loaded.')

    @commands.command(name='hangman')
    async def create_hangman_game(self, ctx):
        '''
        Hangman game with Middle Earth related characters and places
        '''

        with open('words.csv', 'r') as csvfile:
            word = random.choice(csvfile.readlines()).strip()
        word_condensed = word.lower().replace(' ', '')

        steps = 2 if len(word_condensed) <= 6 else 1

        game_states = self.bot.config['discord']['hangman']['ongoing_states']
        end_states = self.bot.config['discord']['hangman']['end_states']

        used_chars = []  # used characters array
        max_ind = len(game_states)-1 # max index
        ind = 0

        h_embed = create_hangman_embed(ctx.message.author, word, game_states[0], 0, [], True)
        hangman = await ctx.send(embed=h_embed)

        def check(chk_msg):
            return chk_msg.author == ctx.message.author and chk_msg.channel == ctx.channel

        self.bot.blocked.append(ctx.message.author.id)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=self.bot.config['discord']['hangman']['timeout'])
                msg = msg.content.lower()

            except asyncio.TimeoutError:
                h_embed = create_hangman_embed(ctx.message.author, word, end_states[0], 8, used_chars, False)
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
                h_embed = create_hangman_embed(ctx.message.author, word, end_states[0], 8, used_chars, False)
                await hangman.edit(embed=h_embed)
                await ctx.send('Game over! You lost all your lives!')
                break

            for char in word_condensed:
                if char not in used_chars and char.isalpha():
                    break
            else:
                h_embed = create_hangman_embed(ctx.message.author, word, end_states[1], 0, used_chars, False)
                await hangman.edit(embed=h_embed)
                await ctx.send('Congratulations! You won the game!')
                break

            h_embed = create_hangman_embed(ctx.author, word, game_states[ind], ind, used_chars, True)
            await hangman.edit(embed=h_embed)

        self.bot.blocked.remove(ctx.author.id)

def create_hangman_embed(user, word, state, ind, used_chars, ongoing):
    '''
    creates Hangman embed
    '''
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

    author_info = ('{}\'s hangman game'.format(user.display_name), user.avatar_url)

    color = (cogs._dcutils.map_vals(ind, 0, 8, 0, 255),
            cogs._dcutils.map_vals(ind, 0, 8, 255, 0), 0)

    return cogs._dcutils.create_embed(hangman, author_info=author_info, content=used + state, color=color)


def setup(bot):
    bot.add_cog(Hangman(bot))
