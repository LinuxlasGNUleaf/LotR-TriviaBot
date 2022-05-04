# finds missing newlines
import re

regex1 = r".*\S.*\n\b[A-Z][A-Z]+\b"
regex2 = r"\n\n\b[A-Z][a-z]+.*\b"

with open('script.txt', 'r') as f:
    transcript = f.read()
    matches = re.finditer(regex1, transcript)
    for match in matches:
        print (match[0])
    print('-----')
    matches = re.finditer(regex2, transcript)
    for match in matches:
        print (match[0])