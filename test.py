import lotr_config
import csv
import random
from time import sleep 

with open('questions.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    content = random.choice(list(csvreader))

char_count = 0
for item in content[1:]:
    char_count += len(item.strip())
    print(item)

timeout = char_count / lotr_config.DISCORD_CONFIG['trivia.multiplier'] + \
                      lotr_config.DISCORD_CONFIG['trivia.extra_time']
print(timeout)
sleep(timeout)
print("Time's up!")
