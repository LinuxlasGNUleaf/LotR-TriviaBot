# LotR-TriviaBot
This is a discord bot written in Python 3.
It utilizes the Discord, Reddit (and Google in the near future) API.
The bot features mutliple minigames, including:
* **LotR - Trivia Game**
In this game you get asked trivia questions from LotR, the Hobbit, the Silmarillion and the Extended Lore. You have four possible answers. Your score is tracked.
* **LotR - Hangman**
Features the classic hangman game with LotR terms
* **Random Silmarillion quote**
Output a random Silmarillion quote on demand.
* **Reddit meme**
Outputs a dank meme from r/lotrmemes
* **Autoscript feature**
Recognizes lines from the movie script and in the case of a 85% match, completes the sentence and prints the next dialog line

## TODO
- [x] **Succeeding in keeping the god damn credentials out of the repository** they old ones are all invalid by now, so don't even bother :)
- [x] LotR trivia quiz
- [x] LotR hangman with words from Middleearth
- [x] Silmarillion quotes on demand
- [x] Autoscript feature
- [X] Reddit memes from r/lotrmemes (not yet finished)
- [x] Pylint refactoring
- [X] Youtube API
- [ ] Using Facebook API for fetching memes from ShirePosting :/
- [ ] enhance Silmarillion quote parser

## Contributors
Well, that would be me. If you want to contact me,
you can also send me a DM on discord: `The_Legolas#1169`

## Help wanted
You want to help? Great! There are currently the following tasks (apart from coding) that you could help with:
* **Adding new questions to `questions.csv`** If the format of the file confuses you, contact me and I will explain how it gets parsed.
* **Adding new words to `words.csv`** This is the source for the hangman game. The format is pretty simple, but you can ask me ofc.
* **Preparing another movie script** That would be a *HUGE* help, but is also incredibly annoying. At the moment, I have only prepared the Fellwoship of the Ring for parsing. On further information how to prepare the scripts, contact me.