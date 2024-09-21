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

x_values = np.array(range(1, sorted_stats[-1][0] + 1))
y_values1 = np.zeros(np.size(x_values))

for element in sorted_stats:
    y_values1[element[0] - 1] = element[1]

plt.plot(x_values, y_values1)
plt.axis([min(x_values), max(x_values), 0, max(y_values1) * 1.2])
plt.ylabel('question count')
plt.xlabel('times asked')
plt.show()
