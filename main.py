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
sys.path.append(os.path.abspath('./yt_data_api'))
sys.path.append(os.path.abspath('./google'))

import dc_client
import reddit_client
import yt_api_client
import google_search_client

def get_token(loc, name, essential):
    '''
    returns token from a given tokenfile location, \
and raises an Error if file is essential and not valid.
    '''
    try:
        with open(loc, 'r') as infofile:
            temp = infofile.readlines()
            if not temp and essential:
                raise EOFError
            for i, item in enumerate(temp):
                temp[i] = item.strip()
            return temp
    except (FileNotFoundError, EOFError):
        msg = '{}: {} not found!'.format('[ERROR]' if essential else '[WARN]', name)
        if essential:
            raise EOFError(msg)
        else:
            print(msg)


# ==========================> LISTS <==================================
SCOREBOARD = {}
SETTINGS = {}
MEME_LOG = {}
BLOCKED = [] # temporarily blocked users (cannot issue commands)

# ==========================> STARTUP <==================================
try:
    with open(lotr_config.DISCORD_CONFIG['scoreboard.loc'], 'rb') as SC_FILE:
        SCOREBOARD = pickle.load(SC_FILE)
        print('[INFO]: unserialized trivia scoreboard')
except (FileNotFoundError, EOFError):
    print('[WARN]: could not unserialize trivia scoreboard! Creating empty one instead.')
    open(lotr_config.DISCORD_CONFIG['scoreboard.loc'], 'w').close()

try:
    with open(lotr_config.DISCORD_CONFIG['settings.loc'], 'rb') as SET_FILE:
        SETTINGS = pickle.load(SET_FILE)
        print('[INFO]: unserialized settings')
except (FileNotFoundError, EOFError):
    print('[WARN]: could not unserialize settings! Creating empty one instead.')
    open(lotr_config.DISCORD_CONFIG['settings.loc'], 'w').close()

try:
    with open(lotr_config.REDDIT_CONFIG['memelog.loc'], 'rb') as MEME_FILE:
        MEME_LOG = pickle.load(MEME_FILE)
        print('[INFO]: unserialized meme log')
except (FileNotFoundError, EOFError):
    print('[WARN]: could not unserialize meme log! Creating empty one instead.')
    open(lotr_config.REDDIT_CONFIG['memelog.loc'], 'w').close()


TOKEN = get_token(lotr_config.DISCORD_CONFIG['token.loc'], 'discord token', True)[0].strip()
if not TOKEN:
    raise EOFError('[ERROR]: discord token not found! abort.')

# aquire credentials from the token files
reddit_credentials = get_token(lotr_config.REDDIT_CONFIG['token.loc'], 'reddit credentials', True)

yt_api_credentials = get_token(lotr_config.YT_CONFIG['token.loc'], 'yt api credentials', True)

# create the client instances
REDDIT_CLIENT = reddit_client.RedditClient(reddit_credentials, MEME_LOG)

YT_API_CLIENT = yt_api_client.YtAPIClient(yt_api_credentials)

GOOGLE_SEARCH_CLIENT = google_search_client.GoogleSearchClient()

DC_CLIENT = dc_client.LotrBot(lotr_config,
                              SCOREBOARD,
                              SETTINGS,
                              MEME_LOG,
                              REDDIT_CLIENT,
                              YT_API_CLIENT,
                              GOOGLE_SEARCH_CLIENT)

try:
    DC_CLIENT.run(TOKEN)
    print('\n[INFO]: Shutting down...')
except (KeyboardInterrupt, RuntimeError):
    print('\n[INFO]: Catched error... Shutting down...')

with open(lotr_config.DISCORD_CONFIG['scoreboard.loc'], 'wb') as SC_FILE:
    pickle.dump(SCOREBOARD, SC_FILE)
with open(lotr_config.REDDIT_CONFIG['memelog.loc'], 'wb') as MEME_FILE:
    pickle.dump(MEME_LOG, MEME_FILE)
with open(lotr_config.DISCORD_CONFIG['settings.loc'], 'wb') as SET_FILE:
    pickle.dump(SETTINGS, SET_FILE)
