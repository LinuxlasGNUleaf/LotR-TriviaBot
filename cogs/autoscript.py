from difflib import SequenceMatcher
from random import choice
import logging
from discord.ext import commands
import discord

class Autoscript(commands.Cog):
    '''
    handles the Autoscript integration of the Bot
    '''
    def __init__(self,bot):
        self.bot = bot
        self.script = []
        self.condensed_script = []
        self.parse_script(self.script, self.condensed_script)
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('%s cog has been loaded.', self.__class__.__name__.title())

    @commands.Cog.listener('on_message')
    async def autoscript(self, message):
        '''
        attempts to find similar line from script and formats it, if found.
        '''
        if message.author.bot:
            return
        # format message string
        content = message.content.lower().strip()
        channel = message.channel

        if isinstance(channel, discord.channel.DMChannel):
            return
        if not channel.permissions_for(channel.guild.me).send_messages:
            return

        # stop if the message is shorter than 2 words
        if len(content.split(' ')) < 2:
            return

        for char in self.bot.config['discord']['autoscript']['punctuation_chars']:
            content = content.replace(char, '.')
        for char in self.bot.config['discord']['autoscript']['elimination_chars']:
            content = content.replace(char, '')
        content = content.split('.')

        # searching condensed script for matching line
        log = {}

        # search the script for each sentence in the message individually
        for msg_part in content:
            msg_part = msg_part.strip()

            if not msg_part:
                continue

            # iterate through lines
            for line_ind, line in enumerate(self.condensed_script):

                # abort conditions
                if not line:
                    continue
                if isinstance(line, str):
                    if line == 'STOP' or line == 'HARDSTOP':
                        continue

                # iterate through sentences in the line
                for part_ind, part in enumerate(line):
                    # get the matching ratio
                    ratio = SequenceMatcher(None, part, msg_part).ratio()
                    if ratio > self.bot.config['discord']['autoscript']['threshold']:
                        # if line has already been found
                        if line_ind in log.keys():
                            num, found_conf, highest_part_ind = log[line_ind]
                            log[line_ind] = (num+1, # found-parts
                                            round((found_conf*num+ratio)/num+1, 2), # conf
                                            max(highest_part_ind, part_ind)) # part-ind

                        # if line was not yet found, only add it if the sentence is longer than
                        # one word. This prevents the bot from reacting to very short sentences.
                        elif len(msg_part.split(' ')) > 1:
                            log[line_ind] = (1, round(ratio, 2), part_ind)

        # log entries have the following scheme: [line index]: number-of-found-parts, confidence, part index
        if log:
            # I swear I'm not insane, but this next part might look like I am :)

            # sort results by found parts
            ranking = sorted(log, key=lambda x: log[x][0])[::-1]
            # filter the results that have the same amount of found parts as the top one
            filtered_dict = dict(filter(lambda item: item[1][0] == log[ranking[0]][0], log.items()))
            # sort these by the confidence
            filtered_ranking = sorted(filtered_dict, key=lambda x: filtered_dict[x][1])[::-1]
            # aaand select all those entries that have the same conf level as the highest ranked one.
            super_filtered_ranking = dict(filter(lambda item: filtered_dict[item[0]][1] == filtered_dict[filtered_ranking[0]][1], filtered_dict.items()))

            # pick a random one
            line_ind = choice(list(super_filtered_ranking.keys()))
            part_ind = log[line_ind][2]

            parts = []
            punctuation_found = False

            # get the corresponding line from the complete script
            author, line = self.script[line_ind].split('|')
            temp = ''

            # try to split the sentence by punctuations (to find the correct point to continue)
            for char in line:
                if char in self.bot.config['discord']['autoscript']['punctuation_chars']:
                    punctuation_found = True
                elif punctuation_found:
                    punctuation_found = False
                    parts.append(temp.strip())
                    temp = ''
                temp += char
            if temp.strip():
                parts[-1] += temp

            # if there is something after this line, print it
            if part_ind < len(parts)-1 or line_ind < len(self.script)-1:
                return_text = ''
                # if there is a part of the line that is missing, complete it
                if part_ind < len(parts)-1:
                    temp = ''
                    for part in parts[part_ind+1:]:
                        temp += part+' '
                    return_text += '**{}:** ... {}\n'.format(author.title(), temp)

                # if the line is not the last one of the script, add the next one
                skipped_lines = 0
                i = 0
                while i < self.bot.config['discord']['autoscript']['dialog_count']+skipped_lines:
                    i += 1
                    if line_ind+i <= len(self.script)-1:
                        if self.script[line_ind+i] != 'HARDSTOP':
                            # if a scene STOP is before the next line,
                            # continue only if configured to do so.
                            if self.script[line_ind+i] == 'STOP':
                                if self.bot.config['discord']['autoscript']['scene_end_interrupt'] and line_ind+i >= len(self.script)-1:
                                    break
                                i += 1
                                skipped_lines += 1
                                return_text += '**`[NEXT SCENE]`**\n'
                                author, text = self.script[line_ind+i].split('|')
                                return_text += '**{}:** {}\n'.format(author.title(), text)
                            else:
                                author, text = self.script[line_ind+i].split('|')
                                return_text += '**{}:** {}\n'.format(author.title(), text)
                        else:
                            break

                if channel.permissions_for(channel.guild.me).add_reactions:
                    await message.add_reaction('✅')

                # to prevent discord from complaining about too long messages.
                while len(return_text) >= 2000:
                    return_text = '\n'.join(return_text.split('\n')[:-1])

                await channel.send(return_text.strip())

    def parse_script(self, script, condensed_script):
        '''
        reads the LOTR script to array.
        Also outputs a condensed version for faster searching.
        '''
        with open(self.bot.config['discord']['autoscript']['file'], 'r') as script_file:
            temp = ''
            last = ''
            for line in script_file:
                line = line.strip()

                if not line and temp:
                    script.append(temp)
                    temp = ''
                else:
                    temp += line
                    if last:
                        temp += ' '
                    if not last and 'STOP' not in line:
                        temp += '|'

                last = line

        for line in script:
            if 'STOP' in line:
                condensed_script.append(line.strip())
                continue

            line = line.lower().split('|', 1)[1]
            punctuation_found = False
            temp_arr = []

            for char in line:
                if char in self.bot.config['discord']['autoscript']['elimination_chars']:
                    continue
                if char in self.bot.config['discord']['autoscript']['punctuation_chars']:
                    punctuation_found = True
                elif punctuation_found:
                    punctuation_found = False
                    temp_arr.append(temp.strip())
                    temp = ''
                temp += char
            condensed_script.append(temp_arr)

def setup(bot):
    bot.add_cog(Autoscript(bot))
