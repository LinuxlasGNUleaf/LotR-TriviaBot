"""
The LotR-Bot discord integration. This is the main class for the bot.
"""
import random
import discord

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

def create_embed(title, author_name, avatar_url, content, color, footnote):
    """
    creates an Discord Embed with title, content, footer, etc.
    """
    embed = discord.Embed(color=discord.Color.from_rgb(
        int(color[0]),
        int(color[1]),
        int(color[2])),
                          title=title)
    embed.set_author(name=author_name, icon_url=avatar_url)
    embed.set_footer(text=footnote)
    embed.description = content
    return embed

def create_trivia_profile(user, scoreboard, config):
    """
    create trivia scoreboard embed for a certain user
    """
    played, wins = scoreboard[user.id]
    color = (map_vals(wins/played, 0, 1, 255, 0), map_vals(wins/played, 0, 1, 0, 255), 0)
    author_name = "{}'s results for their trials in the Art of Middle Earth trivia"\
                  .format(user.display_name)
    icon_url = user.avatar_url
    title = "{}'s results".format(user.display_name)
    content = "Trivia games played: {}\nTrivia games won: {}\nWin/Played ratio: {}%"\
              .format(played, wins, round(wins/played*100, 2))
    return create_embed(title, author_name, icon_url, content, color, config.FOOTER)

def create_hangman_embed(user, game_info, game_status, config):
    """
    creates Hangman embed
    """
    word, _, steps, used_chars, state_ind = game_info
    color = (map_vals(state_ind, 0, 8, 0, 255), map_vals(state_ind, 0, 7, 255, 0), 0)
    hangman = ""
    for split_word in word.split(" "):
        for char in split_word:
            if char.lower() in used_chars or game_status != 0:
                hangman += "__{}__ ".format(char)
            else:
                hangman += '\_ '
        hangman += "  "
    hangman = hangman.strip()

    used = "Used letters:\n "
    if used_chars:
        for char in used_chars:
            used += ":regional_indicator_{}: ".format(char)
        used = used.strip()

    if game_status == 0: # GAME ONGOING STATUS
        content = config.STATES[state_ind]+used
        lives = (7-state_ind)//steps
    elif game_status == -1: # GAME LOST STATUS
        content = config.STATES[-2]+used+"\nGame over! You lost."
        lives = 0
    elif game_status == 1: # GAME WON STATUS
        content = config.STATES[-1]+used+"\nGame over! You won!"
        lives = (7-state_ind)//steps

    return create_embed(hangman, user.display_name+"'s hangman game ({} lives left)"\
    .format(lives), user.avatar_url, content, color, config.FOOTER)

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

    # config variables for the embed
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    icon_url = user.avatar_url

    #get info from scoreboard
    if user.id in scoreboard.keys():
        count = scoreboard[user.id][0] + 1
    else:
        count = 1

    author_name = "{}'s {} trial in the Arts of Middle Earth trivia"\
                .format(user.display_name, config.ORDINAL(count))

    # get random question
    with open("questions.csv", "r") as csvfile:
        content = random_line(csvfile).strip().split('"')[1:-1]
        while "," in content[::-1]:
            content.remove(",")

    # pop the source and the question (first element)
    source = content.pop(0)
    question = content.pop(0)
    # shuffle answers
    random.shuffle(content)
    # create_question(user, count, question, content.copy())

    answers = content.copy()
    correct_index = 0
    for num in range(len(answers)):
        if answers[num].startswith(config.MARKER):
            answers[num] = answers[num][1:]
            correct_index = num+1

    title = question
    embed_text = "```markdown"
    for num, cont in enumerate(answers):
        embed_text += "    {}) {}\n".format(num+1, cont)
    embed_text += "```\nsource: {}".format(source)
    # returning the embed and the answers WITH THE CORRECT ANSWER,
    # so that the given answer can be validated later
    return (create_embed(title, author_name, icon_url, embed_text, color, config.FOOTER), correct_index, len(answers))

def create_trivia_reply(user, msg, scoreboard, correct_index, len_answers, config):
    """
    creates an appropiate reply to a trivia question. changes scoreboard according to outcome.
    """
    if not msg:
        return create_reply(user, True, config)+"\nYou took too long to answer!"

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
        word = random.choice(csvfile.readline().strip().split(','))[1:-1]
    word_condensed = word.lower().replace(" ", "")


    if len(word_condensed) <= 6:
        steps = 2
    else:
        steps = 1

    game_info = (word, word_condensed, steps, used_chars, state_ind)
    return (create_hangman_embed(user, game_info, 0, config), game_info)

def update_hangman_game(user, msg, game_info, config):
    """
    updates the hangman game and returns info about whether the game is finished
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
