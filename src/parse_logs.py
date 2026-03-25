import csv
import os
import subprocess
import json
import re

hash: str
author: str
email: str
date: str
commits = {}

target_dir = "../../smods"
script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commit_csv.sh")

logs = subprocess.run([script_path], cwd=target_dir, capture_output=True, text=True, check=True)

        for line in logs.stdout.split("\n"):
        line = line[1:len(line) - 1]
        stuff = line.split('","')
        hash = stuff[0]
        author = stuff[1]
        email = stuff[2]
        date = stuff[3]
        diff = subprocess.run(['git', 'show', hash], cwd=target_dir, capture_output=True, text=True, check=True)
        lines_changed = []

        current_file = None
        file_changes = {str : list}
        for row in diff.stdout.split("\n"):

            file_match = re.match(r'^\+\+\+ b/(.*)', row)

            if file_match:
                current_file = file_match.group(1)
                print(current_file)
                if current_file not in file_changes:
                    file_changes[current_file] = []


            match = re.match(r'^@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@', row)
            if match and current_file:
                new_start = int(match.group(3))
                new_amt = int(match.group(4)) if match.group(4) else 1

                file_changes[current_file].append([new_start, new_amt])
                
        commits[hash] = [author, date, email, file_changes]
        print("Commit: " + hash, end = ". ")
        print(commits[hash])
        ### Stop at first commit
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

### TEST INSERTS
commits['test'] = ['Goku', 'Sun, 22 Mar 1733 22:11:35 -0300', 'goku@gmail.com', {'demo.lua': [['1', '21']]}]

expertise_map = {}
for func in funcs_dict['definitions']:
    func_name = func['name']
    func_start_line = int(func['line_start'])
    func_end_line = int(func['line_end'])

    if func_name not in expertise_map:
        expertise_map[func_name] = {}

    for hash, data in commits.items():
        email = data[2]
        date = data[1] 
        files_changed = data[3] 
        
        for file, changes in files_changed.items():
            #change_file = files_changed['demo.lua']
            func_file = 'game_object.lua'
            if file == func_file:
                for change in changes:
                    change_start = int(change[0])
                    change_end = change_start + int(change[1])

                    if not (change_end < func_start_line or change_start > func_end_line):
                        if email not in expertise_map[func_name]:
                            expertise_map[func_name][email] = 1
                        else:
                            expertise_map[func_name][email] += 1

print(expertise_map)

