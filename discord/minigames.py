"""
The LotR-Bot discord integration. This is the main class for the bot.
"""
import random
import csv
import string
from difflib import SequenceMatcher

import discord

PUNCTUATION_CHARS = ["?", "!", ".", ":", ";"]
IMAGE_EXT = ["jpg", "jpeg", "gif", "png"]
ELIMINATION_CHARS = ["'", ","]


def constrain_val(val, in_min, in_max):
    """
    constrains a value in a range
    """
    return min(max(val, in_min), in_max)


def map_vals(val, in_min, in_max, out_min, out_max):
    """
    maps a value in a range to another range
    """
    val = constrain_val(val, in_min, in_max)
    return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


# algorithm R(3.4.2) (Waterman's "Reservoir Algorithm")
def random_line(afile):
    """
    returns a random element from an enumerator
    """
    line = next(afile)
    for num, aline in enumerate(afile, 2):
        if random.randrange(num):
            continue
        line = aline
    return line


def match_sequences(str_a, str_b):
    """
    returns the match-ratio of two strings (a and b)
    """
    return SequenceMatcher(None, str_a, str_b).ratio()


def create_embed(title, content=False, embed_url=False, link_url=False,
                 footnote=False, color=False, author_info=False):
    """
    creates an Discord Embed with title, content, footer, etc.
    """

    embed = discord.Embed(title=title)
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
        if link_url.split(".").pop().strip() in IMAGE_EXT:
            embed.set_image(url=link_url)
    return embed


def create_trivia_profile(user, scoreboard, config):
    """
    create trivia scoreboard embed for a certain user
    """
    played, wins = scoreboard[user.id]
    color = (map_vals(wins/played, 0, 1, 255, 0),
             map_vals(wins/played, 0, 1, 0, 255), 0)
    author_name = "{}'s results for their trials in the Art\
of Middle Earth trivia".format(user.display_name)

    title = "{}'s results".format(user.display_name)
    content = "Trivia games played: {}\nTrivia games won: {}\n\
               Win/Played ratio: {}%"\
              .format(played, wins, round(wins/played*100, 2))
    author_info = (author_name, user.avatar_url)
    return create_embed(title, author_info=author_info, content=content,
                        color=color, footnote=config.FOOTER)


def create_hangman_embed(user, game_info, game_status, config):
    """
    creates Hangman embed
    """
    word, _, steps, used_chars, state_ind = game_info
    hangman = ""
    for split_word in word.split(" "):
        for char in split_word:
            if char.lower() in used_chars or game_status != 0:
                hangman += "__{}__ ".format(char)
            else:
                hangman += r'\_ '
        hangman += "  "
    hangman = hangman.strip()

    used = "Used letters:\n "
    if used_chars:
        for char in used_chars:
            used += ":regional_indicator_{}: ".format(char)
        used = used.strip()

    if game_status == 0:  # GAME ONGOING STATUS
        content = config.STATES[state_ind]+used
        lives = (7-state_ind)//steps
    elif game_status == -1:  # GAME LOST STATUS
        content = config.STATES[-2]+used+"\nGame over! You lost."
        lives = 0
    elif game_status == 1:  # GAME WON STATUS
        content = config.STATES[-1]+used+"\nGame over! You won!"
        lives = (7-state_ind)//steps

    author_info = (user.display_name+"'s hangman game ({} lives left)"
                   .format(lives), user.avatar_url)

    color = (map_vals(state_ind, 0, 8, 0, 255),
             map_vals(state_ind, 0, 7, 255, 0), 0)

    return create_embed(hangman, author_info=author_info, content=content,
                        color=color, footnote=config.FOOTER)


def create_reply(user, insult, config):
    """
    creates a reply to an user, insult or compliment
    """
    if insult:
        msg = random.choice(config.INSULTS)
    else:
        msg = random.choice(config.COMPLIMENTS)
    return msg if "{}" not in msg else msg.format(user.display_name)


def create_trivia_question(user, scoreboard, config):
    """
    returns an embed with a trivia question for a specific user AND the
    correct index
    """

    # get info from scoreboard
    if user.id in scoreboard.keys():
        count = scoreboard[user.id][0] + 1
    else:
        count = 1

    author_name = "{}'s {} trial in the Arts of Middle Earth trivia"\
        .format(user.display_name, config.ORDINAL(count))

    # get random question
    with open("questions.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        content = random.choice(list(csvreader))

    # pop the source and the question (first element)
    source = content.pop(0)
    question = content.pop(0)
    # shuffle answers
    random.shuffle(content)

    answers = content.copy()
    correct_index = 0
    for i, item in enumerate(answers):
        if item.startswith(config.MARKER):
            answers[i] = item[1:]
            correct_index = i+1
            break

    title = question
    embed_text = "```markdown\n"
    for num, cont in enumerate(answers):
        embed_text += "{}. {}\n".format(num+1, cont)
    embed_text += "```\nsource: {}".format(source)
    # returning the embed and the answers WITH THE CORRECT ANSWER,
    # so that the given answer can be validated later
    author_info = (author_name, user.avatar_url)
    embed = create_embed(title, author_info=author_info,
                         content=embed_text, footnote=config.FOOTER)
    return (embed, correct_index, len(answers))


def create_trivia_reply(user, msg, scoreboard, correct_index,
                        len_answers, config):
    """
    creates an appropiate reply to a trivia question.\
    Changes scoreboard according to outcome.
    """
    if not msg:
        return create_reply(user, True, config) +\
                            "\nYou took too long to answer!"

    if user.id in scoreboard.keys():
        count, wins = scoreboard[user.id]
    else:
        count, wins = (0, 0)
    msg = msg.content
    ret_string = ""
    if msg.isdigit():
        # if msg is a digit
        msg = int(msg)
        if msg > 0 and msg <= len_answers:
            if msg == correct_index:
                # right answer
                wins += 1
                ret_string = create_reply(user, False, config)
            else:
                # invalid digit
                ret_string = create_reply(user, True, config)
        else:
            # invalid digit
            ret_string = create_reply(user, True, config) + \
                "\nHmm... maybe try picking a valid digit next time ?"
    else:
        # not a digit
        ret_string = create_reply(user, True, config) + \
            "\nWhat is that supposed to be? Clearly not a digit..."

    scoreboard[user.id] = (count+1, wins)
    return ret_string


def initiate_hangman_game(user, config):
    """
    creates a hangman game
    returns the following tuple:
    (embed, word, word_condensed, steps)
    """
    used_chars = []
    state_ind = 0
    # import words for hangman
    with open("words.csv", "r") as csvfile:
        word = random.choice(list(csv.reader(csvfile, delimiter=',', quotechar='"'))[0])
    word_condensed = word.lower().replace(" ", "")

    if len(word_condensed) <= 6:
        steps = 2
    else:
        steps = 1

    game_info = (word, word_condensed, steps, used_chars, state_ind)
    return (create_hangman_embed(user, game_info, 0, config), game_info)


def update_hangman_game(user, msg, game_info, config):
    """
    updates the hangman game and returns info about whether the\
    game is finished
    """
    word, word_condensed, steps, used_chars, state_ind = game_info

    if not msg:
        ret_str = "Game over! You took too long to answer!"
        ret_break = True
        ret_embed = create_hangman_embed(user, game_info, -1, config)
        return (ret_embed, ret_break, ret_str, game_info)

    msg = msg.content.lower()

    for char in msg:
        if char not in used_chars and char.isalpha():
            used_chars.append(char)
            if char not in word_condensed:
                state_ind += steps

    used_chars.sort()

    game_info = (word, word_condensed, steps, used_chars, state_ind)

    if state_ind >= 7:
        ret_embed = create_hangman_embed(user, game_info, -1, config)
        ret_str = "Game over! You lost all your lives!"
        ret_break = True
        return (ret_embed, ret_break, ret_str, game_info)

    all_chars_found = True
    for char in word_condensed:
        if char not in used_chars:
            all_chars_found = False

    if all_chars_found:
        ret_embed = create_hangman_embed(user, game_info, 1, config)
        ret_str = "Congratulations! You won the game!"
        ret_break = True
        return (ret_embed, ret_break, ret_str, game_info)

    ret_embed = create_hangman_embed(user, game_info, 0, config)
    ret_str = ""
    ret_break = False
    return (ret_embed, ret_break, ret_str, game_info)


def parse_script(file, arr, condensed_arr):
    """
    reads LOTR script to array.
    Also outputs a condensed version for faster searching.
    """
    with open(file, "r") as script:
        temp = ""
        last = ""
        for line in script:
            line = line.strip()

            if not line and temp:
                arr.append(temp)
                temp = ""
            else:
                temp += line
                if last:
                    temp += " "
                if not last and line != "STOP":
                    temp += "|"

            last = line

    for line in arr:
        if line.startswith("STOP"):
            condensed_arr.append("STOP")
            continue

        line = line.lower().split('|', 1)[1]
        punctuation_found = False
        temp_arr = []

        for char in line:
            if char in ELIMINATION_CHARS:
                continue
            if char in PUNCTUATION_CHARS:
                punctuation_found = True
            elif punctuation_found:
                punctuation_found = False
                temp_arr.append(temp.strip())
                temp = ""
            temp += char
        condensed_arr.append(temp_arr)


def find_similar_from_script(msg, condensed_arr, script):
    """
    attempts to find similar line from script and formats it, if found.
    """
    # format message string
    msg = msg.lower()
    for char in PUNCTUATION_CHARS:
        msg = msg.replace(char, ".")
    for char in ELIMINATION_CHARS:
        msg = msg.replace(char, "")

    msg = msg.split(".")

    found_parts = {}
    for msg_part in msg:
        for line_ind, line in enumerate(condensed_arr):
            # abort conditions
            if not line:
                continue
            if isinstance(line, str):
                if line == "STOP":
                    continue

            for part_ind, part in enumerate(line):
                ratio = match_sequences(part, msg_part)
                if ratio > 0.85:
                    if line_ind in found_parts.keys():
                        if found_parts[line_ind][0] < part_ind:
                            found_parts[line_ind] = \
                                (part_ind, max(found_parts[line_ind][1], ratio))
                    else:
                        found_parts[line_ind] = (part_ind, ratio)

    if found_parts.keys():
        max_confidence = 0
        ind = -1
        for key, entry in found_parts.items():
            if entry[1] > max_confidence:
                max_confidence = entry[1]
                ind = key

        if ind < 0:
            return []
        return_texts = []
        part_ind = found_parts[ind][0]
        parts = []
        punctuation_found = False
        author, line = script[ind].split("|")
        temp = ""
        for char in line:
            if char in PUNCTUATION_CHARS:
                punctuation_found = True
            elif punctuation_found:
                punctuation_found = False
                parts.append(temp.strip())
                temp = ""
            temp += char

        if part_ind < len(parts)-1:
            temp = ""
            for part in parts[part_ind+1:]:
                temp += part+" "
            return_texts.append("**{}**: ... {}".format(author.title(), temp))

        if ind < len(script)-1:
            if script[ind+1] != "STOP":
                author, text = script[ind+1].split("|")
            return_texts.append("**{}:** {}".format(author.title(), text))

        return return_texts


def reddit_meme(message, reddit_client):
    """
    outputs a reddit meme from LOTR subreddit
    """
    server = message.channel.guild
    submission = reddit_client.get_meme(server, "lotrmemes")
    post_url = "https://reddit.com/"+submission.id
    footnote = "This meme is certified to be {}% dank".format(submission.upvote_ratio*100)
    if submission.is_self:
        return create_embed(submission.title, embed_url=post_url, content=submission.self(), footnote=footnote)
    return create_embed(submission.title, embed_url=post_url, link_url=submission.url, footnote=footnote)


def silmarillion_quote(config):
    """
    outputs random quote from the Silmarillion with chapter and heading.
    """
    out = ""
    with open(config.SILMARILLION_LOC, "r") as silmarillion_file:
        silmarillion = silmarillion_file.readlines()
        max_ind = len(silmarillion)-1
        index = random.randint(0, max_ind)
        for i in range(index, min(max_ind, index+config.SILMARILLION_SENTENCES_COUNT+1)):
            if is_headline(silmarillion[i]):
                break
            out += silmarillion[i].strip()+" "

        # attempt to find title
        for i in range(index-1, -1, -1):
            line = silmarillion[i].strip()
            if is_headline(line) and i > 0:
                previous_line = silmarillion[i-1].strip()
                if line and is_headline(previous_line):
                    title = "**"+previous_line+"**:\n"+line.lower()
                else:
                    title = "**"+line+"**"
                break

    return create_embed(title, content=out)


def is_headline(line):
    """
    checks whether line from Silmarillion is headline
    """
    allowed_chars = string.ascii_uppercase + string.digits + " " + "-"
    for char in line:
        if char not in allowed_chars:
            return False
    return True
