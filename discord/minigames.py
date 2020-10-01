'''
Library for all the minigames for the LotR Trivia Bot. Accessed by the Discord Client
'''
import random
import csv
import string
import sys
from difflib import SequenceMatcher
from html import unescape
from time import strftime
import asyncio
import pickle

import discord

async def auto_save(config, scoreboard, memelog, settings):
    '''
    autosave feature
    '''
    sys.stdout.write('\nAutosave initialized.')
    msg_len = 0
    while True:
        await asyncio.sleep(config.GENERAL_CONFIG['autosave.interval'])
        with open(config.DISCORD_CONFIG['scoreboard.loc'], 'wb') as sc_file:
            pickle.dump(scoreboard, sc_file)
        with open(config.REDDIT_CONFIG['memelog.loc'], 'wb') as meme_file:
            pickle.dump(memelog, meme_file)
        with open(config.DISCORD_CONFIG['settings.loc'], 'wb') as set_file:
            pickle.dump(settings, set_file)

        msg = strftime('Last Autosave: %X on %a %d/%m/%y')
        msg_len = max(msg_len, len(msg))
        sys.stdout.write('\r{}{}'.format(msg, ((msg_len-len(msg))*' ')))


async def create_hangman_game(channel, bot, user, settings, config, blocked):
    '''
    creates and manages the hangman minigame
    '''
    if not feature_allowed('hangman', channel, settings, config):
        return

    with open('words.csv', 'r') as csvfile:
        word = random.choice(csvfile.readlines()).strip()
    word_condensed = word.lower().replace(' ', '')

    steps = 2 if len(word_condensed) <= 6 else 1

    game_states = config.DISCORD_CONFIG['hangman.ongoing_states']
    end_states = config.DISCORD_CONFIG['hangman.end_states']

    used_chars = []  # used characters array
    max_ind = len(game_states)-1 # max index
    ind = 0

    h_embed = create_hangman_embed(user, word, game_states[0], 0, [], True)
    hangman = await channel.send(embed=h_embed)

    def check(chk_msg):
        return chk_msg.author == user and chk_msg.channel == channel

    blocked.append(user.id)

    while True:
        try:
            msg = await bot.wait_for('message',
                                     check=check,
                                     timeout=config.DISCORD_CONFIG['hangman.timeout'])
            msg = msg.content.lower()

        except asyncio.TimeoutError:
            h_embed = create_hangman_embed(user, word, end_states[0], 8, used_chars, False)
            await hangman.edit(embed=h_embed)
            await channel.send('Game over! You took too long to answer!')
            break

        for char in msg:
            if char not in used_chars and char in config.DISCORD_CONFIG['hangman.allowed_chars']:
                used_chars.append(char)
                if char not in word_condensed:
                    ind += steps
        used_chars.sort()

        if ind > max_ind:
            h_embed = create_hangman_embed(user, word, end_states[0], 8, used_chars, False)
            await hangman.edit(embed=h_embed)
            await channel.send('Game over! You lost all your lives!')
            break

        for char in word_condensed:
            if char not in used_chars and char.isalpha():
                break
        else:
            h_embed = create_hangman_embed(user, word, end_states[1], 0, used_chars, False)
            await hangman.edit(embed=h_embed)
            await channel.send('Congratulations! You won the game!')
            break

        h_embed = create_hangman_embed(user, word, game_states[ind], ind, used_chars, True)
        await hangman.edit(embed=h_embed)

    blocked.remove(user.id)


async def display_profile(channel, user, settings, config, scoreboard):
    '''
    creates a profile for the user and displays it.
    '''
    if not feature_allowed('trivia-quiz', channel, settings, config):
        return
    if not user.id in scoreboard.keys():
        await channel.send('You have to play a game of trivia before a profile can be generated! Use `{} trivia` to take a quiz!'.format(config.GENERAL_CONFIG['key']))
        return

    played, wins = scoreboard[user.id]
    color = (map_vals(wins/played, 0, 1, 255, 0), map_vals(wins/played, 0, 1, 0, 255), 0)

    title = '{}\'s results'.format(user.display_name)
    content = 'Trivia games played: {}\nTrivia games won: {}\n\
               Win/Played ratio: {}%'\
              .format(played, wins, round(wins/played*100, 2))
    await channel.send(embed=create_embed(title, content=content, color=color))


def prepare_trivia_question(user, count, config):
    '''
    picks a trivia question and prepares the embed
    '''
    # get random question
    with open('questions.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        content = random.choice(list(csvreader))

    # pop the source and the question (first element)
    source = content.pop(0)
    question = content.pop(0)
    # shuffle answers
    random.shuffle(content)

    answers = content.copy()
    for i, item in enumerate(answers):
        if item.startswith(config.GENERAL_CONFIG['marker']):
            answers[i] = item[1:]
            correct_index = i+1
            break

    # create author info
    author_name = '{}\'s {} trial in the Arts of Middle Earth trivia'\
        .format(user.display_name, config.ORDINAL(count) if count else '')
    author_info = (author_name, user.avatar_url)

    # create the embed text
    embed_text = '```markdown\n'
    char_count = len(question)
    for num, cont in enumerate(answers):
        embed_text += '{}. {}\n'.format(num+1, cont)
        char_count += len(cont)

    # calculate the timeout
    timeout = round(char_count / config.DISCORD_CONFIG['trivia.multiplier'] + \
                    config.DISCORD_CONFIG['trivia.extra_time'], 1)

    # add source and timeout to embed text
    embed_text += '```\nsource: {}'.format(source)
    embed_text += '\n:stopwatch: {} seconds'.format(round(timeout))

    # send the trivia question
    return (create_embed(question, author_info=author_info, content=embed_text),
            correct_index,
            timeout)


async def create_trivia_quiz(channel, bot, user, settings, config, blocked, scoreboard):
    '''
    creates and manages a trivia quiz for a user
    '''
    if not feature_allowed('trivia-quiz', channel, settings, config):
        return

    if user.id in scoreboard.keys():
        count, wins = scoreboard[user.id]
        count += 1
    else:
        count, wins = (1, 0)

    # function to check whether the user's reply is valid
    def check(chk_msg):
        return chk_msg.author == user and chk_msg.channel == channel

    embed, correct_index, timeout = prepare_trivia_question(user, count, config)
    trivia_embed = await channel.send(embed=embed)

    # block user from sending any commands
    blocked.append(user.id)
    try:
        msg = await bot.wait_for('message', check=check, timeout=timeout)
        if msg.content.isdigit():
            msg = int(msg.content)
            if msg == correct_index:
                # right answer
                wins += 1
                ret_string = create_reply(user, False, config)
            else:
                # invalid digit
                ret_string = create_reply(user, True, config)
        else:
            # not a digit
            ret_string = create_reply(user, True, config) + \
                '\nWhat is that supposed to be? Clearly not a digit...'

    except asyncio.TimeoutError:
        ret_string = create_reply(user, True, config) + '\nYou took too long to answer!'

    # unblock user afterwards
    blocked.remove(user.id)

    # update scoreboard, send reply and delete the question
    scoreboard[user.id] = (count, wins)
    await channel.send(ret_string)
    await trivia_embed.delete()

    # certain chance to send a small tip
    if random.random() <= config.DISCORD_CONFIG['trivia.tip_probability']:
        tip = random.choice(config.DISCORD_CONFIG['trivia.tips'])
        await channel.send(tip.format(config.DISCORD_CONFIG['trivia.link']), delete_after=30)


async def manage_config(channel, user, content, config, settings):
    '''
    manages the settings for this channel/server
    '''
    content = content.split(' ')[2:]
    server = channel.guild

    for i, item in enumerate(content):
        content[i] = item.strip()

    # user wants to change the settings
    if content[0] in config.DISCORD_CONFIG['settings.features']:
        if channel.permissions_for(user).manage_channels or \
            user.id in config.GENERAL_CONFIG['superusers']:
            if user.id in config.GENERAL_CONFIG['superusers']:
                await channel.send(':desktop: Superuser detected, overriding permissions...')
            await edit_settings(content, settings, channel)
        else:
            await channel.send(':x: You do not have permission to change these settings!')

    # user wants to see the help message
    elif content[0] == 'help':
        await channel.send(config.DISCORD_CONFIG['settings.help'])

    # user wants to see the config embed
    elif content[0] == 'show':
        title = 'Config for #{}, Server: {}'.format(channel, server)
        content = ''
        for feature in config.DISCORD_CONFIG['settings.features']:
            content += '**Feature `{}`:**\n'.format(feature)

            server_setting = ':grey_question:'
            if server.id in settings.keys():
                if feature in settings[server.id]:
                    server_setting = ':white_check_mark:' if settings[server.id][feature] else ':x:'

            channel_setting = ':grey_question:'
            if channel.id in settings.keys():
                if feature in settings[channel.id]:
                    channel_setting = ':white_check_mark:' if settings[channel.id][feature] else ':x:'

            effective = ':white_check_mark:' if feature_allowed(feature,
                                                                channel,
                                                                settings,
                                                                config) else ':x:'
            content += 'Server: {} Channel: {} Effective: {}\n\n'\
                    .format(server_setting, channel_setting, effective)

        embed = create_embed(title=title, content=content, footnote=config.GENERAL_CONFIG['footer'])
        channel.send(embed=embed)
    else:
        await channel.send('Unknown Feature! Try one of the following:\n`'+'`, `'
                           .join(config.DISCORD_CONFIG['settings.features']+['help', 'show'])+'`')


async def display_scoreboard(channel, server, settings, config, scoreboard):
    '''
    display a trivia scoreboard for the server
    '''
    if not feature_allowed('trivia-quiz', channel, settings, config):
        return

    users = server.members
    found_users = []
    scoreboard_string = ''
    for user in users:
        if user.id in scoreboard.keys() and scoreboard[user.id][1] > 0:
            found_users.append([scoreboard[user.id][1], user.name,
                                round((scoreboard[user.id][1] / scoreboard[user.id][0])*100, 1)])

    medals = ['🥇 **Eru Ilúvatar:**\n{}', '🥈 **Manwë:**\n{}', '🥉 Gandalf:\n{}\n', '👏 {}']
    user_str = '**[{} pts]** {} ({}%)'
    for i, user in enumerate(sorted(found_users, key=lambda x: x[0])[::-1]):
        temp = user_str.format(*user)

        if i < len(medals):
            scoreboard_string += medals[i].format(temp)+'\n'
        else:
            scoreboard_string += medals[-1].format(temp)+'\n'
    await channel.send(embed=create_embed(title='Scoreboard for: *{}*'.format(server), content=scoreboard_string))


async def lotr_battle(channel, bot, user, content, config, settings):
    '''
    initiates and manages a trivia battle between two users
    '''
    if not feature_allowed('trivia-quiz', channel, settings, config):
        return

    # fetch the tagged user, exit conditions for bots / same user
    try:
        players = [user, await bot.fetch_user(content.split('<@')[-1][:-1])]
        if players[1].bot or players[1] == user:
            await channel.send('I suppose you think that was terribly clever.\nYou can\'t fight yourself or a bot! Tag someone else!')
            return
    except (discord.errors.HTTPException, IndexError):
        await channel.send('Please tag a valid user here you want to battle.')
        return

    await channel.send('{}, are you ready to battle {}? If so, respond with `yes`, otherwise do nothing or respond with `no`'\
                       .format(players[1].display_name, players[0].display_name))

    # waiting for a response by the opponent
    def ready_check(chk_msg):
        return (chk_msg.author == players[1] and
                chk_msg.channel == channel)

    bot.blocked.append(players[1].id)
    try:
        msg = await bot.wait_for('message', check=ready_check, timeout=bot.config.DISCORD_CONFIG['battle.timeout'])

        if msg.content.lower() == 'yes':
            await channel.send('{}, your opponent is ready. Let the game begin!'.format(user.mention))
        elif msg.content.lower() == 'no':
            await channel.send('{}, your opponent is not ready to battle just yet.'.format(user.mention))
        else:
            await channel.send('... well, I will take that as a no. {}, your opponent is not ready to battle just yet.'.format(user.mention))
            return
    except asyncio.TimeoutError:
        await channel.send('{}, your opponent did not respond.'.format(user.mention))
        return
    bot.blocked.remove(players[1].id)

    # create user DMs, in case they did not yet exist
    for player in players:
        if not player.dm_channel:
            await player.create_dm()

    def answer_check(chk_msg):
        # check whether author is opponent and channel is the corresponding DM
        if chk_msg.author in pending and chk_msg.channel == chk_msg.author.dm_channel:
            pending.remove(chk_msg.author)
            if chk_msg.content.strip().isdigit():
                answers[players.index(chk_msg.author)] = (int(chk_msg.content.strip()) == question[1])

        # return true if pending is empty
        return not pending

    await channel.send('I will send you both a trivia question in a few seconds.\
Answer it in time and continue to do so until the game is over. Then return to this chat to see who won.')


    # preparing score embed
    score = [0, 0]
    max_char = max(len(players[0].display_name), len(players[1].display_name))
    content = '```\n{0}: {2}\n{1}: {3}```'\
              .format(players[0].display_name.ljust(max_char+1),
                      players[1].display_name.ljust(max_char+1),
                      score[0], score[1])

    score_msg = await channel.send(embed=create_embed(title='LotR Battle Score', color=(255, 0, 0), content=content))
    round_ind = 0
    timeout = 3

    while True:
        # reset / manage round variables
        round_ind += 1
        pending = players.copy()
        answers = [-1]*len(players)

        # get new trivia question and distribute it
        question = prepare_trivia_question(player, 0, config)
        for player in players:
            await player.dm_channel.send(embed=question[0])

        # try to get an answer from all pending players
        try:
            await bot.wait_for('message', check=answer_check, timeout=question[2])
        except asyncio.TimeoutError:
            pass

        # if both players failed or won
        if answers[0] == answers[1]:
            for player in players:
                if answers[0] == 1: # both got it right
                    await player.dm_channel.send('Well done! You both answered correctly.')
                elif answers[0] == 0:
                    await player.dm_channel.send('You fools! Both of you answered incorrectly.')
                else:
                    timeout -= 1
                    await player.dm_channel.send('You both did not answer in time! Timeout in {} rounds.'.format(timeout))
                    if timeout < 1:
                        await channel.send('You both did not answer multiple times... timing out.')
                        return

            footnote = 'Players drawed the {} round.'.format(config.ORDINAL(round_ind))

        # if there is a clear winner
        else:
            winner = answers[1]
            await players[winner].dm_channel.send(create_reply(user, False, config))
            await players[not winner].dm_channel.send(create_reply(user, True, config))
            footnote = '{} won the {} round!'.format(players[winner].display_name, config.ORDINAL(round_ind))
            score[winner] += 1

        # update score embed
        content = '```\n{0}: {2}\n{1}: {3}```'\
              .format(players[0].display_name.ljust(max_char+1),
                      players[1].display_name.ljust(max_char+1),
                      score[0], score[1])

        new_score = create_embed(title='LotR Battle Score',
                                 color=(255, 0, 0),
                                 content=content,
                                 footnote=footnote)
        await score_msg.edit(embed=new_score)

        # exit condition
        if abs(score[0]-score[1]) > 1 and score[0]+score[1] > 2:
            winner = (players[0] if score[0] > score[1] else players[1])
            await channel.send('Congratulations, {} You won the game!\n'.format(winner.mention))
            return


async def display_help(channel, config):
    '''
    displays the help message for the usage of the LotR-Trivia-Bot spcififed in the config
    '''
    embed = create_embed(title='LotR Trivia Bot help',
                         content=config.DISCORD_CONFIG['help.text'],
                         footnote=config.DISCORD_CONFIG['help.footer'])
    await channel.send(embed=embed)


def map_vals(val, in_min, in_max, out_min, out_max):
    '''
    maps a value in a range to another range
    '''
    val = min(max(val, in_min), in_max)
    return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def create_embed(title=False, content=False, embed_url=False, link_url=False,
                 footnote=False, color=False, author_info=False):
    '''
    creates an Discord Embed with title, content, footer, etc.
    '''
    if title:
        embed = discord.Embed(title=title)
    else:
        embed = discord.Embed()
    if color:
        embed.color = discord.Color.from_rgb(
            int(color[0]),
            int(color[1]),
            int(color[2]))
    else:
        embed.color = discord.Color.from_rgb(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255))

    if author_info:
        author_name, avatar_url = author_info
        embed.set_author(name=author_name, icon_url=avatar_url)

    if footnote:
        embed.set_footer(text=footnote)

    if content:
        embed.description = content

    if embed_url:
        embed.url = embed_url
    if link_url:
        if link_url.split('.').pop().strip() in ['jpg', 'jpeg', 'gif', 'png']:
            embed.set_image(url=link_url)
    return embed


def create_hangman_embed(user, word, state, ind, used_chars, ongoing):
    '''
    creates Hangman embed
    '''

    hangman = ''
    for char in word:
        if char == ' ':
            hangman += '  '
            continue
        if not char.isalpha():
            hangman += char + ' '
        elif char.lower() in used_chars or not ongoing:
            hangman += '__{}__ '.format(char)
        else:
            hangman += r'\_ '
    hangman = hangman.strip()

    if used_chars:
        used = 'Used letters:\n '
        for char in used_chars:
            used += ':regional_indicator_{}: '.format(char)
        used = used.strip()
    else:
        used = ''

    author_info = ('{}\'s hangman game'.format(user.display_name), user.avatar_url)

    color = (map_vals(ind, 0, 8, 0, 255),
             map_vals(ind, 0, 8, 255, 0), 0)

    return create_embed(hangman,
                        author_info=author_info,
                        content=used + state,
                        color=color)


def create_reply(user, insult, config):
    '''
    creates a reply to an user, insult or compliment
    '''
    if insult:
        msg = ':x: ' + random.choice(config.DISCORD_CONFIG['insults'])
    else:
        msg = ':white_check_mark: ' + random.choice(config.DISCORD_CONFIG['compliments'])
    return msg if '{}' not in msg else msg.format(user.display_name)


def parse_script(config, arr, condensed_arr):
    '''
    reads LOTR script to array.
    Also outputs a condensed version for faster searching.
    '''
    with open(config.DISCORD_CONFIG['script.path'], 'r') as script:
        temp = ''
        last = ''
        for line in script:
            line = line.strip()

            if not line and temp:
                arr.append(temp)
                temp = ''
            else:
                temp += line
                if last:
                    temp += ' '
                if not last and line != 'STOP':
                    temp += '|'

            last = line

    for line in arr:
        if line.startswith('STOP'):
            condensed_arr.append('STOP')
            continue

        line = line.lower().split('|', 1)[1]
        punctuation_found = False
        temp_arr = []

        for char in line:
            if char in config.DISCORD_CONFIG['autoscript.elimination_chars']:
                continue
            if char in config.DISCORD_CONFIG['autoscript.punctuation_chars']:
                punctuation_found = True
            elif punctuation_found:
                punctuation_found = False
                temp_arr.append(temp.strip())
                temp = ''
            temp += char
        condensed_arr.append(temp_arr)


async def find_similar_from_script(channel, message, condensed_arr, script, settings, config):
    '''
    attempts to find similar line from script and formats it, if found.
    '''
    if not feature_allowed('autoscript', channel, settings, config):
        return

    # format message string
    content = message.content.lower().strip()

    # stop if the message is shorter than 2 words
    if len(content.split(' ')) < 2:
        return

    for char in PUNCTUATION_CHARS:
        content = content.replace(char, '.')
    for char in ELIMINATION_CHARS:
        content = content.replace(char, '')
    content = content.split('.')

    # searching condensed script for matching line
    log = {}

    # search the script for each sentence in the message individually
    for msg_part in content:
        msg_part = msg_part.strip()

        if not msg_part:
            continue

        # iterate through lines
        for line_ind, line in enumerate(condensed_arr):

            # abort conditions
            if not line:
                continue
            if isinstance(line, str):
                if line == 'STOP':
                    continue

            # iterate through sentences in the line
            for part_ind, part in enumerate(line):
                # get the matching ratio
                ratio = SequenceMatcher(None, part, msg_part).ratio()
                if ratio > 0.8:
                    # if line has already been found
                    if line_ind in log.keys():
                        num, found_conf, highest_part_ind = log[line_ind]
                        log[line_ind] = (num+1, # found-parts
                                         round((found_conf*num+ratio)/num+1, 2), # conf
                                         max(highest_part_ind, part_ind)) # part-ind

                    # if line was not yet found, only add it if the sentence is longer than
                    # one word. This prevents the bot from reacting to very short sentences.
                    elif len(msg_part.split(' ')) > 1:
                        log[line_ind] = (1, round(ratio, 2), part_ind)

    if log:
        # sort results by found parts
        ranking = sorted(log, key=lambda x: log[x][0])[::-1]

        # filter the results that have the same amount of found parts as the top one
        filtered_dict = dict(filter(lambda item: item[1][0] == log[ranking[0]][0], log.items()))

        # sort these by the confidence
        filtered_ranking = sorted(filtered_dict, key=lambda x: filtered_dict[x][1])[::-1]

        # pick the top one
        line_ind = filtered_ranking[0]
        part_ind = log[line_ind][2]

        parts = []
        punctuation_found = False

        # get the 'real' line from the script by taking
        # the index of the line in the condensed array
        author, line = script[line_ind].split('|')
        temp = ''

        # try to split the uncondensed sentence by punctuations
        # to find the starting point for autoscript
        for char in line:
            if char in PUNCTUATION_CHARS:
                punctuation_found = True
            elif punctuation_found:
                punctuation_found = False
                parts.append(temp.strip())
                temp = ''
            temp += char
        if temp.strip():
            parts[-1] += temp

        # if there is something after this line, print it
        if part_ind < len(parts)-1 or line_ind < len(script)-1:
            return_text = ''
            # if there is a part of the line that is missing, complete it
            if part_ind < len(parts)-1:
                temp = ''
                for part in parts[part_ind+1:]:
                    temp += part+' '
                return_text += '**{}:** ... {}\n'.format(author.title(), temp)

            # if the line is not the last one of the script, add the next one
            if line_ind < len(script)-1:
                if script[line_ind+1] != 'STOP':
                    author, text = script[line_ind+1].split('|')
                    return_text += '**{}:** {}\n'.format(author.title(), text)

                # if a scene STOP is before the next line,
                # continue only if configured to do so.
                elif not config.DISCORD_CONFIG['autoscript.scene_end_interrupt'] \
                     and line_ind < len(script)-2:
                    return_text += '**`[NEXT SCENE]`**\n'
                    author, text = script[line_ind+2].split('|')
                    return_text += '**{}:** {}'.format(author.title(), text)

            if channel.permissions_for(channel.guild.me).add_reactions:
                await message.add_reaction('✅')
            await channel.send(return_text.strip())


async def reddit_meme(channel, reddit_client, subreddit, config, settings):
    '''
    outputs a reddit meme from LOTR subreddit
    '''

    if not feature_allowed('memes', channel, settings, config):
        return

    ch_id = channel.id if isinstance(channel, discord.channel.DMChannel) else channel.guild.id

    submission = reddit_client.get_meme(ch_id, subreddit)
    post_url = 'https://reddit.com/'+submission.id
    footnote = 'This meme is certified to be {}% dank'.format(submission.upvote_ratio*100)

    parent = reddit_client.get_crosspost_parent(submission)
    if parent:
        submission = parent

    if submission.is_self: # is text-only
        text = submission.selftext
        if len(text) > 2000:
            text = text[:2000]
            text += '...'
        return create_embed(
            submission.title,
            embed_url=post_url,
            content=text,
            footnote=footnote)

    # has embedded media
    embed = create_embed(title=(':repeat: Crosspost: ' if parent else '') + submission.title,
                         embed_url=post_url,
                         link_url=submission.url,
                         footnote=footnote)
    await channel.send(embed=embed)


async def silmarillion_quote(channel, settings, config):
    '''
    outputs random quote from the Silmarillion with chapter and heading.
    '''

    if not feature_allowed('squote', channel, settings, config):
        return

    out = ''
    with open(config.DISCORD_CONFIG['silmarillion.path'], 'r') as silmarillion_file:
        silmarillion = silmarillion_file.readlines()
        max_ind = len(silmarillion)-1
        index = random.randint(0, max_ind)
        ind_limit = min(max_ind, index+config.DISCORD_CONFIG['silmarillion.sentence_count']+1)
        for i in range(index, ind_limit):
            if is_headline(silmarillion[i]):
                break
            out += silmarillion[i].strip()+' '

        # attempt to find title
        for i in range(index-1, -1, -1):
            line = silmarillion[i].strip()
            if is_headline(line) and i > 0:
                previous_line = silmarillion[i-1].strip()
                if line and is_headline(previous_line):
                    title = '**'+previous_line+'**:\n'+line.lower()
                else:
                    title = '**'+line+'**'
                break

    await channel.create_embed(title, content=out)


def is_headline(line):
    '''
    checks whether line from Silmarillion is headline
    '''
    allowed_chars = string.ascii_uppercase + string.digits + ' ' + '-'
    for char in line:
        if char not in allowed_chars:
            return False
    return True


async def search_youtube(channel, user, raw_content, google_client, config, settings):
    '''
    returns a give number of Youtube Video embeds for a specific channel
    '''
    if not feature_allowed('yt-search', channel, settings, config):
        return

    raw_content = raw_content.split(config.GENERAL_CONFIG['key'] + ' yt ')[1]
    start, end = (-1, -1)
    query = ''

    start = raw_content.find('"')
    if start != -1:
        end = raw_content.find('"', start + 1)
        if end != -1:
            query = raw_content[start+1:end]
            if raw_content[:start].strip().isdigit():
                num = max(1, int(raw_content[:start].strip()))
            elif raw_content[end+1:].strip().isdigit():
                num = max(1, int(raw_content[end+1:].strip()))
            else:
                num = 1

    if not query:
        return create_reply(user, True, config) + '\nTry providing a query next time!\n\
The correct syntax is: `{0} yt "<keywords>" \n(you can also provide a video count, \
before or after the query)`\n'.format(config.GENERAL_CONFIG['key'])

    res = google_client.get_video_from_channel(
        config.YT_CONFIG['channel_id'],
        query,
        min(config.YT_CONFIG['max_video_count'], num))['items']

    if not res:
        await channel.send('*\'I have no memory of this place\'* ~Gandalf\nYour query `{}` yielded no results!'.format(query))

    for i, item in enumerate(res):
        title = ':mag: Search Result {}\n'.format(i+1)+unescape(item['snippet']['title'])
        yt_link = 'https://www.youtube.com/watch?v='+item['id']['videoId']
        thumbnail_link = item['snippet']['thumbnails']['medium']['url']
        publish_time = 'Published at: ' + '/'.join(
            item['snippet']['publishedAt'][:10].split('-')[::-1])
        # Video API call for every vid
        vid_info = google_client.get_video_info(item['id']['videoId'])['items'][0]
        description = unbloat_description(vid_info['snippet']['description'])
        views = '{:,}'.format(int(vid_info['statistics']['viewCount']))
        likes = int(vid_info['statistics']['likeCount'])
        comments = '{:,}'.format(int(vid_info['statistics']['commentCount']))
        info_bar = ':play_pause: {views} **|** :thumbsup: {likes} **|** :speech_balloon: {comm}'\
            .format(views=views, likes='{:,}'.format(likes), comm=comments)
        await channel.send(embed=create_embed(title,
                                              embed_url=yt_link,
                                              link_url=thumbnail_link,
                                              footnote=publish_time,
                                              content=description+'\n'+info_bar))


def unbloat_description(desc):
    '''
    strips yt descriptions down to the bare minimum
    '''
    desc = desc.split('\n')
    new_desc = ''
    for i, line in enumerate(desc):
        blacklisted = False
        line = line.strip().lower()
        if not line:
            continue

        for item in DESCRIPTION_BLACKLIST:
            if item in line:
                blacklisted = True
                break

        if blacklisted:
            continue
        new_desc += desc[i].strip()+'\n'
    return new_desc


async def lotr_search(channel, google_client, raw_content, config):
    '''
    searches on a given site for a given entry
    '''
    query = ' '.join(raw_content.split(' ')[2:]).strip()
    site = config.GOOGLE_CONFIG['site']
    content = list(google_client.google_search(query, site))
    if not content:
        await channel.send(':x: No results for `{}` on  *{}*.'.format(query, site))
        return
    content = content[0]
    title = ':mag: 1st result for `{}` on  *{}* :'.format(query, site)
    await channel.send(embed=create_embed(title=title, content=content))


def feature_allowed(feature, channel, settings, config):
    '''
    checks the settings whether the feature is allowed in this channel
    '''
    if isinstance(channel, discord.channel.DMChannel):
        return 1
    server = channel.guild
    if channel.id in settings.keys():
        if feature in settings[channel.id]:
            return settings[channel.id][feature]
    if server.id in settings.keys():
        if feature in settings[server.id]:
            return settings[server.id][feature]
    if feature in config.DISCORD_CONFIG['settings.defaults'].keys():
        return config.DISCORD_CONFIG['settings.defaults'][feature]
    return 1


async def edit_settings(cmd, settings, channel):
    '''
    edits the settings for the server or channel based on the given command
    '''
    if cmd[1] == 'on' or cmd[1] == 'off' or cmd[1] == 'unset':
        channel = channel.id
        if not channel in settings.keys():
            settings[channel] = {}

        if cmd[1] == 'on':
            settings[channel][cmd[0]] = 1
            await channel.send('feature `{}` for this channel was turned **on**'.format(cmd[0]))
        elif cmd[1] == 'off':
            settings[channel][cmd[0]] = 0
            await channel.send('feature `{}` for this channel was turned **off**'.format(cmd[0]))
        elif cmd[1] == 'unset':
            if cmd[0] in settings[channel].keys():
                del settings[channel][cmd[0]]
                await channel.send('feature `{}` for this channel was **unset**'.format(cmd[0]))
            await channel.send('feature `{}` for this channel was not yet set'.format(cmd[0]))


    elif cmd[1] == 'server-on' or cmd[1] == 'server-off' or cmd[1] == 'server-unset':
        server = channel.guild.id
        if not server in settings.keys():
            settings[server] = {}

        if cmd[1] == 'server-on':
            settings[server][cmd[0]] = 1
            await channel.send('feature `{}` for this server was turned **on**'.format(cmd[0]))
        elif cmd[1] == 'server-off':
            settings[server][cmd[0]] = 0
            await channel.send('feature `{}` for this server was turned **off**'.format(cmd[0]))
        elif cmd[1] == 'server-unset':
            if cmd[0] in settings[server].keys():
                del settings[server][cmd[0]]
                await channel.send('feature `{}` for this server was **unset**'.format(cmd[0]))
            await channel.send('feature `{}` for this server was not yet set'.format(cmd[0]))
    else:
        await channel.send('state `{}` not recognized'.format(cmd[1]))
