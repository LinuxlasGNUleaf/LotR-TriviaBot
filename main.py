'''
A LotR-bot written by JaWs
'''
# coding=utf-8

# imports
import pickle
import os
import sys
import yaml

sys.path.append(os.path.abspath('./discord'))
sys.path.append(os.path.abspath('./reddit'))
sys.path.append(os.path.abspath('./yt_data_api'))
sys.path.append(os.path.abspath('./google'))

import dc_client
import reddit_client
import yt_api_client
import google_search_client

def get_token(path, name):
    '''
    returns token from a given tokenfile location, and raises an error if not valid.
    '''
    try:
        with open(path, 'r') as infofile:
            temp = infofile.readlines()
            if not temp:
                raise EOFError
            for i, item in enumerate(temp):
                temp[i] = item.strip()
            return temp
    except (FileNotFoundError, EOFError):
        msg = '[ERROR]: {} not found!'.format(name)
        raise EOFError(msg)

def get_cache(path, name):
    try:
        with open(path, 'rb') as cache_file:
            obj = pickle.load(cache_file)
            print('[INFO]: unserialized {} cache.'.format(name))
            return obj
    except (FileNotFoundError, EOFError):
        print('[WARN]: could not unserialize {}! Creating empty one instead.'.format(name))
        open(path, 'w').close()
        return {}

def update_cache_path(path):
    return os.path.join(config['general']['path'], path)

if __name__ == '__main__':
    # ==========================> LISTS <==================================
    scoreboard = {}
    settings = {}
    memelog = {}
    BLOCKED = [] # temporarily blocked users (cannot issue commands)
    # ==========================> STARTUP <==================================


    with open("config.yaml", 'r') as cfg_stream:
        try:
            sys.stdout.write('parsing config file...')
            config = yaml.safe_load(cfg_stream)
            config['general']['path'] = eval(config['general']['path'])
            print('done.')
        except yaml.YAMLError as exc:
            print("While parsing the config file, the following error occured: "+exc)
            exit(-1)

    # unserialize caches from the cache files
    config['discord']['trivia']['cache'] = update_cache_path(config['discord']['trivia']['cache'])
    config['discord']['settings']['cache'] = update_cache_path(config['discord']['settings']['cache'])
    config['reddit']['cache'] = update_cache_path(config['reddit']['cache'])
    config['discord']['trivia']['stats_file'] = update_cache_path(config['discord']['trivia']['stats_file'])

    try:
        with open(config['discord']['trivia']['stats_file'], 'rb') as stats_file:
            pickle.load(stats_file)
    except (FileNotFoundError, EOFError):
        with open(config['discord']['trivia']['stats_file'], 'wb') as stats_file:
            pickle.dump({}, stats_file)

    scoreboard = get_cache(config['discord']['trivia']['cache'], 'Scoreboard Cache')
    settings = get_cache(config['discord']['settings']['cache'], 'Settings Cache')
    memelog = get_cache(config['reddit']['cache'], 'Reddit Cache')


    # aquire credentials from the token files
    config['discord']['token'] = update_cache_path(config['discord']['token'])
    config['youtube']['token'] = update_cache_path(config['youtube']['token'])

    discord_token = get_token(config['discord']['token'], 'Discord Token')[0].strip()
    yt_api_credentials = get_token(config['youtube']['token'], 'Youtube API Credentials')

    # create the client instances
    YT_API_CLIENT = yt_api_client.YtAPIClient(yt_api_credentials)
    GOOGLE_SEARCH_CLIENT = google_search_client.GoogleSearchClient()
    REDDIT_CLIENT = reddit_client.RedditClient(memelog, config)

    DC_CLIENT = dc_client.LotrBot(config,
                                scoreboard,
                                settings,
                                memelog,
                                REDDIT_CLIENT,
                                YT_API_CLIENT,
                                GOOGLE_SEARCH_CLIENT)

    try:
        DC_CLIENT.run(discord_token)
        print('\n[INFO]: Shutting down...')
    except (KeyboardInterrupt, RuntimeError):
        print('\n[INFO]: Catched error... Shutting down...')

    with open(config['discord']['trivia']['cache'], 'wb') as SC_FILE:
        pickle.dump(scoreboard, SC_FILE)
    with open(config['discord']['settings']['cache'], 'wb') as SET_FILE:
        pickle.dump(settings, SET_FILE)
    with open(config['reddit']['cache'], 'wb') as MEME_FILE:
        pickle.dump(memelog, MEME_FILE)
