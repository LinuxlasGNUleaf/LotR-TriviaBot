import os

# MAIN CONFIG FILE
MARKER = '*'
KEY = "lotr"
FOOTER = "A discord bot written in Python by JaWs"
CONFIG_PATH = ".config/discord/bots/lotr-bot/"

SCOREBOARD_LOC = os.path.join(os.getenv("HOME"), CONFIG_PATH, "scoreboard.pyobj")
MEME_LOG_LOC = os.path.join(os.getenv("HOME"), CONFIG_PATH, "meme_log.pyobj")
REDDIT_TOKEN = os.path.join(os.getenv("HOME"), CONFIG_PATH, "reddit.tk")
DISCORD_TOKEN = os.path.join(os.getenv("HOME"), CONFIG_PATH, "discord.tk")
GOOGLE_TOKEN = os.path.join(os.getenv("HOME"), CONFIG_PATH, "google.tk")

SCRIPT_LOC = "lotr_fellowship.txt"
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
