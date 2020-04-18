# coding=utf-8
# imports
import discord
import random
import pickle
import asyncio.exceptions

# aquire token from file
with open("/home/jakobw/.config/discord/bots/lotr-bot/token.tk","r") as tokenfile:
    token = tokenfile.readline().strip()

# some lambda code stolen from Gareth on codegolf to create ordinals:
ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

# crappy ASCII art for hangman game
states = [
"``` \n \n \n \n \nililililillllililii```",
"```    //\n    ||\n    ||\n    ||\n    ||    \nililililillllililii```",
"```    //====\\\n    ||\n    ||\n    ||\n    ||\n    ||\nililililillllililii```",
"```    //====\\\n    ||    |\n    ||   (\")\n    ||\n    ||\n    ||\nililililillllililii```",
"```    //====\\\n    ||    |\n    ||   (\")\n    ||   \\|\n    ||\n    ||\nililililillllililii```",
"```    //====\\\n    ||    |\n    ||   (\")\n    ||   \\|/\n    ||    X\n    ||\n    ||\nililililillllililii```",
"```    //====\\\n    ||    |\n    ||   (\")\n    ||   \\|/\n    ||    X\n    ||   /\n    ||\nililililillllililii```",
"```    //====\\\n    ||    |\n    ||   (\")\n    ||   \\|/\n    ||    X\n    ||   / \\\n    ||\nililililillllililii```",
"```    //====\\\n    ||\n    ||\n    ||   (\")\n    ||   \\|/\n    ||    X\n    ||   / \\\nililililillllililii```"]

alpha = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']

# ==========================> CONFIG <==================================
marker = '*'
key = "lotr"

footer = "A discord bot written in Python by JaWs"

insults = ["Stupid fat {}! ~Smeagol","Fool of a {}! ~Gandalf","I would cut off your head {}... if it stood but a little higher from the ground. ~Éomer",
"Dotard! What is the house of {} but a thatched barn where brigands drink in the reek, and their brats roll on the floor among the dogs? ~Saruman",
"Hey, {}! Don't go getting too far behind. ~Sam","Feanor gave up because of your stupidity, {}!"]

compliments = ["Well done, my dear {}!","{}, you should be counted amongst the wise of middleearth.","Very good {}, I could not have done it better myself!"]

scoreboard = {}
blocked = [] #temporarily blocked users (cannot issue commands)

def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# algorithm R(3.4.2) (Waterman's "Reservoir Algorithm")
def random_line(afile):
    line = next(afile)
    for num, aline in enumerate(afile, 2):
      if random.randrange(num): continue
      line = aline
    return line

def createEmbed(title,author_name,avatar_url,content,color,footnote):
    embed = discord.Embed(color=discord.Color.from_rgb(int(color[0]),int(color[1]),int(color[2])))
    embed.set_author(name=author_name, icon_url=avatar_url)
    embed.title = title
    embed.set_footer(text=footnote)
    embed.description = content
    return embed

def createQuestion(user,num,question,answers):
    # random color
    for i in range(len(answers)):
        if answers[i].startswith("*"):
            answers[i] = answers[i][1:]
    color = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
    author_name = "{}'s {} trial in the Arts of Middle Earth trivia".format(user.display_name,ordinal(num))
    icon_url = user.avatar_url
    title = question
    content = ""
    for i in range(0,len(answers)):
        content += "    {}) {}\n".format(i+1,answers[i])

    return createEmbed(title,author_name,icon_url,content,color,footer)

def createProfile(user):
    played,wins = scoreboard[user.id]
    color = (map(wins/played,0,1,255,0),map(wins/played,0,1,0,255),0)
    author_name = "{}'s results for their trials in the Art of Middle Earth trivia".format(user.display_name)
    icon_url = user.avatar_url
    title = "{}'s results".format(user.display_name)
    content = "Trivia games played: {}\nTrivia games won: {}\nWin/Played ratio: {}%".format(played,wins,round(wins/played*100,2))
    return createEmbed(title,author_name,icon_url,content,color,footer)

def createHangman(user,word,state_ind,steps,used_chars,game_status):
    color = (map(state_ind,0,8,0,255),map(state_ind,0,7,255,0),0)
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
    
    if game_status == 0:
        content = states[state_ind]+used
        lives = (7-state_ind)//steps
    elif game_status == -1:
        content = states[-2]+used+"\nGame over! You lost."
        lives = 0
    elif game_status == 1:
        content = states[-1]+used+"\nGame over! You won!"
        lives = (7-state_ind)//steps

    return createEmbed(hangman,user.display_name+"'s hangman game ({} lives left)".format(lives),user.avatar_url,content,color,footer)

def createReply(user,insult=True):
    msg = insults[random.randint(0,len(insults)-1)] if insult else compliments[random.randint(0,len(compliments)-1)]
    return msg if "{}" not in msg else msg.format(user.display_name)

class MyClient(discord.Client):

    async def on_ready(self):
        print("PreInit...")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Boromir die"))
        print("online. All systems operational.")

    async def on_message(self, message):
        user = message.author
        content = message.content.lower()
        channel = message.channel

        if user == client.user or user in blocked:
            return


        if content == key+" trivia":

            #get info from scoreboard
            if user.id in scoreboard.keys():
                count,wins = scoreboard[user.id]
                count += 1
            else:
                count,wins = (1,0)
            
            # get random question
            with open("questions.csv","r") as csvfile:
                content = random_line(csvfile).strip().split('"')[1:-1]
                while "," in content[::-1]:
                    content.remove(",")
            # pop the question (first element)
            question = content.pop(0)
            # shuffle answers
            random.shuffle(content)            

            # send the question message
            await channel.send(embed=createQuestion(user,count,question,content.copy()))

            def check(m):
                return m.author == user and m.channel == channel

            blocked.append(user.id)
            try:
                msg = await client.wait_for('message',check=check,timeout=15)
            except asyncio.TimeoutError:
                await channel.send(createReply(user,insult=True)+"\nYou took too long to answer!")
                return

            blocked.remove(user.id)
            msg = msg.content
            if msg.isdigit(): 
                # if msg is a digit
                msg = int(msg)-1
                if msg in range(len(content)):
                    if content[msg].startswith(marker):
                        # right answer
                        await channel.send(createReply(user,insult=False))
                        wins += 1
                    else:
                        # invalid digit
                        await channel.send(createReply(user,insult=True))
                else:
                    # invalid digit
                    await channel.send(createReply(user,insult=True)+"\nHmm... maybe next time picking a valid digit?")
            else: 
                # not a digit
                await channel.send(createReply(user,insult=True)+"\nWhat is that supposed to be? Clearly not a positive digit...")
            
            scoreboard[user.id] = (count,wins)


        elif content == key+" profile":
            if user.id in scoreboard.keys():
                await channel.send(embed=createProfile(user))
            else:
                await channel.send("You have to play a game of trivia before a profile can be generated! use `lotriv` to take a quiz!")


        elif content == key+" hangman":
            # import words for hangman
            with open("words.csv","r") as csvfile:
                word = random.choice(csvfile.readline().strip().split(','))[1:-1]
            word_condensed = word.lower().replace(" ","")
            used_chars = []
            state_ind = 0

            if len(word_condensed) <= 6:
                steps = 2
            else:
                steps = 1

            hangman_msg = await channel.send(embed=createHangman(user,word,0,steps,[],0))
            
            def check(m):
                return m.author == user and m.channel == channel

            blocked.append(user.id)
            while True:
                try:
                    msg = await client.wait_for('message',check=check,timeout=15)
                    msg = msg.content.lower()
                except asyncio.TimeoutError:
                    await hangman_msg.edit(embed=createHangman(user,word,state_ind,steps,used_chars,True))
                    await channel.send("Game over! You took too long to answer!")
                    break                   
                
                for char in msg:
                    if char in used_chars or char not in alpha:
                        continue
                    else:
                        used_chars.append(char)
                    if char not in word_condensed:
                        state_ind += steps

                used_chars.sort()
                
                if state_ind >= 7:
                    await hangman_msg.edit(embed=createHangman(user,word,state_ind,steps,used_chars,-1))
                    await channel.send("Game over! You lost all your lives!")
                    break

                all_chars_found = True
                for char in word_condensed:
                    if char not in used_chars:
                        all_chars_found = False
                
                if all_chars_found:
                    await hangman_msg.edit(embed=createHangman(user,word,state_ind,steps,used_chars,1))
                    await channel.send("Congratulations! You won the game!")
                    break
                
                await hangman_msg.edit(embed=createHangman(user,word,state_ind,steps,used_chars,0))

            blocked.remove(user.id)


try:
    with open("scoreboard.pyobj", 'rb') as sc_file:
        scoreboard = pickle.load(sc_file)
        print("successfully loaded scoreboard.pyobj")
except (FileNotFoundError,EOFError):
    print("scoreboard file not found, skipping.")

# create the client object
client = MyClient()

try:
    client.run(token)
    print("\nShutting down...")
    with open("scoreboard.pyobj", 'wb') as sc_file:
        pickle.dump(scoreboard,sc_file)

except (KeyboardInterrupt,RuntimeError):
    print("\nCatched error... Shutting down...")
    with open("scoreboard.pyobj", 'wb') as sc_file:
        pickle.dump(scoreboard,sc_file)
