import asyncio
import discord

import minigames

class LotrBot(discord.Client):
    """
    Bot client, inheriting from discord.Client
    """
    def __init__(self, config, scoreboard):
        self.config = config
        self.scoreboard = scoreboard
        self.blocked = []
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

        if content == self.config.KEY+" trivia":
            # send the question message
            embed, correct_ind, len_answers = minigames.create_trivia_question(user, self.scoreboard, self.config)
            await channel.send(embed=embed)

            def check(chk_msg):
                return chk_msg.author == user and chk_msg.channel == channel

            self.blocked.append(user.id)
            try:
                msg = await self.wait_for('message', check=check, timeout=15)
            except asyncio.TimeoutError:
                msg = ""
            self.blocked.remove(user.id)

            reply = minigames.create_trivia_reply(user, msg, self.scoreboard, correct_ind, len_answers, self.config)
            await channel.send(reply)


        elif content == self.config.KEY+" profile":
            if user.id in self.scoreboard.keys():
                await channel.send(embed=minigames.create_trivia_profile(user, self.scoreboard, self.config))
            else:
                await channel.send("You have to play a game of trivia before a \
profile can be generated! use `{} trivia` to take a quiz!".format(self.config.KEY))


        elif content == self.config.KEY+" hangman":
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
