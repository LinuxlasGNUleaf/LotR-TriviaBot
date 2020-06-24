import asyncio

import discord

import minigames

class LotrBot(discord.Client):
    """
    Bot client, inheriting from discord.Client
    """
    def __init__(self, config, scoreboard, reddit_client):
        self.config = config
        self.scoreboard = scoreboard
        self.blocked = []
        self.do_autoscript = True
        self.meme_progress = {} #keeps track of sent memes in each server
        self.script = []
        self.script_condensed = []
        self.reddit_client = reddit_client
        minigames.parse_script(config.SCRIPT_LOC, self.script, self.script_condensed)
        super().__init__()


    async def on_ready(self):
        """
        init function for discord bot
        """
        print("PreInit...")
        await self.change_presence(activity=discord.Activity\
            (type=discord.ActivityType.watching, name="Boromir die"))
        print("online. All systems operational.")


    async def on_message(self, message):
        """
        main function to recognize a bot command
        """

        if message.author == self.user or message.author.id in self.blocked:
            return

        user = message.author
        content = message.content.lower()
        channel = message.channel

        
        if content.startswith(self.config.KEY + " config "):
            self.config(message, user, channel)

        elif content == self.config.KEY + " trivia":
            self.trivia(message, user, channel)
        
        elif content == self.config.KEY+" hangman":
            self.hangman(message, user, channel)

        elif content == self.config.KEY + " meme":
            embed = minigames.reddit_meme(message, self.reddit_client, self.meme_progress)
            await channel.send(embed=embed)
        
        elif content == self.config.KEY + " squote":
            embed = minigames.silmarillion_quote(self.config)
            await channel.send(embed=embed)

        elif content == self.config.KEY + " profile":
            self.profile(message, user, channel)

        elif self.do_autoscript:
            self.autoscript(message, user, channel)


    def hangman(self, message, user, channel):
        """
        handles initiation of the hangman game
        """
        embed, game_info = minigames.initiate_hangman_game(user, self.config)
        hangman_msg = await channel.send(embed=embed)

        def check(chk_msg):
            return chk_msg.author == user and chk_msg.channel == channel

        self.blocked.append(user.id)

        failed = False
        while not failed:
            try:
                msg = await self.wait_for('message', check=check, timeout=15)
            except asyncio.TimeoutError:
                msg = ""

            embed, failed, message, game_info = minigames.update_hangman_game(user, msg, game_info, self.config)
            await hangman_msg.edit(embed=embed)
            if message:
                await channel.send(message)

        self.blocked.remove(user.id)


    def autoscript(self, message, _, channel):
        """
        handles initiation of the autoscript feature
        """
        result = minigames.find_similar_from_script\
            (message.content, self.script_condensed, self.script)
        if result:
            await message.add_reaction("✅")
            for line in result:
                await channel.send(line)


    def trivia(self, _, user, channel):
        """
        handles the initiation of the trivia game
        """
        # send the question message
        embed, correct_ind, len_answers = minigames.\
            create_trivia_question(user, self.scoreboard, self.config)
        await channel.send(embed=embed)

        def check(chk_msg):
            return chk_msg.author == user and chk_msg.channel == channel

        self.blocked.append(user.id)
        try:
            msg = await self.wait_for('message', check=check, timeout=15)
        except asyncio.TimeoutError:
            msg = ""
        self.blocked.remove(user.id)

        reply = minigames.create_trivia_reply(user, msg, self.scoreboard, 
                                              correct_ind, len_answers, 
                                              self.config)
        await channel.send(reply)


    def profile(self, message, user, channel):
        if user.id in self.scoreboard.keys():
                await channel.send(embed=minigames.create_trivia_profile(user, self.scoreboard, self.config))
            else:
                await channel.send("You have to play a game of trivia before a \
profile can be generated! use `{} trivia` to take a quiz!".format(self.config.KEY))


    def config(self, message, user, channel):
        content = content.split(" ")[2:]
        if content[0] == "autoscript":
            if content[1] == "true":
                self.do_autoscript = True
                await channel.send("option `autoscript` was enabled!")
            elif content[1] == "false":
                self.do_autoscript = False
                await channel.send("option `autoscript` was disabled!")
            else:
                await channel.send("state for option `autoscript` was not recognized!")
        else:
            await channel.send("option `{}` was not recognized!".format(content[0]))