import pickle
import pathlib

bd_file =  pathlib.posixpath.expandvars('/home/$USER/.config/discord/bots/lotr-bot/caches/birthdays.cache')
with open(bd_file, 'rb') as infile:
    bdays = pickle.load(infile)

first = True
fstring = '{:>02}\t{:<32}\t{:>02}.{:>02}.\t{:>20}'

while (first or input('Continue? [Y/n]').lower() != 'n'):
    first = False
    for i, content in enumerate(bdays):
        month, day, name, id = content
        print(fstring.format(i, name, day, month, id if id else "None"))
    print("="*64)
    delete_index = input(f"Enter index to delete (or use index {len(bdays)} to append): ")
    if not delete_index.isdecimal():
        print("Invalid input!")
        continue
    delete_index = int(delete_index)
    if delete_index in range(len(bdays)):
        info = bdays[delete_index]
        print(f"Deleting {info[2]}'s birthday...")
        del bdays[delete_index]
        continue
    elif delete_index == len(bdays):
        try:
            name = input('Name: ')
            day = int(input('Day of Month: '))
            month = int(input('Month: '))
            id = input('ID: (leave empty for None): ')
            id = None if not id else id
            bdays.append([month, day, name, id])
        except TypeError:
            print("Invalid input, aborting append.")
        continue
    else:
        print("Index not in range!")
        continue

with open(bd_file, 'wb') as outfile:
    pickle.dump(bdays, outfile)