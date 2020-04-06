import discord
import os
import random
import pickle
import time

with open("/home/jakobw/.config/discord/bots/lotr-bot/token.tk","r") as tokenfile:
    token = tokenfile.readline().strip()
    
marker = '*'
insults = ["Stupid fat hobbit! ~Smeagol","Fool of a took! ~Gandalf","I would cut off your head {}... if it stood but a little higher from the ground. ~Éomer",
"Dotard! What is the house of {} but a thatched barn where brigands drink in the reek, and their brats roll on the floor among the dogs? ~Saruman",
"Hey, Stinker! Don't go getting too far behind. ~Sam","Feanor gave up because of your stupidity"]
compliments = ["Well done, my dear hobbit!","{}, you should be counted amongst the wise of middleearth.","I could not have done it better myself!"]
scoreboard = {}
class PendingEvent():
    def __init__(self,correct_ind,author,timestamp,channel):
        self.correct_ind = correct_ind
        self.author = author
        self.timestamp = timestamp
        self.channel = channel

pending = []

def format_questionString(bot,user,num,question,answers):
    # random color
    cl = discord.Color.from_rgb(random.randint(0,255),random.randint(0,255),random.randint(0,255))

    embed = discord.Embed(color=cl)
    embed.title = "LotR trivia quiz for {} (number {})".format(user,num)
    embed.set_author(name=bot.user.display_name, icon_url=bot.user.avatar_url)
    ans_str = ""
    for i in range(0,len(answers)):
        ans_str += "    {}) {}\n".format(i+1,answers[i])
    out = "****```\n {}\n\n{}```""".format(question,ans_str)
    embed.description = ans_str
    return embed

def stripName(name):
    return str(name).split("#")[0]

def createMsg(insult,user):
    if insult:
        msg = "`"+insults[random.randint(0,len(insults)-1)]+"`"
    else:
        msg = "`"+compliments[random.randint(0,len(compliments)-1)]+"`"
    if "{}" in msg:
        return msg.format(user)
    return msg

class MyClient(discord.Client):

    async def on_ready(self):
        print("Booting up... ")
        print("Setting status...")

        # sets status to "watching Boromir die"
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Boromir die"))
        print("done.")
        
        # importing the questions from the .csv file
        print("Attempting to import the questions from questions.csv...")
        self.questions = []
        try:
            with open("questions.csv","r") as q_file:
                # one line, one question
                for line in q_file.readlines():
                    # strip the line of trailing whitespaces, then split at ', and cut the first and last element off
                    items = line.strip().split('\'')[1:-1]

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
        if message.author == client.user:
            return

        # check for user who sended the message
        for pend_event in pending:

            # if author and the channel matches
            if message.author == pend_event.author and message.channel == pend_event.channel:

                # try to parse the answer given to an int
                content = scoreboard[message.author]
                try:
                    answer = int(message.content)
                    # if answer is correct:
                    if answer == pend_event.correct_ind:
                        await message.channel.send(createMsg(False,stripName(message.author)))
                        scoreboard[message.author] = (scoreboard[message.author][0],content[1]+1)
                    # if not:
                    else:
                        await message.channel.send(createMsg(True,stripName(message.author)))
                except ValueError:
                    await message.channel.send(createMsg(True,stripName(message.author))+"\nThis is not a valid answer! Don't you know how to count to four?")
                pending.remove(pend_event)
                return
        
        # if the message is the trivia command
        if message.content == "lotriv":
            # get random question
            answers = self.questions[random.randint(0,len(self.questions)-1)].copy()
            # strip the question (first element)
            question = answers.pop(0)
            # get the correct answer from the last element of the list
            correct_answer = answers[int(answers[len(answers)-1])]
            # remove the last element (the correct index)
            answers.pop()

            # if the author is already in the scoreboard, retrieve info
            if message.author in scoreboard.keys():
                content = scoreboard[message.author]
                scoreboard[message.author] = (content[0]+1,[content[1]])
                count = content[0]+1
            else:
                scoreboard[message.author] = (1,0)
                count = 1

            # shuffle answers
            random.shuffle(answers)            

            # save the correct index, plus 1 (for GUI)
            ind = answers.index(correct_answer) + 1

            # send the question message
            await message.channel.send(embed=format_questionString(self,stripName(message.author),count,question,answers))

            # create a new pending object
            newpending = PendingEvent(ind,message.author,message.created_at,message.channel)

            # append to pending list (lol)
            pending.append(newpending)

        elif message.content == "lotrprofile":
            if message.author in scoreboard:
                content = scoreboard[message.author]
                await message.channel.send("Profile for {}\n```Total played trivia games: {}\nTotal trivia won games   :{}".format(stripName(message.author),content[0],content[1]))

try:
    with open("scoreboard.pyobj", 'rb') as sc_file:
        scoreboard =  pickle.load(sc_file)
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
