import csv
import os
import subprocess
import json
import re
import tempfile
from pprint import pprint

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
# TODO: Implement file caching across commmits if not changed too much?
# Any way to limit search to around commit areas to improve performance?
# Improve with pandas?
expertiseMap = {}

functionCache = {}

for hash, data in commits.items():

    for file, hunks in data['fileChanges'].items():

        cacheKey = (hash, file)
        
        if cacheKey not in functionCache:
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
                print(funcsJSON.stdout)
                data['fileFunctions'][file] = json.loads(funcsJSON.stdout)
            except subprocess.CalledProcessError as e:
                print(f"File not found {file}: {e.stderr}")
            finally: 
                os.remove(luaInputPath)

            functionCache[cacheKey] = 


        email = data['email']
        date = data['date']
        expertiseMa

        for change in data['fileFunctions'][file]['definitions']:
            # Function overlap
            functionStart = 
            startLine = change[0]
            endLine = [change][0] + change[1]
            
            
def sortFuncs(definitions):
    funcs = []
    for f in definitions:
        start = f.get('line_start') or f['line']
        end   = f.get('line_end')   or f['line']
        funcs.append((start, end, f.get('name')))
    return sorted(funcs, key=lambda f: f[0]) 
        
        
def getBlobHash(hash, file, cwd):
    result = subprocess.run(
        ['git', 'ls-tree', hash, '--', file],
        cwd=cwd, capture_output=True, text=True
    )
    # output: "100644 blob a1b2c3d4...  filename"
    parts = result.stdout.split()
    return parts[2] if len(parts) >= 3 else None

