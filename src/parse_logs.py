import csv 
import os
import subprocess
# 

hash: str
author: str
email: str
date: str

target_dir = "../../smods"

result = subprocess.run(['./commit_csv.sh' ], cwd=target_dir, capture_output=True, text = True, check=True)

#print(result.stdout)
if (result.returncode != 0):
    #print(result.stderr)
    os.abort(1)
else:
    lines = result.stdout.split("\n")
    for row in lines:
        row = row[1:len(row) -1]
        print(row)
        stuff = row.split('","')
        hash = stuff[0]
        author = stuff[1] 
        email = stuff[2]
        date = stuff[3]
        results2 = subprocess.run(['git', 'show', hash], cwd= target_dir, capture_output=True, text = True, check=True)
