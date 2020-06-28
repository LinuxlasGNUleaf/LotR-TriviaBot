PUNCTUATION_CHARS = ["?", "!", ".", ":"]
OTHER_CHARS = ["'", ",", " ", "-"]
CONTINUATION_CHARS = ["’"]
temp = ""
last = ""
cut_out = False
import string
with open("lotr_twotowers.txt", "r") as from_file:
    with open("lotr_twotowers_edited.txt", "w") as to_file:
        lines = from_file.readlines()
        for i, line in enumerate(lines):
            temp = []
            line = line.strip()
            for char in line:
                if char == "[":
                    cut_out = True
                elif char == "]":
                    cut_out = False
                
                if not cut_out:
                    temp += char
            to_file.write("\n")
            