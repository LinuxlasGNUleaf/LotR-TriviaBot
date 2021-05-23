# finds missing newlines
import re

regex = r".*\S.*\n\b[A-Z][A-Z]+\b"

with open('script.txt', 'r') as f:
    transcript = f.read()
    matches = re.finditer(regex, transcript)
    for match in matches:
        print (match[0])