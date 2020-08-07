'''
Main discord bot class, includes minigames.py for all the extra functionality
'''
import asyncio
import discord
import minigames

class LotrBot(discord.Client):
    '''
    Bot client, inheriting from discord.Client
    '''
    def __init__(self, config, scoreboard, reddit_client, yt_api_client, google_search_client):
        self.config = config
        self.scoreboard = scoreboard
        self.blocked = []
        self.do_autoscript = True
        self.script = []
        self.script_condensed = []
        self.reddit_client = reddit_client
        self.yt_api_client = yt_api_client
        self.google_search_client = google_search_client
        minigames.parse_script(config.DISCORD_CONFIG['script.path'],
                               self.script, self.script_condensed)
        super().__init__()


    async def on_ready(self):
        '''
        init function for discord bot
        '''
        print('[INFO]: Setting rich presence...')
        await self.change_presence(activity=discord.Activity\
            (type=discord.ActivityType.watching, name='Boromir getting boromir\'d'))
        print('[SYSTEM]: online. All systems operational.')
        print('||>----------- O N L I N E ------------>||')


    async def on_message(self, message):
        '''
        main function to recognize a bot command
        '''
        if message.author == self.user or message.author.id in self.blocked:
            return

        user = message.author
        raw_content = message.content.strip()
        content = raw_content.lower()
        channel = message.channel
        isDM = isinstance(channel, discord.channel.DMChannel)
        if not isDM:
            server = channel.guild

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key'] + ' trivia':
            # send the question message
            embed, correct_ind, len_answers = minigames.\
                create_trivia_question(user, self.scoreboard, self.config)
            await channel.send(embed=embed,
                               delete_after=self.config.DISCORD_CONFIG['trivia.timeout'])

            def check(chk_msg):
                return chk_msg.author == user and chk_msg.channel == channel

            self.blocked.append(user.id)
            try:
                msg = await self.wait_for('message',
                                          check=check,
                                          timeout=self.config.DISCORD_CONFIG['trivia.timeout'])
            except asyncio.TimeoutError:
                msg = ''
            self.blocked.remove(user.id)

            reply = minigames.create_trivia_reply(user, msg, self.scoreboard,
                                                  correct_ind, len_answers,
                                                  self.config)
            await channel.send(reply)

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key']+' hangman':
            embed, game_info = minigames.initiate_hangman_game(user, self.config)
            hangman_msg = await channel.send(embed=embed)

            def check(chk_msg):
                return chk_msg.author == user and chk_msg.channel == channel

            self.blocked.append(user.id)

            failed = False
            while not failed:
                try:
                    msg = await self.wait_for('message',
                                              check=check,
                                              timeout=self.config.DISCORD_CONFIG['hangman.timeout'])
                except asyncio.TimeoutError:
                    msg = ''

                embed, failed, message, game_info = minigames.\
                    update_hangman_game(user, msg, game_info, self.config)
                await hangman_msg.edit(embed=embed)
                if message:
                    await channel.send(message)

            self.blocked.remove(user.id)

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key'] + ' meme':
            ch_id = channel.id if isDM else server.id 
            embed = minigames.reddit_meme(ch_id, self.reddit_client)
            await channel.send(embed=embed)

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key'] + ' squote':
            embed = minigames.silmarillion_quote(self.config)
            await channel.send(embed=embed)

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key'] + ' profile':
            if user.id in self.scoreboard.keys():
                await channel.send(embed=minigames.create_trivia_profile(user, self.scoreboard))
            else:
                await channel.send('You have to play a game of trivia before a \
profile can be generated! use `{} trivia` to take a quiz!'\
                                   .format(self.config.GENERAL_CONFIG['key']))

#==============================================================================
        elif content.startswith(self.config.GENERAL_CONFIG['key'] + ' yt '):
            raw_content = raw_content.split(' ')[2:]

            if raw_content[0].isdigit():  # Video count was provided
                num = int(raw_content[0])
                query = ' '.join(raw_content[1:])
            else:
                query = ' '.join(raw_content)
                num = 1

            if not query:
                await channel.send(minigames.create_reply(user, True, self.config) +
                                   '\nTry providing a query next time!\nThe correct syntax is: \
`{0} yt (<max video count>) <keywords>\n(count is optional)`'\
                                   .format(self.config.GENERAL_CONFIG['key']))
                return

            result = minigames.search_youtube(
                self.yt_api_client,
                self.config.YT_CONFIG['channel_id'],
                query,
                num,
                self.config)

            if not result:
                await channel.send('*\'I have no memory of this place\'*\n\
~Gandalf\nYour query `{}` yielded no results!'.format(query))
                return

            for embed in result:
                await channel.send(embed=embed)

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key'] + ' help':
            embed = minigames.create_embed(
                title='LotR Trivia Bot help',
                content=self.config.DISCORD_CONFIG['help.text'],
                footnote=self.config.DISCORD_CONFIG['help.footer'])
            await channel.send(embed=embed)

#==============================================================================
        elif content == self.config.GENERAL_CONFIG['key'] + ' scoreboard':
            if isDM:
                channel.send("Well that's not going to work, mate.\nYou are in a DM... join a server where this amazing bot is present to create a scoreboard.")
                return
            embed = minigames.create_scoreboard(self.scoreboard, server)
            await channel.send(embed=embed)

#==============================================================================
        elif content.startswith(self.config.GENERAL_CONFIG['key'] + ' search '):
            raw_content = ' '.join(raw_content.split(' ')[2:]).strip()
            result = minigames.lotr_search(self.google_search_client, raw_content, self.config)
            if isinstance(result, str):
                await channel.send(result)
            else:
                await channel.send(embed=result[0])
                await channel.send(result[1])

#==============================================================================
        elif self.do_autoscript and not isDM:
            result = minigames.find_similar_from_script\
            (message.content, self.script_condensed, self.script)
            if isinstance(result, list):
                await message.add_reaction('✅')
                for line in result:
                    await channel.send(line)
