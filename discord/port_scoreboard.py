import pickle
import sys
import yaml
import os
from shutil import copyfile

def update_cache_path(path):
    return os.path.join(config['general']['path'], path)

with open("config.yaml", 'r') as cfg_stream:
    try:
        sys.stdout.write('parsing config file...')
        config = yaml.safe_load(cfg_stream)
        config['general']['path'] = eval(config['general']['path'])
        print('done.')
    except yaml.YAMLError as exc:
        print("While parsing the config file, the following error occured: "+exc)
        exit(-1)

config['discord']['trivia']['cache'] = update_cache_path(config['discord']['trivia']['cache'])

with open(config['discord']['trivia']['cache'], 'rb') as SC_FILE:
    scoreboard = pickle.load(SC_FILE)

copyfile(config['discord']['trivia']['cache'], config['discord']['trivia']['cache']+'.bak')

for user, value in scoreboard.items():
    if len(value) != 2:
        print('Scoreboard length invalid!')
        exit(-1)
    value = list(value)
    value.append(0)
    print(user, value)
    scoreboard[user] = value

with open(config['discord']['trivia']['cache'], 'wb') as SC_FILE:
    scoreboard = pickle.dump(scoreboard, SC_FILE)
