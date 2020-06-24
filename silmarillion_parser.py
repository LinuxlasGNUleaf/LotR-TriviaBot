PUNCTUATION_CHARS = ["?", "!", ".", ":"]
OTHER_CHARS = ["'",","," ","-"]
CONTINUATION_CHARS = ["’"]
temp = ""
last = ""
unknown = []
import string
with open("silmarillion.txt","r") as from_file:
    with open("silmarillion_edited.txt","w") as to_file:
        lines = from_file.readlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if line.isupper():
                to_file.write(line+"\n")
                continue
            if not line:
                if i < len(lines) - 1:
                    if lines[i+1].replace(" ","").isupper():
                        to_file.write("\n")
                continue
            for j, char in enumerate(line):
                if char.isupper() and last.islower() and j > 0:
                    temp += char.lower()
                else:
                    temp += char
                
                if not(char in string.ascii_letters or char in string.digits or char in PUNCTUATION_CHARS or char in OTHER_CHARS):
                    if char not in unknown:
                        unknown.append(char)
                if char in PUNCTUATION_CHARS:
                    if j < len(line) - 1:
                        if line[j+1] in CONTINUATION_CHARS:
                            continue
                    elif i < len(lines) - 1:
                        if lines[i+1].strip():
                            if lines[i+1].strip() in CONTINUATION_CHARS:
                                continue
                    to_file.write(temp.strip()+"\n")
                    temp = ""

                last = char
            temp += " "

for char in unknown:
    print(char)