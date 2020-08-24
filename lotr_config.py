'''
this is the config file for the LotR-Triva Bot and applies to all servers,
DMs, etc. It also handles the location of tokenfiles, serialized objects
as well as settings for minigames.
'''
import os

# UTILS
ORDINAL = lambda n: '%d%s' % (n, 'tsnrhtdd'[(n/10%10 != 1)*(n%10 < 4)*n%10::4])

# MAIN CONFIG FILE
GENERAL_CONFIG = {
    'version': '2.3',
    'marker': '*',
    'key': 'lotr',
    'footer': 'A discord bot written in Python by JaWs',
    'config.path': '.config/discord/bots/lotr-bot/',
    'superusers': [277083306087022592]
}

REDDIT_CONFIG = {
    'subreddit': 'lotrmemes',
    'memelog.loc': os.path.join(os.getenv('HOME'),
                                GENERAL_CONFIG['config.path'],
                                'meme_log.pyobj'),

    'token.loc': os.path.join(os.getenv('HOME'),
                              GENERAL_CONFIG['config.path'],
                              'reddit.tk')
}

YT_CONFIG = {
    'max_video_count': 3,
    'token.loc': os.path.join(os.getenv('HOME'),
                              GENERAL_CONFIG['config.path'],
                              'google.tk'),
    'channel_id': 'UCYXpatz5Z4ek0M_5VR-Qt1A',
}

GOOGLE_CONFIG = {
    'site':'tolkiengateway.net'
}

DISCORD_CONFIG = {
    'scoreboard.loc': os.path.join(os.getenv('HOME'),
                                   GENERAL_CONFIG['config.path'],
                                   'scoreboard.pyobj'),

    'settings.loc': os.path.join(os.getenv('HOME'),
                                 GENERAL_CONFIG['config.path'],
                                 'dc_settings.pyobj'),

    'settings.help': \
'''
**How the config works:**
You can set preferences for a server or a channel (DMs excluded),\
which means you set the feature to on / off.
If set, the channel preference for a feature will __always__ be relevant.
If the channel preference for this feature is not set, the server-preference will be used.
If the server-preference is not set, the defaults will be used, which is "allowed".\n
**How to use the config command:**
`{0} config <feature> on` to turn <feature> on for this channel
`{0} config <feature> off` to turn <feature> off for this channel
`{0} config <feature> unset` to unset <feature> setting for this channel
(the server preferences are used, or if these are not set either, the defaults.)
\n
`{0} config <feature> server-on` to turn <feature> on for this server** \
(all channels where the bot has send_messages permission)
`{0} config <feature> server-off` to turn <feature> off for this server**
`{0} config <feature> server-unset` to unset <feature> for this server
(the channel preferences are used, or if these are not set, directly the defaults.)
'''.format(GENERAL_CONFIG['key']),

    'settings.features': ['autoscript',
                          'memes',
                          'trivia-quiz',
                          'yt-search',
                          'hangman',
                          'squote'],

    'settings.defaults': {'autoscript':1,
                          'memes':1,
                          'trivia-quiz':1,
                          'yt-search':1,
                          'hangman':1,
                          'squote':1},

    'token.loc': os.path.join(os.getenv('HOME'),
                              GENERAL_CONFIG['config.path'],
                              'discord.tk'),

    # minigames config
    'script.path': 'script.txt',
    'silmarillion.path': 'silmarillion_edited.txt',
    'silmarillion.sentence_count': 2,

    # this is the char per second multiplier. According to the web,
    # the average reading speed is 15.7 chars/second
    'trivia.multiplier': 15.7,
    # this is thinking time that is added to the calculated reading time
    'trivia.extra_time': 5.0,
    # =============================
    'hangman.timeout': 20,
    'autoscript.scene_end_interrupt': False,

    'custom_status': \
['Boromir not simply walk into Mordor',
 'Viggo Mortensen break his toe',
 'Gimli lose his shoe',
 'Legolas no-scoping Orcs',
 'Merry and Pippin smoking pipe-weed',
 'Eowyn brewing a stew',
 'Gandalf bumping his head in Bag End',
 'Feanor doing nothing wrong',
 'Frodo getting stabbed by Shelob',
 'Smeagol smacc Sam with a stone',
 'Aragorn charging for Frodo'],

    "hangman.allowed_chars":\
['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'],

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


    'insults':\
['Stupid fat {}!',
 'Fool of a {}! Stay quiet next time and rid us of your stupidity!',
 'I would cut off your head {}... if it stood but a little higher from the ground.',
 'Dotard! What is the house of {} but a thatched barn where brigands drink in the reek,\
and their brats roll on the floor among the dogs?',
 'Hey, {}! Don\'t go getting too far behind. ~Sam',
 'Feanor gave up because of your stupidity, {}!',
 'Feanor did nothing wrong, but the same can not be said about you, {}!',
 'Bombur does not approve.',
 'Stop your squeaking you dunghill rat, {}!',
 'You stinking two-faced sneak!',
 'What are you doing, you useless scum?'],

    'compliments': \
['Well done, my dear {}!',
 '{}, you should be counted amongst the wise of middleearth.',
 'Very good {}, I could not have done it better myself!',
 'Bombur approves. Well done, {}!',
 'May the wind under your wings bear you where the sun sails and the moon walks.'],


    'help.text': \
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
*to create a scoreboard for the whole server:*
`{0} scoreboard`

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
The channel id is set in the config file.
*to search for videos:*
`{0} yt "query"`
(note the "quotes". you can also provide a video count before or after the query)

**- LotR Wiki Search**
Allows you to search the wiki for a specific topic.
The wiki URL is set in the config file.
*to search the wiki:*
`{0} search <keywords>`
'''.format(GENERAL_CONFIG['key']),


    'help.footer':\
'''LICENSE:
LotR Trivia Bot version {}, Copyright (C) 2020 JaWs
LotR Trivia Bot comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions; see the GPL License for details.
'''.format(GENERAL_CONFIG['version'])
}
