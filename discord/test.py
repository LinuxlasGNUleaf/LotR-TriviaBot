import os
import minigames

arr = []
condensed_arr = []
minigames.parseScript(os.path.abspath('lotr_fellowship.txt'), arr, condensed_arr)
for line in condensed_arr:
    print(line)
ind, part = minigames.findSimilarfromScript(input("Input: "), condensed_arr)