import os
import minigames

arr = []
condensed_arr = []
minigames.parse_script(os.path.abspath('lotr_fellowship.txt'), arr, condensed_arr)
for line in condensed_arr:
    print(line)
ind, part = minigames.find_similar_from_script(input("Input: "), condensed_arr)
