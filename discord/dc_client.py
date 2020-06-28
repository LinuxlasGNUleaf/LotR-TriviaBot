"""
Main discord bot class, includes minigames.py for all the extra functionality
"""
import asyncio
import discord
import minigames

class LotrBot(discord.Client):
    """
    Bot client, inheriting from discord.Client
    """
    def __init__(self, config, scoreboard, reddit_client, google_client):
        self.config = config
        self.scoreboard = scoreboard
        self.blocked = []
        self.do_autoscript = True
        self.script = []
        self.script_condensed = []
        self.reddit_client = reddit_client
        self.google_client = google_client
        minigames.parse_script(config.SCRIPT_LOC, self.script, self.script_condensed)
        super().__init__()


    async def on_ready(self):
        """
        init function for discord bot
        """
        print("[INFO]: Setting rich presence...")
        await self.change_presence(activity=discord.Activity\
            (type=discord.ActivityType.watching, name="Boromir die"))
        print("[SYSTEM]: online. All systems operational.")
        print("||>----------- O N L I N E ------------>||")


    async def on_message(self, message):
        """
        main function to recognize a bot command
        """

        if message.author == self.user or message.author.id in self.blocked:
            return

        user = message.author
        raw_content = message.content.strip()
        content = raw_content.lower()
        channel = message.channel

#==============================================================================
        if content.startswith(self.config.KEY + " config "):
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

#==============================================================================
        elif content == self.config.KEY + " trivia":
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

#==============================================================================
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

                embed, failed, message, game_info = minigames.\
                    update_hangman_game(user, msg, game_info, self.config)
                await hangman_msg.edit(embed=embed)
                if message:
                    await channel.send(message)

            self.blocked.remove(user.id)

#==============================================================================
        elif content == self.config.KEY + " meme":
            embed = minigames.reddit_meme(message, self.reddit_client)
            await channel.send(embed=embed)

#==============================================================================
        elif content == self.config.KEY + " squote":
            embed = minigames.silmarillion_quote(self.config)
            await channel.send(embed=embed)

#==============================================================================
        elif content == self.config.KEY + " profile":
            if user.id in self.scoreboard.keys():
                await channel.send(embed=minigames.\
                create_trivia_profile(user, self.scoreboard, self.config))
            else:
                await channel.send("You have to play a game of trivia before a \
    profile can be generated! use `{} trivia` to take a quiz!".format(self.config.KEY))

#==============================================================================
        elif content.startswith(self.config.KEY + " yt "):
            raw_content = raw_content.split(" ")[2:]
            if raw_content[0].isdigit():  # Video count was provided
                num = int(raw_content[0])
                query = " ".join(raw_content[1:])
            else:
                query = " ".join(raw_content)
                num = 1

            if not query:
                await channel.send(minigames.create_reply(user, True, self.config) +
                                   "\nTry providing a query next time!\nThe correct syntax is: \
`{0} yt (<max video count>) <keywords>\n(count is optional)`".format(self.config.KEY))
                return

            result = minigames.search_youtube(
                self.google_client,
                self.config.TEH_LURD_CHANNEL_ID,
                query,
                num,
                self.config)
            if not result:
                await channel.send("*\"I have no memory of this place\"*\n\
~Gandalf\nYour query `{}` yielded no results!".format(query))
                return
            for embed in result:
                await channel.send(embed=embed)

#==============================================================================
        elif content == self.config.KEY + " help":
            embed = minigames.create_embed(
                title="LotR Trivia Bot help",
                content=self.config.HELP_TEXT,
                footnote=self. config.HELP_FOOTER)
            await channel.send(embed=embed)
#==============================================================================
        elif self.do_autoscript:
            result = minigames.find_similar_from_script\
            (message.content, self.script_condensed, self.script)
            if result:
                await message.add_reaction("✅")
                for line in result:
                    await channel.send(line)
