"""
A LotR-bot written by JaWs
"""
# coding=utf-8

# imports
import pickle
import os
import sys

import praw

sys.path.append(os.path.abspath('./discord'))

import lotr_config
import dc_client

# ==========================> LISTS <==================================
SCOREBOARD = {}
BLOCKED = [] #temporarily blocked users (cannot issue commands)

# ==========================> CLIENT <==================================


# ==========================> STARTUP <==================================
# aquire discord token from file
with open(lotr_config.TOKEN_LOC, "r") as tokenfile:
    TOKEN = tokenfile.readline().strip()

# aquire Reddit credentials from file
with open(lotr_config.REDDIT_CREDENTIALS, "r") as tokenfile:
    info = tokenfile.readlines()
    for i in range(len(info)):
        info[i] = info[i].strip()
    client_id = info[0]
    client_secret = info[1]
    username = info[2]
    password = info[3]

# reddit = praw.Reddit(client_id=client_id,
#                      client_secret=client_secret,
#                      password=password,
#                      user_agent="reddit post yoinker by /u/_LegolasGreenleaf",
#                      username=username)
# print(reddit.user.me())

try:
    with open(lotr_config.SCOREBOARD_LOC, 'rb') as SC_FILE:
        SCOREBOARD = pickle.load(SC_FILE)
        print("successfully loaded scoreboard.pyobj")
except (FileNotFoundError, EOFError):
    print("scoreboard file not found, skipping.")

# create the client object
CLIENT = dc_client.LotrBot(lotr_config, SCOREBOARD)

try:
    CLIENT.run(TOKEN)
    print("\nShutting down...")
    with open(lotr_config.SCOREBOARD_LOC, 'wb') as SC_FILE:
        pickle.dump(SCOREBOARD, SC_FILE)

except (KeyboardInterrupt, RuntimeError):
    print("\nCatched error... Shutting down...")
    with open(lotr_config.SCOREBOARD_LOC, 'wb') as SC_FILE:
        pickle.dump(SCOREBOARD, SC_FILE)
