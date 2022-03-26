from curses import doupdate
import yaml
import sys

with open("triple.yaml", 'r', encoding='utf-8') as qstream:
    try:
        print('parsing config file...')
        quotes = yaml.safe_load(qstream)
    except yaml.YAMLError as exc:
        print(f'While parsing the quote file, the following error occured:\n{exc}')
        sys.exit()

for quote in quotes["tripleQuotes"]["nonshipping"]["sfw"]:
    s = quote.format("Amelie","Ben","Carmen",ast=r"\*")
    input(s+"\n")
    