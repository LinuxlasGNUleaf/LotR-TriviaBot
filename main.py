"""
A LotR-bot written by JaWs
"""
# coding=utf-8

# imports
import pickle
import os
import sys

sys.path.append(os.path.abspath('./discord'))
sys.path.append(os.path.abspath('./reddit'))

import lotr_config
import dc_client
import reddit_client

# ==========================> LISTS <==================================
SCOREBOARD = {}
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
except (FileNotFoundError, EOFError):
    print("[WARN]: scoreboard file not found, ignoring.")



# aquire Reddit credentials from file
try:
    with open(lotr_config.REDDIT_CREDENTIALS, "r") as tokenfile:
        info = tokenfile.readlines()
        for i in range(len(info)):
            info[i] = info[i].strip()
except (FileNotFoundError, EOFError):
    print("[ERROR]: reddit credentials not found! abort.")
    sys.exit(-1)
except IndexError:
    print("[ERROR]: reddit credentials invalid! abort.")
    sys.exit(-1)


# create the client objects
DC_CLIENT = dc_client.LotrBot(lotr_config, SCOREBOARD)
# REDDIT_CLIENT = reddit_client(lotr_config, info)

try:
    DC_CLIENT.run(TOKEN)
    print("\n[INFO]: Shutting down...")
    with open(lotr_config.SCOREBOARD_LOC, 'wb') as SC_FILE:
        pickle.dump(SCOREBOARD, SC_FILE)

except (KeyboardInterrupt, RuntimeError):
    print("\n[INFO]: Catched error... Shutting down...")
    with open(lotr_config.SCOREBOARD_LOC, 'wb') as SC_FILE:
        pickle.dump(SCOREBOARD, SC_FILE)
