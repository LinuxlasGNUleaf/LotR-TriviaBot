blacklist = ["ANGLE ON:", "INT.", "Final Revision", "CONTINUED:", "INSERT", "QUICK CUTS:", "EXT.", "ANGLES ON:", "CUT","CLOSE ON:"]
with open("rotk_final.txt", "r") as from_file:
    with open("rotk_edited.txt", "w") as to_file:
        for line in from_file.readlines():
            delete_line = False
            for item in blacklist:
                if item in line:
                    delete_line = True
            if not delete_line:
                to_file.write(line)