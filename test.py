import lotr_config
import pickle

try:
    with open(lotr_config.DISCORD_CONFIG['discord.scoreboard'], 'rb') as SC_FILE:
        SCOREBOARD = pickle.load(SC_FILE)
        print('[INFO]: unserialized trivia scoreboard')
    with open(lotr_config.REDDIT_CONFIG['reddit.memelog'], 'rb') as MEME_FILE:
        MEME_LOG = pickle.load(MEME_FILE)
        print('[INFO]: unserialized meme log')
except (FileNotFoundError, EOFError):
    print('[WARN]: meme log file not found, ignoring.')

SCOREBOARD = {}
SCOREBOARD[230693513547743232] = (20,15)
SCOREBOARD[270904126974590976] = (30,5)
SCOREBOARD[277083306087022592] = (7, 3)

with open(lotr_config.DISCORD_CONFIG['discord.scoreboard'], 'wb') as SC_FILE:
    pickle.dump(SCOREBOARD, SC_FILE)