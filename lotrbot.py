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

insults = ["Stupid fat hobbit! ~Smeagol","Fool of a took! ~Gandalf","I would cut off your head {}... if it stood but a little higher from the ground. ~Éomer",
"Dotard! What is the house of {} but a thatched barn where brigands drink in the reek, and their brats roll on the floor among the dogs? ~Saruman",
"Hey, Stinker! Don't go getting too far behind. ~Sam","Feanor gave up because of your stupidity"]

compliments = ["Well done, my dear hobbit!","{}, you should be counted amongst the wise of middleearth.","I could not have done it better myself!"]

scoreboard = {}

def format_questionString(user,num,question,answers):
    # random color
    color = discord.Color.from_rgb(random.randint(0,255),random.randint(0,255),random.randint(0,255))
    embed = discord.Embed(color=color)
    embed.set_author(name="{}'s {} trial in the Arts of Middle Earth trivia".format(user.display_name,ordinal(num)), icon_url=user.avatar_url)
    embed.title = question
    embed.set_footer(text="A discord bot written in Python by JaWs")
    ans_str = ""
    for i in range(0,len(answers)):
        ans_str += "    {}) {}\n".format(i+1,answers[i])
    embed.description = ans_str
    return embed

def createMsg(user,insult=True):
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

        if user == client.user:
            return

        if content == "lotriv":
            # get random question
            answers = self.questions[random.randint(0,len(self.questions)-1)].copy()
            # strip the question (first element)
            question = answers.pop(0)
            # get the correct answer from the last element of the list
            correct_answer = answers[int(answers[len(answers)-1])]
            # remove the last element (the correct index)
            answers.pop()

            # if the author is already in the scoreboard, retrieve info
            if user in scoreboard.keys():
                content = scoreboard[user]
                scoreboard[user] = (content[0]+1,[content[1]])
                count = content[0]+1
            else:
                scoreboard[user] = (1,0)
                count = 1

            # shuffle answers
            random.shuffle(answers)            

            # save the correct index, plus 1 (for GUI)
            ind = answers.index(correct_answer) + 1

            # send the question message
            await message.channel.send(embed=format_questionString(user,count,question,answers))

            def check(m):
                return m.author == user and m.channel == channel
            try:
                msg = await client.wait_for('message',check=check,timeout=15)
            except asyncio.TimeoutError:
                await message.channel.send(createMsg(user,insult=True)+"\nYou took to long to answer!")
                return

            if msg.content.isdigit(): # if msg is a digit
                if int(msg.content) == ind:
                    await message.channel.send(createMsg(user,insult=False))
                    scoreboard[user] = (scoreboard[user][0],scoreboard[user][1]+1) # increase the won games counter
                else:
                    await message.channel.send(createMsg(user,insult=True))
            else: # not a digit
                await message.channel.send(createMsg(user,insult=True)+"\nWhat is that supposed to be? Clearly not a digit...")
                
try:
    with open("scoreboard.pyobj", 'rb') as sc_file:
        scoreboard = pickle.load(sc_file)
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
    print("\nShutting down...")
    with open("scoreboard.pyobj", 'wb') as sc_file:
        pickle.dump(scoreboard,sc_file)
