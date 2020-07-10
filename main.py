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

# ==========================> LISTS <==================================
SCOREBOARD = {}
MEME_LOG = {}
BLOCKED = [] #temporarily blocked users (cannot issue commands)

# ==========================> STARTUP <==================================
try:
    with open(lotr_config.DISCORD_CONFIG['discord.scoreboard'], 'rb') as SC_FILE:
        SCOREBOARD = pickle.load(SC_FILE)
        print('[INFO]: unserialized trivia scoreboard')
    with open(lotr_config.REDDIT_CONFIG['discord.memelog'], 'rb') as MEME_FILE:
        MEME_LOG = pickle.load(MEME_FILE)
        print('[INFO]: unserialized meme log')
except (FileNotFoundError, EOFError):
    print('[WARN]: meme log file not found, ignoring.')

# aquire discord credentials from file
try:
    with open(lotr_config.DISCORD_CONFIG['discord.token'], 'r') as tokenfile:
        TOKEN = tokenfile.readline().strip()
        if not TOKEN:
            raise EOFError
except (FileNotFoundError, EOFError):
    print('[ERROR]: discord token not found! abort.')
    sys.exit(-1)

# aquire reddit credentials from file
try:
    with open(lotr_config.REDDIT_CONFIG['reddit.token'], 'r') as tokenfile:
        reddit_credentials = tokenfile.readlines()
        for i, item in enumerate(reddit_credentials):
            reddit_credentials[i] = item.strip()
except (FileNotFoundError, EOFError):
    print('[ERROR]: reddit credentials not found! abort.')
    sys.exit(-1)

# aquire Google credentials from file
try:
    with open(lotr_config.YT_CONFIG['yt.token'], 'r') as tokenfile:
        google_credentials = tokenfile.readlines()
        for i, item in enumerate(google_credentials):
            google_credentials[i] = item.strip()
except (FileNotFoundError, EOFError):
    print('[ERROR]: google credentials not found! abort.')
    sys.exit(-1)

# create the reddit client
REDDIT_CLIENT = reddit_client.RedditClient(lotr_config, reddit_credentials, MEME_LOG)

# create the Google client
GOOGLE_CLIENT = google_client.GoogleClient(google_credentials)

# create the discord client and pass the reddit client
DC_CLIENT = dc_client.LotrBot(lotr_config, SCOREBOARD, REDDIT_CLIENT, GOOGLE_CLIENT)

try:
    DC_CLIENT.run(TOKEN)
    print('\n[INFO]: Shutting down...')
except (KeyboardInterrupt, RuntimeError):
    print('\n[INFO]: Catched error... Shutting down...')

with open(lotr_config.DISCORD_CONFIG['discord.scoreboard'], 'wb') as SC_FILE:
    pickle.dump(SCOREBOARD, SC_FILE)
with open(lotr_config.DISCORD_CONFIG['discord.memelog'], 'wb') as MEME_FILE:
    pickle.dump(MEME_LOG, MEME_FILE)
