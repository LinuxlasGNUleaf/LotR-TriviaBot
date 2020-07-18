'''
A LotR-bot written by JaWs
'''
# coding=utf-8

# imports
import pickle
import os
import sys
import lotr_config

sys.path.append(os.path.abspath('./discord'))
sys.path.append(os.path.abspath('./reddit'))
sys.path.append(os.path.abspath('./google'))

import dc_client
import reddit_client
import google_client

def getFile(loc, name, essential):
    try:
        with open(loc, 'r') as infofile:
            temp = infofile.readlines()
            if not temp and essential:
                raise EOFError
            for i, item in enumerate(temp):
                temp[i] = item.strip()
            return temp
    except (FileNotFoundError, EOFError):
        print('{}: {} not found!'.format('[ERROR]' if essential else '[WARN]', name))
        if essential:
            sys.exit(-1)


# ==========================> LISTS <==================================
SCOREBOARD = {}
MEME_LOG = {}
BLOCKED = [] # temporarily blocked users (cannot issue commands)

# ==========================> STARTUP <==================================
try:
    with open(lotr_config.DISCORD_CONFIG['scoreboard'], 'rb') as SC_FILE:
        SCOREBOARD = pickle.load(SC_FILE)
        print('[INFO]: unserialized trivia scoreboard')
    with open(lotr_config.REDDIT_CONFIG['memelog'], 'rb') as MEME_FILE:
        MEME_LOG = pickle.load(MEME_FILE)
        print('[INFO]: unserialized meme log')
except (FileNotFoundError, EOFError):
    print('[WARN]: meme log file not found, ignoring.')


TOKEN = getFile(lotr_config.DISCORD_CONFIG['token'], 'discord token', True)[0].strip()
if not TOKEN:
    raise EOFError('[ERROR]: discord token not found! abort.')

# aquire credentials from the token files
reddit_credentials = getFile(lotr_config.REDDIT_CONFIG['token'], 'reddit credentials', True)

google_credentials = getFile(lotr_config.YT_CONFIG['token'], 'yt api credentials', True)


# create the client instances
REDDIT_CLIENT = reddit_client.RedditClient(reddit_credentials, MEME_LOG)

YT_API_CLIENT = google_client.GoogleClient(google_credentials)

DC_CLIENT = dc_client.LotrBot(lotr_config, SCOREBOARD, REDDIT_CLIENT, YT_API_CLIENT)

try:
    DC_CLIENT.run(TOKEN)
    print('\n[INFO]: Shutting down...')
except (KeyboardInterrupt, RuntimeError):
    print('\n[INFO]: Catched error... Shutting down...')

with open(lotr_config.DISCORD_CONFIG['scoreboard'], 'wb') as SC_FILE:
    pickle.dump(SCOREBOARD, SC_FILE)
with open(lotr_config.REDDIT_CONFIG['memelog'], 'wb') as MEME_FILE:
    pickle.dump(MEME_LOG, MEME_FILE)
