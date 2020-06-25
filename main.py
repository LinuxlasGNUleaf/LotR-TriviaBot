"""
A LotR-bot written by JaWs
"""
# coding=utf-8

# imports
import pickle
import os
import sys
import lotr_config

sys.path.append(os.path.abspath('./discord'))
sys.path.append(os.path.abspath('./reddit'))

import dc_client
import reddit_client

# ==========================> LISTS <==================================
SCOREBOARD = {}
MEME_LOG = {}
BLOCKED = [] #temporarily blocked users (cannot issue commands)

# ==========================> STARTUP <==================================

# DISCORD
# aquire discord token from file
try:
    with open(lotr_config.TOKEN_LOC, "r") as tokenfile:
        TOKEN = tokenfile.readline().strip()
except (FileNotFoundError, EOFError):
    print("[ERROR]: discord token not found! abort.")
    sys.exit(-1)
if not TOKEN:
    print("[ERROR]: discord token found empty! abort.")
    sys.exit(-1)

try:
    with open(lotr_config.SCOREBOARD_LOC, 'rb') as SC_FILE:
        SCOREBOARD = pickle.load(SC_FILE)
        print("[INFO]: unserialized trivia scoreboard")
    with open(lotr_config.MEME_LOG_LOC, 'rb') as MEME_FILE:
        MEME_LOG = pickle.load(MEME_FILE)
        print("[INFO]: unserialized meme log")
except (FileNotFoundError, EOFError):
    print("[WARN]: meme log file not found, ignoring.")



# aquire Reddit credentials from file
try:
    with open(lotr_config.REDDIT_CREDENTIALS, "r") as tokenfile:
        info = tokenfile.readlines()
        for i, item in enumerate(info):
            info[i] = item.strip()
except (FileNotFoundError, EOFError):
    print("[ERROR]: reddit credentials not found! abort.")
    sys.exit(-1)
except IndexError:
    print("[ERROR]: reddit credentials invalid! abort.")
    sys.exit(-1)


# create the reddit client
REDDIT_CLIENT = reddit_client.RedditClient(lotr_config, info, MEME_LOG)

# create the discord client and pass the reddit client
DC_CLIENT = dc_client.LotrBot(lotr_config, SCOREBOARD, REDDIT_CLIENT)

try:
    DC_CLIENT.run(TOKEN)
    print("\n[INFO]: Shutting down...")
except (KeyboardInterrupt, RuntimeError):
    print("\n[INFO]: Catched error... Shutting down...")

with open(lotr_config.SCOREBOARD_LOC, 'wb') as SC_FILE:
    pickle.dump(SCOREBOARD, SC_FILE)
with open(lotr_config.MEME_LOG_LOC, 'wb') as MEME_FILE:
    pickle.dump(SCOREBOARD, MEME_FILE)
