import csv

with open('questions.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for i, question in enumerate(csvreader):
        if len(question) != 6:
            print("Unusal number of arguments in this question: "+question[1])
        if '?' not in question[1]:
            print("No question mark in this question: "+question[1])
        count = 0
        for item in question:
            if item.startswith('*'):
                count += 1
        if count != 1:
            print("Too many or not enough ({}) correct answers marked: {}".format(count,question[1]))
    print("done.")
