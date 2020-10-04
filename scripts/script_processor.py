empty = False
actors = []
with open('auj.txt', 'r') as from_file:
    with open('auj_edited.txt', 'w') as to_file:
        for line in from_file.readlines():
            if line.strip():
                if empty:
                    line = line.upper()
                    if line.strip().title() not in actors:
                        actors.append(line.strip().title())
                    empty = False
            else:
                empty = True
            to_file.write(line.strip()+'\n')