import sys
import os
import yaml

greek_to_num = {
    1:'single',
    2:'double',
    3:'triple',
    4:'quad',
    5:'penta',
    6:'hexa'
}

suspicious_chars = ['<','[',']','>']

with open('quotes.yaml', 'r', encoding='utf-8') as qfile:
    try:
        sys.stdout.write(f'parsing {qfile.name}...')
        quotes = yaml.safe_load(qfile)
        print('done.')
    except yaml.YAMLError as exc:
        print(f'While parsing {qfile.name}, the following error occured:\n{exc}')
        sys.exit(0)

for num, category in greek_to_num.items():
    print(f"{'='*30}> checking {category}Quotes. <{'='*30}")

    quoteCategory = quotes[f"{category}Quotes"]
    all_quotes = quoteCategory["shipping"]["nsfw"] + quoteCategory["shipping"]["sfw"] + quoteCategory["nonshipping"]["nsfw"] + quoteCategory["nonshipping"]["sfw"]

    print("testing for suspicious characters...")
    for i, quote in enumerate(all_quotes):
        for char in suspicious_chars:
            if char in quote:
                i = quote.index(char)
                quote = quote[i-20:i+20].replace("\n","")
                print(f'\tfound "{char}" in quote:\n\t\t"{quote}"\n')
    print("done.\n")

    print("testing for invalid number of characters...")
    for i, quote in enumerate(all_quotes):
        for test_num in range(max(greek_to_num.keys())):
            if not ("{"+str(test_num)+"}") in quote and test_num < num:
                print(f'player {test_num} not found in quote:\n\t\t"{quote[:40]}"')
            elif ("{"+str(test_num)+"}") in quote and test_num >= num:
                print(f'player {test_num} found in quote, which is more than allowed:\n\t\t"{quote[:40]}"')
    print("done.\n")