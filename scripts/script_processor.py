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
            to_file.write(line+'\n')

exit(0)
with open('dos.txt', 'r') as from_file:
    with open('dos_edited.txt', 'w') as to_file:
        lines = from_file.readlines()
        for ind, line in enumerate(lines):
            if line.strip():
                if empty:
                    line = line.upper()
                    if line.strip().title() not in actors:
                        actors.append(line.strip().title())
                    empty = False
            else:
                empty = True
            to_file.write(line.strip()+'\n')
