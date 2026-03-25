import csv
import os
import subprocess
import json

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

        break

try:
    funcs_json = subprocess.run(
        ['parse_lua.lua', '../demo.lua'],
        capture_output=True,
        text=True,
        check=True
    )
except subprocess.CalledProcessError as e:
    print(f"Execution failed with return code {e.returncode}")
    print(f"Error: {e.stderr}")

funcs_dict = json.loads(funcs_json.stdout)

print(funcs_dict["definitions"])

expertise_map = {}

commits['test'] = ['Goku', 'Sun, 22 Mar 1733 22:11:35 -0300', 'goku@gmail.com', [['1', '21']]]

for func in funcs_dict["definitions"]:
    func_name = func["name"]
    start_line = int(func["line_start"])
    end_line = int(func["line_end"])

    if func_name not in expertise_map:
        expertise_map[func_name] = {}

    for hash, data in commits.items():
        email = data[2]
        date = data[1] 
        lines_changed = data[3] 

        for change in lines_changed:
            change_start = int(change[0])
            
            if (change_start >= start_line and change_start <= end_line):
                if email not in expertise_map[func_name]:
                    expertise_map[func_name][email] = 1
                else:
                    expertise_map[func_name][email] += 1

print(expertise_map)