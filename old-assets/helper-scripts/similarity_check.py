import csv, os
from difflib import SequenceMatcher

f_name = 'questions.csv'
fpath = os.path.abspath(f_name)

WHOLE_QUESTIONS = False

print('opening {}...'.format(fpath))
with open(fpath, 'r') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    questions = [' '.join(q) for q in list(csvreader)] if WHOLE_QUESTIONS else [q[1] for q in list(csvreader)]
    questions_orig = questions.copy()

i = len(questions_orig)
while questions:
    qu1 = questions.pop()
    for j, qu2 in enumerate(questions):
        sim = SequenceMatcher(None, qu1, qu2).ratio()
        if sim >= 0.75:
            str1 = f"Similar questions found: \"{fpath}\", line {i:<3} "
            len_str1 = len(str1)
            str2 = f" || \"{fpath}\", line {j+1:<3} =====> {round(sim*100,1)}%"
            print(str1+str2)
            print(f"{qu1}".rjust(len_str1) +f" || {qu2}\n")
    i -= 1
