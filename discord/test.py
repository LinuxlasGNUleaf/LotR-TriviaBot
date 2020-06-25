import os
import minigames

with open("silmarillion_edited.txt","r") as silm:
    silm = silm.readlines()
    for line in silm:
        line = line.strip()
        if minigames.is_headline(line):
            print(line)