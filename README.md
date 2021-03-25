# LotR-TriviaBot
This is a discord bot written in Python 3.
It utilizes the Discord, Reddit and Youtube Data API.
The bot features multiple minigames, including:
* **LotR - Trivia Game**
In this game you get asked trivia questions from LotR, the Hobbit, the Silmarillion and the Extended Lore. You have four possible answers, your score is tracked.
Additional features include profile and server-wide scoreboard creation.
* **LotR - Hangman**
Features the classic hangman game with LotR terms.
* **Random Silmarillion quote**
Output a random Silmarillion quote on demand.
* **Reddit meme**
Outputs a dank meme from r/lotrmemes or r/hobbit_memes.
* **Autoscript feature**
Recognizes lines from the movie script and in the case of a 85% match, completes the sentence and prints the next dialog line
* **Youtube videos**
Searches for videos from a specific Youtube Channel.
The Channel ID is set in the config.
* **LotR Wiki Search**
Searches the wiki for a specific topic.
The wiki URL is set in the config file.
* **Configuration**
Adding easy-to-use config to control use of features channel- and server-wide
* **LotR Battle**
Challenge your friends to a battle in LotR trivia!

# Checklist

## Done
- [x] LotR trivia quiz
- [x] LotR hangman with words from Middleearth
- [x] Silmarillion quotes on demand
- [x] Autoscript feature
- [X] Reddit memes from r/lotrmemes and r/hobbit_memes
- [x] Pylint refactoring
- [X] Youtube API
- [X] parsing all three movies for autoscript feature
- [x] Adding config to control use of features channel- and server-wide
- [x] Switched from overkill PRAW reddit API to simple read-only JSON api for massive performance boost

## QOL Improvements
- [x] Fixing DM issues
- [x] Respecting Discord Permissions
- [x] support for Reddit crossposts, text-only and image-embed submissions
- [x] Graphical Config Visualization

# Code Contributors
Well, that would be me. If you want to contact me,
you can also send me a DM on Discord: `Linuxlas GNUleaf#1169`
## Trivia Questions Contributors
* MC4dden
* Eldarion
* Savior of teh White Tree
* Teh Lurd of Hogwarts
* Lord HellRaiser
* Hobbz45 The Orange

## Help wanted
You want to help? Great! There are currently the following tasks (apart from coding) that you could help with:
* **Adding new questions to `questions.csv`** If the format of the file confuses you, contact me and I will explain how it gets parsed.
* **Adding new words to `words.csv`** This is the source for the hangman game. The format is pretty self-explanatory.

**TO SUBMIT NEW QUESTIONS, FILL OUT THIS [FORM](https://forms.gle/k4oMTiyUEJgntMyb9)**

# Developer Informations
## To add the bot to your Discord Server:
Want to add the bot to your server? Use this link: [click here](https://discord.com/oauth2/authorize?client_id=694837766504316948&scope=bot&permissions=268495936) or do it yourself with the [perms calculator](https://discordapi.com/permissions.html) and the client_id `694837766504316948`

## To host the bot yourself:
Install python3 on your OS, clone this repository and run `pip3 install -r requirements.txt` to install the necessary packages.
The bot will create cache files. **Changing the default directory is mandatory on Windows**, on Linux you will have to create the directory `~/.config/discord/bots/lotr-bot`. To change the direcotry, see the `config.yaml`.
Run the bot with: `python3 main.py`, preferrably in a Terminal Multiplexer like screen or tmux.
To stop the bot, hit `Ctrl+C` **once**.