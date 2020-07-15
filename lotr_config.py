import os

# UTILS
ORDINAL = lambda n: '%d%s' % (n, 'tsnrhtdd'[(n/10%10 != 1)*(n%10 < 4)*n%10::4])

# MAIN CONFIG FILE
GENERAL_CONFIG = {
    'version': '2.1',
    'marker': '*',
    'key': 'lotr',
    'footer': 'A discord bot written in Python by JaWs',
    'config.path': '.config/discord/bots/lotr-bot/'
}

REDDIT_CONFIG = {
    'reddit.memelog': os.path.join(os.getenv('HOME'),
                                   GENERAL_CONFIG['config.path'],
                                   'meme_log.pyobj'),

    'reddit.token': os.path.join(os.getenv('HOME'),
                                 GENERAL_CONFIG['config.path'],
                                 'reddit.tk')
}

YT_CONFIG = {
    'yt.max_video_count': 3,
    'yt.token': os.path.join(os.getenv('HOME'),
                             GENERAL_CONFIG['config.path'],
                             'google.tk'),
    'yt.channel_id': 'UCYXpatz5Z4ek0M_5VR-Qt1A',
}
   

DISCORD_CONFIG = {
    'discord.scoreboard': os.path.join(os.getenv('HOME'),
                                       GENERAL_CONFIG['config.path'],
                                       'scoreboard.pyobj'),

    'discord.token': os.path.join(os.getenv('HOME'),
                                  GENERAL_CONFIG['config.path'],
                                  'discord.tk'),

    # minigames config
    'script.path': 'script.txt',
    'silmarillion.path': 'silmarillion_edited.txt',
    'silmarillion.sentence_count': 2,
    'trivia_timeout': 15,
    'hangman_timeout': 15,

    # crappy ASCII art for hangman game
    'hangman.ongoing_states':\
['``` \n \n \n \n \nililililillllililii```',
 '```    //\n    ||\n    ||\n    ||\n    ||    \nililililillllililii```',
 '```    //====\\\n    ||\n    ||\n    ||\n    ||\n    ||\nililililillllililii```',
 '```    //====\\\n    ||    |\n    ||   (")\n    ||\n    ||\n    ||\nililililillllililii```',
 '```    //====\\\n    ||    |\n    ||   (")\n    ||   \\|\n    ||\n    ||\nililil\
ilillllililii```',
 '```    //====\\\n    ||    |\n    ||   (")\n    ||   \\|/\n    ||\n    \
||\n    ||\nililililillllililii```',
 '```    //====\\\n    ||    |\n    ||   (")\n    ||   \\|/\n    ||    X\n    \
||   /\n    ||\nililililillllililii```'],

    'hangman.lost_state': '```    //====\\\n    ||    |\n    ||   (")\n    ||   \\|/\n    ||\
    X\n    ||   / \\\n    ||\nililililillllililii```',

    'hangman.won_state': '```    //====\\\n    ||\n    ||\n    ||   (")\n    ||   \\|/\n    ||\
    X\n    ||   / \\\nililililillllililii```',


    'discord.insults':\
['Stupid fat {}!',
 'Fool of a {}!',
 'I would cut off your head {}... if it stood but a little higher from the ground.',
 'Dotard! What is the house of {} but a thatched barn where brigands drink in the reek,\
and their brats roll on the floor among the dogs?',
 'Hey, {}! Don\'t go getting too far behind. ~Sam',
 'Feanor gave up because of your stupidity, {}!',
 'Feanor did nothing wrong, but the same can not be said about you, {}!',
 'Bombur does not approve.'
],

    'discord.compliments': \
['Well done, my dear {}!',
 '{}, you should be counted amongst the wise of middleearth.',
 'Very good {}, I could not have done it better myself!',
 'Bombur approves. Well done, {}!'],


    'discord.help_text': \
'''
Welcome to the LotR Trivia Bot!
This is a discord bot written in Python 3.
It utilizes the Discord, Reddit, and Youtube Data API.
The bot features mutliple minigames, including:

**- LotR - Trivia Game**
In this game you get asked trivia questions from LotR, the Hobbit,
the Silmarillion and the Extended Lore.
You have four possible answers, your score is tracked.
*to play a game:*
`{0} trivia`
*to see your score:*
`{0} profile`

**- LotR - Hangman**
Features the classic hangman game with LotR terms.
*to play a game:*
`{0} hangman`

**- Random Silmarillion quote**
Output a random Silmarillion quote on demand.
*to get a quote:*
`{0} squote`

**- Reddit meme**
Outputs a dank meme from r/lotrmemes.
*to get a meme:*
`{0} meme`

**- Autoscript feature**
Recognizes lines from the movie script and in the case of a 85% match,
completes the sentence and prints the next dialog line to use this feature,
send any __whole sentence from the LotR movies__, the bot will respond.

**- Youtube Video Search**
Allows you to provide keywords to search the videos of a channel.
The channel id is currently set in the config file.
to search for videos:
`{0} yt <max video count> <keywords>`

'''.format(GENERAL_CONFIG['key']),


    'discord.help_footer':\
'''LICENSE:
LotR Trivia Bot version {}, Copyright (C) 2020 JaWs
LotR Trivia Bot comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions; see the GPL License for details.
'''.format(GENERAL_CONFIG['version'])
}
