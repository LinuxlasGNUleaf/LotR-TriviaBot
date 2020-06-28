PUNCTUATION_CHARS = ["?", "!", ".", ":"]
OTHER_CHARS = ["'", ",", " ", "-"]
CONTINUATION_CHARS = ["’"]
temp = ""
last = ""
cut_out = False

with open("lotr_twotowers.txt", "r") as from_file:
    with open("lotr_twotowers_edited.txt", "w") as to_file:
        lines = from_file.readlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                if i > 0 and i < len(lines)-1:
                    if lines[i-1].strip() and lines[i+1].strip():
                        to_file.write("\n")
                        continue
            for char in line:
                if char == "[":
                    cut_out = True
                elif char == "]":
                    cut_out = False
                    continue

                if not cut_out:
                    temp += char
            if not cut_out and temp.strip():
                to_file.write(temp.strip()+"\n")
                temp = ""
