import csv
import os
import subprocess
import json
import re
import tempfile
import pprint

hash: str
author: str
email: str
date: str
commits = {}

targetDir = "../../smods"
scriptPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commit_csv.sh")

try:
    logs = subprocess.run([scriptPath], cwd=targetDir, capture_output=True, text=True, check=True)
except subprocess.CalledProcessError:
    sys.exit(1)

currentLogHash = None
currentLog = None
currentFile = None
for line in logs.stdout.split("\n"):

    commitMatch = re.match(r'^commit ([0-9a-f]{40})', line)
    if commitMatch:
        if currentLog:
            commits[currentLogHash] = currentLog
            #print(commits[currentLogHash])
            break
        currentLogHash = commitMatch.group(1)
        currentLog = {'author': None, 'email': None, 'date': None, 'fileChanges': {}, 'fileFunctions': {}} # file changes are a dictionary of file -> hunks[]
        currentFile = None
        continue # move to next line

    # iterate until commit line is found
    if not currentLog:
        continue

    authorMatch = re.match(r'^Author: (.+?) <(.+?)>', line)
    if authorMatch:
        currentLog['author'] = authorMatch.group(1)
        currentLog['email'] = authorMatch.group(2)

    elif dateMatch := re.match(r'^Date:\s+(.+)', line):
        currentLog['date'] = dateMatch.group(1)

    elif fileMatch := re.match(r'^\+\+\+ b/(.*)', line):
        currentFile = fileMatch.group(1)
        currentLog['fileChanges'].setdefault(currentFile, [])
    
    elif currentFile and (hunkMatch := re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)):
        hunkNewStartLine = int(hunkMatch.group(3))
        hunkNewCount = int(hunkMatch.group(4)) if hunkMatch.group(4) else 1
        currentLog['fileChanges'][currentFile].append([hunkNewStartLine, hunkNewCount])
        
    #     currentLog['fileChanges'][currentFile].append({
    #         'start': hunkNewStartLine,
    #         'count': hunkNewCount,
    #         'lines': []
    #     })
    
    # elif currentFile and currentLog['fileChanges'].get(currentFile): # placeholder is in
    #     currentHunk = currentLog['fileChanges'][currentFile][-1]  # last in list (next always last)
    #     if line.startswith('+') and not line.startswith('+++'): # new lines
    #         currentHunk['lines'].append(line[1:])  # strip +


# Last commit
if currentLog:
    commits[currentLogHash] = currentLog



# Funcs extraction
for hash, data in commits.items():
    for file in data['fileChanges']:
    
        fullNewFile = subprocess.run(['git', 'show', f'{hash}:{file}'], 
         cwd=targetDir, capture_output=True, text=True, check=True)
        if fullNewFile.returncode != 0: 
            continue

        with tempfile.NamedTemporaryFile(mode='w', suffix ='.lua', delete=False) as luaInput:
            luaInput.write(fullNewFile.stdout)
            luaInputPath = luaInput.name
        
        try:
            funcsJSON = subprocess.run(['parse_lua.lua', luaInputPath],#, input = fullNewFile.stdout,
            capture_output=True, text=True, check=True)
            data['fileFunctions'][file] = json.loads(funcsJSON.stdout)
        except subprocess.CalledProcessError as e:
            print(f"File not found {file}: {e.stderr}")
        finally: 
            os.remove(luaInputPath)
    
        #data['fileFunctions'][file] = json.loads(funcsJSON.stdout)
    pprint(commits)

