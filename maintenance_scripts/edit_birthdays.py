import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

DEFAULT_TIMEZONE = 'GMT'


def valid_timezone(name):
    try:
        ZoneInfo(name)
        return True
    except (ZoneInfoNotFoundError, ValueError):
        return False


bd_file = os.path.expandvars('$HOME/.config/discord/bots/lotr-bot/caches/birthdays.yaml')
with open(bd_file, 'r', encoding='utf-8') as infile:
    bdays = yaml.safe_load(infile) or []

for index, entry in enumerate(bdays):
    month, day, name, uid, *timezone = entry
    timezone = timezone[0] if timezone and valid_timezone(timezone[0]) else DEFAULT_TIMEZONE
    bdays[index] = [month, day, name, uid, timezone]

first = True
fstring = '{:>02}\t{:<32}\t{:>02}.{:>02}.\t{:>20}'

while (first or input('Continue? [Y/n]').lower() != 'n'):
    first = False
    for i, content in enumerate(bdays):
        month, day, name, id, timezone = content
        print(f'{fstring.format(i, name, day, month, id if id else "None")}\t{timezone}')
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
            timezone = input(f'Timezone [{DEFAULT_TIMEZONE}]: ').strip() or DEFAULT_TIMEZONE
            if not valid_timezone(timezone):
                print('Invalid timezone, aborting append.')
                continue
            bdays.append([month, day, name, id, timezone])
        except (TypeError, ValueError):
            print("Invalid input, aborting append.")
        continue
    else:
        print("Index not in range!")
        continue

with open(bd_file, 'w', encoding='utf-8') as outfile:
    yaml.safe_dump(bdays, outfile, allow_unicode=True, sort_keys=False)