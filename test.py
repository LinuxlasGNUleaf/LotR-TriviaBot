PUNCTUATION_CHARS = ["?", "!", ".", ":"]
OTHER_CHARS = ["'",","," ","-"]
temp = ""
last = ""
unknown = []
import string
with open("silmarillion.txt","r") as from_file:
    with open("silmarillion2.txt","w") as to_file:
        last_line = ""
        for i, line in enumerate(from_file.readlines()):
            line = line.strip()
            if line.isupper():
                to_file.write(line+"\n")
                continue
            if not line:
                to_file.write("\n")
                continue
            for char in line:
                if char.isupper() and last.islower():
                    temp += char.lower()
                else:
                    temp += char
                
                if not(char in string.ascii_letters or char in string.digits or char in PUNCTUATION_CHARS or char in OTHER_CHARS):
                    if char not in unknown:
                        unknown.append(char)
                if last in PUNCTUATION_CHARS:
                    to_file.write(temp[:-1].strip()+"\n")
                    temp = ""

                last = char
            temp += " "
            last_line = line

for char in unknown:
    print(char)