import pickle

with open('questions_stats.txt', 'rb') as stats_file:
    stats = pickle.load(stats_file)

answered, correctly_answered = (0,0)
max_answered = 0
for item in stats:
    answered += stats[item][0]
    correctly_answered += stats[item][1]
    if not max_answered:
        max_answered = item
    elif stats[item][0] > stats[max_answered][0]:
        max_answered = item
print("SUMMARY: {} questions asked, {} answered correctly. Overall win rate of {}%".format(answered,correctly_answered,round((correctly_answered/answered)*100,1)))
print("MOST FREQUENTLY ASKED QUESTION: {} (asked {} times)".format(max_answered,stats[max_answered][0]))
max_i = int(input('Output top X easiest and hardest questions. X='))
sorted_stats = sorted(stats, key=lambda x: stats[x][1]/stats[x][0])[::-1]
print('\nTOP QUESTIONS ANSWERED\n\nRATE   COUNT QUESTION')
last = True
for i, key in enumerate(sorted_stats):
    if (i < max_i or abs(len(sorted_stats)-1-i) < max_i):
        last = True
        print('{:5}% ({:0>2}x) {}'.format(round(stats[key][1]/stats[key][0] * 100, 1), stats[key][0], key))
    elif last:
        print('[...]')
        last = False
