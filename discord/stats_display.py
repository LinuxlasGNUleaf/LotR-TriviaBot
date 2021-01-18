import pickle

with open('questions_stats.txt', 'rb') as stats_file:
    stats = pickle.load(stats_file)
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
