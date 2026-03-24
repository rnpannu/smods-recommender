import csv
import os
import subprocess

hash: str
author: str
email: str
date: str
commits = {}

target_dir = "../../smods"

script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commit_csv.sh")

result = subprocess.run(
    [script_path],  
    cwd=target_dir,
    capture_output=True,
    text=True,
    check=True
)

if result.returncode != 0:
    os.abort(1)
else:
    for line in result.stdout.split("\n"):
        line = line[1:len(line) - 1]
        stuff = line.split('","')
        hash = stuff[0]
        author = stuff[1]
        email = stuff[2]
        date = stuff[3]
        diff = subprocess.run(['git', 'show', hash], cwd=target_dir, capture_output=True, text=True, check=True)
        lines_changed = []
        for row in diff.stdout.split("\n"):
            #print(row)
            if row[0:2] == "@@":
                header = row[0:23].strip(" ")
                
                header_items = header.split(" ")[1:3]
                old = header_items[0].strip("-").split(",")
                new = header_items[1].strip("+").split(",")
                
                if (len(old) != 1 and len(new[0]) != 1):
                    lines_changed.append(new)
        commits[hash] = [author, date, email, lines_changed]
        print("Commit: " + hash, end = ". ")
        print(commits[hash])


