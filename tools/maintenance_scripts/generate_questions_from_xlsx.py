from openpyxl import load_workbook
import csv

data_file = 'assets/questions.xlsx'

# Load the worksheet
ws = load_workbook(data_file)['questions']
# put values in matrix
all_rows = [[str(cell.value) for cell in row] for row in ws.rows]
# sort by source first and level second
all_rows.sort(key=lambda row: row[1]+row[0].rjust(2))
# add correct answer mark for questions where it is not marked
for i, row in enumerate(all_rows):
    lvl, source, question, *answers = row
    correct_index = -1
    for ind, answer in enumerate(answers):
        if answer.startswith('*'):
            correct_index = ind
            break
    # if no answer is marked, mark the first one
    if correct_index == -1:
        answers[0] = f'*{answers[0]}'
        correct_index = 0

    correct_answer = answers.pop(correct_index)
    all_rows[i] = [source, lvl, question, *answers]
    print(all_rows[i])

with open('assets/questions.csv', 'w', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file, quoting=csv.QUOTE_ALL, lineterminator='\n')
    writer.writerows(all_rows)