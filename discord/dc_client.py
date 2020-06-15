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
        self.autoscript = True
        self.script = []
        self.script_condensed = []
        minigames.parseScript('lotr_fellowship.txt', self.script, self.script_condensed)
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

        if content.startswith(self.config.KEY+" config "):
            content = content.split(" ")[2:]
            if content[0] == "autoscript":
                if content[1] == "true":
                    self.autoscript = True
                    await channel.send("option `autoscript` was enabled!")
                elif content[1] == "false":
                    self.autoscript = False
                    await channel.send("option `autoscript` was disabled!")
                else:
                    await channel.send("status for option `autoscript` was not recognized!")
            else:
                await channel.send("option `{}` was not recognized!".format(content[0]))


        elif content == self.config.KEY+" trivia":
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

        else:
            result = minigames.findSimilarfromScript(message.content, self.script_condensed)
            punctuations = [".", "?", "!"]
            if result != -1:
                # message.add_reaction(discord.Emoji(self.guild,":white_check_mark:"))
                ind, line_ind = result
                author, line = self.script[ind].split("|")
                parts = []
                punctuation_found = False
                temp = ""
                for char in line:
                    if char in punctuations:
                        punctuation_found = True
                    elif punctuation_found:
                        punctuation_found = False
                        parts.append(temp.strip())
                        temp = ""
                    temp += char

                if (line_ind < len(parts)-1):
                    temp = ""
                    for part in parts[line_ind+1:]:
                        temp += part+" "
                    await channel.send("**{}**: ... {}".format(author.title(), temp))

                if (ind < len(self.script)-1):
                    if self.script[ind+1] != "STOP":
                        author, text = self.script[ind+1].split("|")
                        await channel.send("**{}**: {}".format(author.title(), text))