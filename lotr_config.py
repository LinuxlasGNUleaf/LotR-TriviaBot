import os

# MAIN CONFIG FILE
VERSION = "2.0"
MARKER = '*'
KEY = "lotr"
FOOTER = "A discord bot written in Python by JaWs"
CONFIG_PATH = ".config/discord/bots/lotr-bot/"

MAX_VIDEO_COUNT = 3

SCOREBOARD_LOC = os.path.join(os.getenv("HOME"), CONFIG_PATH, "scoreboard.pyobj")
MEME_LOG_LOC = os.path.join(os.getenv("HOME"), CONFIG_PATH, "meme_log.pyobj")
REDDIT_TOKEN = os.path.join(os.getenv("HOME"), CONFIG_PATH, "reddit.tk")
DISCORD_TOKEN = os.path.join(os.getenv("HOME"), CONFIG_PATH, "discord.tk")
GOOGLE_TOKEN = os.path.join(os.getenv("HOME"), CONFIG_PATH, "google.tk")

SCRIPT_LOC = "script.txt"
SILMARILLION_LOC = "silmarillion_edited.txt"
SILMARILLION_SENTENCES_COUNT = 2

TEH_LURD_CHANNEL_ID = 'UCYXpatz5Z4ek0M_5VR-Qt1A'
# crappy ASCII art for hangman game
STATES = [
    "``` \n \n \n \n \nililililillllililii```",
    "```    //\n    ||\n    ||\n    ||\n    ||    \nililililillllililii```",
    "```    //====\\\n    ||\n    ||\n    ||\n    ||\n    ||\nililililillllililii```",
    "```    //====\\\n    ||    |\n    ||   (\")\n    ||\n    ||\n    ||\nililililillllililii```",
    "```    //====\\\n    ||    |\n    ||   (\")\n    ||   \\|\n    ||\n    ||\nil\
ilililillllililii```",
    "```    //====\\\n    ||    |\n    ||   (\")\n    ||   \\|/\n    ||    X\n    \
||\n    ||\nililililillllililii```",
    "```    //====\\\n    ||    |\n    ||   (\")\n    ||   \\|/\n    ||    X\n    \
||   /\n    ||\nililililillllililii```",
    "```    //====\\\n    ||    |\n    ||   (\")\n    ||   \\|/\n    ||    X\n    \
||   / \\\n    ||\nililililillllililii```",
    "```    //====\\\n    ||\n    ||\n    ||   (\")\n    ||   \\|/\n    ||    X\n \
   ||   / \\\nililililillllililii```"]

INSULTS = ["Stupid fat {}!", "Fool of a {}!",
           "I would cut off your head {}... if it stood but a little higher from the ground.",
           "Dotard! What is the house of {} but a thatched barn where brigands \
drink in the reek, and their brats roll on the floor among the dogs?",
           "Hey, {}! Don't go getting too far behind. ~Sam", "Feanor gave up because of \
your stupidity, {}!", "Feanor did nothing wrong, but the same can not be said about you, {}!"]

COMPLIMENTS = ["Well done, my dear {}!",
               "{}, you should be counted amongst the wise of middleearth.",
               "Very good {}, I could not have done it better myself!"]

# some lambda code stolen from Gareth on codegolf to create ordinals:
ORDINAL = lambda n: "%d%s" % (n, "tsnrhtdd"[(n/10%10 != 1)*(n%10 < 4)*n%10::4])

HELP_TEXT = \
"""
Welcome to the LotR Trivia Bot!
This is a discord bot written in Python 3.
It utilizes the Discord, Reddit, and Youtube Data API.
The bot features mutliple minigames, including:

**- LotR - Trivia Game**
In this game you get asked trivia questions from LotR, the Hobbit,
the Silmarillion and the Extended Lore.
You have four possible answers, your score is tracked.
*to play a game:*
`{0} trivia`
*to see your score:*
`{0} profile`

**- LotR - Hangman**
Features the classic hangman game with LotR terms.
*to play a game:*
`{0} hangman`

**- Random Silmarillion quote**
Output a random Silmarillion quote on demand.
*to get a quote:*
`{0} squote`

**- Reddit meme**
Outputs a dank meme from r/lotrmemes.
*to get a meme:*
`{0} meme`

**- Autoscript feature**
Recognizes lines from the movie script and in the case of a 85% match, completes the sentence and prints the next dialog line to use this feature, send any __whole sentence from the LotR movies__, the bot will respond.

**- Youtube Video Search**
Allows you to provide keywords to search the videos of a channel.
The channel id is currently set in the config file.
to search for videos:
`{0} yt <max video count> <keywords>`

""".format(KEY)

HELP_FOOTER = \
"""
LICENSE:
LotR Trivia Bot version {0}, Copyright (C) 2020 JaWs
LotR Trivia Bot comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions; see the GPL License for details.
""".format(VERSION)
