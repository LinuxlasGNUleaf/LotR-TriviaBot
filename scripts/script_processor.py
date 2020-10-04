empty = True
actors = []
with open('dos.txt', 'r') as from_file:
    with open('dos_edited.txt', 'w') as to_file:
        lines = from_file.readlines()
        for ind, line in enumerate(lines):
            line = line.strip()
            if '[' in line:
                start = line.index('[')
                end = line.index(']')
                if not(start >= 0 and end > start):
                    print('Faulty line: {}\nstart:{}\nend:{}'.format(line, start, end))
                    raise Exception("Error in line: {} invalid square brackets. Please remove.".format(ind+1))
                if start == 0 and end == len(line)-1:
                    continue
                temp = line[start:end+1]
                line = line.replace(temp, '').replace('  ', ' ').replace('  ', ' ')

            line = line.replace('’', '\'')
            to_file.write(line+'\n')

with open('dos.txt', 'r') as from_file:
    with open('dos_edited.txt', 'w') as to_file:
        lines = from_file.readlines()
        for ind, line in enumerate(lines):
            temp = line.split(': ')
            if len(temp) > 2:
                author = temp[0]
                line = ':'.join(temp[1:])
            else:
                if len(temp) != 2:
                    raise Exception("Error in line: {} No \" indicator. Please check.".format(ind+1))
                author, line = temp
            to_file.write('{}\n{}\n'.format(author.upper(), line))
