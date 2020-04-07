# imports
import discord
import os
import random
import pickle
import time
import asyncio.exceptions

# aquire token from file
with open("/home/jakobw/.config/discord/bots/lotr-bot/token.tk","r") as tokenfile:
    token = tokenfile.readline().strip()

# some lambda code stolen from Gareth on codegolf to create ordinals:
ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

# ==========================> CONFIG <==================================
marker = '*'
key = "lotr "

insults = ["Stupid fat {}! ~Smeagol","Fool of a {}! ~Gandalf","I would cut off your head {}... if it stood but a little higher from the ground. ~Éomer",
"Dotard! What is the house of {} but a thatched barn where brigands drink in the reek, and their brats roll on the floor among the dogs? ~Saruman",
"Hey, {}! Don't go getting too far behind. ~Sam","Feanor gave up because of your stupidity, {}!"]

compliments = ["Well done, my dear {}!","{}, you should be counted amongst the wise of middleearth.","Very good {}, I could not have done it better myself!"]

scoreboard = {}
blocked = [] #temporarily blocked users (cannot issue commands)

def createEmbed(title,author_name,avatar_url,content,color,footnote):
    embed = discord.Embed(color=discord.Color.from_rgb(color[0],color[1],color[2]))
    embed.set_author(name=author_name, icon_url=avatar_url)
    embed.title = title
    embed.set_footer(text=footnote)
    embed.description = content
    return embed

def createQuestion(user,num,question,answers):
    # random color
    color = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
    author_name = "{}'s {} trial in the Arts of Middle Earth trivia".format(user.display_name,ordinal(num))
    icon_url = user.avatar_url
    title = question
    footer = "A discord bot written in Python by JaWs"
    content = ""
    for i in range(0,len(answers)):
        content += "    {}) {}\n".format(i+1,answers[i])

    return createEmbed(title,author_name,icon_url,content,color,footer)

def createProfile(user):
    played,wins = scoreboard[user.id]
    ratio = wins/played
    color = (int(255-ratio*255),int(ratio*255),0)
    author_name = "{}'s results for their trials in the Art of Middle Earth trivia".format(user.display_name)
    icon_url = user.avatar_url
    title = "{}'s results".format(user.display_name)
    content = "Trivia games played: {}\nTrivia games won: {}\nWin/Played ratio: {}%".format(played,wins,round(ratio*100,2))
    footer = "A discord bot written in Python by JaWs"
    return createEmbed(title,author_name,icon_url,content,color,footer)

def createReply(user,insult=True):
    msg = insults[random.randint(0,len(insults)-1)] if insult else compliments[random.randint(0,len(compliments)-1)]
    return msg if "{}" not in msg else msg.format(user.display_name)

class MyClient(discord.Client):

    async def on_ready(self):
        print("PreInit...")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Boromir die"))
        # importing the questions from the .csv file
        print("Importing questions from questions.csv...")
        self.questions = []
        try:
            with open("questions.csv","r") as q_file:
                for line in q_file.readlines():
                    # strip the line of trailing whitespaces, then split at ', and cut the first and last element off
                    items = line.strip().split('\"')[1:-1]

                    # remove all entries that contain only ','
                    while ',' in items:
                        items.remove(',')

                    # search for the (ultimate) answer
                    for item in items: 
                        # if item is marked
                        if item.startswith(marker):

                            # get index and remove marker, add the correct index (-1 for the question) to the back of the list
                            index = items.index(item)
                            items[index] = items[index][1:]
                            items.append(index-1)
                            break
                    
                    # add it to the questions
                    self.questions.append(items)

            print("done.")
        
        # if file does not exist, exit.
        except FileNotFoundError:
            print("failed. questions.csv not found. Aborting.")
            exit(-1)
        
        print("online. All systems operational.")

    async def on_message(self, message):
        user = message.author
        content = message.content
        channel = message.channel

        if user == client.user or user in blocked:
            return

        if content == key+"trivia":

            #get info from scoreboard
            if user.id in scoreboard.keys():
                print("user found in scoreboard!\n{}".format(scoreboard[user.id]))
                count,wins = scoreboard[user.id]
                count += 1
            else:
                print("user NOT found in scoreboard!")
                count,wins = (1,0)
            
            # get random question
            answers = self.questions[random.randint(0,len(self.questions)-1)].copy()
            # pop the question (first element)
            question = answers.pop(0)
            # get the correct answer from the last element of the list
            try:
                correct_answer = answers[int(answers[len(answers)-1])]
            except ValueError:
                print("An error occured during retrieving the right index. Probably caused by a missing marker at the correct answer.\nThe question is: {}".format(question))
                await channel.send("An error occured during parsing of the question. Please contact the developer at: `The_Legolas#1169`\nThe question was: `{}`".format(question))
                return
            # remove the last element (the correct index)
            answers.pop()

            # shuffle answers
            random.shuffle(answers)            

            # save the correct index, plus 1 (for GUI)
            ind = answers.index(correct_answer) + 1

            # send the question message
            await channel.send(embed=createQuestion(user,count,question,answers))

            def check(m):
                return m.author == user and m.channel == channel

            blocked.append(user.id)
            try:
                msg = await client.wait_for('message',check=check,timeout=15)
            except asyncio.TimeoutError:
                await channel.send(createReply(user,insult=True)+"\nYou took too long to answer!")
                return
            blocked.remove(user.id)

            if msg.content.isdigit(): 
                # if msg is a digit
                if int(msg.content) == ind:
                    # right answer
                    await channel.send(createReply(user,insult=False))
                    wins += 1
                else:
                    # wrong answer
                    await channel.send(createReply(user,insult=True))
            else: 
                # not a digit
                await channel.send(createReply(user,insult=True)+"\nWhat is that supposed to be? Clearly not a digit...")
            
            scoreboard[user.id] = (count,wins)


        elif content == key+"profile":
            if user.id in scoreboard.keys():
                await channel.send(embed=createProfile(user))
            else:
                await channel.send("You have to play a game of trivia before a profile can be generated! use `lotriv` to take a quiz!")
                
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
