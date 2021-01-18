import pickle
import matplotlib.pyplot as plt
import numpy as np

with open('questions_stats.txt', 'rb') as stats_file:
    stats = pickle.load(stats_file)
count_asked = {}
for i, key in enumerate(stats):
    count = stats[key][0]
    if count in count_asked.keys():
        count_asked[count] += 1
    else:
        count_asked[count] = 1

sorted_stats = sorted(count_asked.items(), key=lambda x: x[0])

xvalues = np.array(range(1, sorted_stats[-1][0]+1))
yvalues1 = np.zeros(np.size(xvalues))

for element in sorted_stats:
    yvalues1[element[0]-1] = element[1]


plt.plot(xvalues, yvalues1)
plt.axis([xvalues.min(), xvalues.max(), 0, yvalues1.max()*1.2])
plt.ylabel('question count')
plt.xlabel('times asked')
plt.show()