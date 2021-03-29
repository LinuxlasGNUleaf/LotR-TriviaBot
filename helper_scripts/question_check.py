import csv, os
fname = 'questions.csv'
fpath = os.path.abspath(fname)
print('opening {}...'.format(fpath))
with open(fpath, 'r') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for i, question in enumerate(csvreader):
        question_str = '"{}", line {}\t'.format(fpath,i+1)
        if len(question) != 6:
            try:
                print(question_str+"Unusal number of arguments in this question: "+question[1])
            except IndexError:
                print("VERY unusal number of arguments in the {}. question!".format(i))
            continue
        if 'source' in question[1].lower():
            print(question_str+"Source not set for this question: "+question[1])
            continue
        if '?' not in question[1]:
            print(question_str+"No question mark in this question: "+question[1])
            continue
        count = 0
        for item in question:
            if item.startswith('*'):
                count += 1
        if count != 1:
            print(question_str+"Too many or not enough ({}) correct answers marked: {}".format(count,question[1]))
    print("done.")
