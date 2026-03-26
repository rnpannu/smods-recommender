import csv
import os
import subprocess
import json
import re
import tempfile
from pprint import pprint
from collections import defaultdict


# Two maps
# Commit history : {hash : [author, email, date, hunkChanges{file : [startLine, lineCount]}]}
# Expertise map: {author(email) : {date : functionsWorkedOn{ function: linesChanged}}}
# 1. Extract commit history from logs
# 2. For each (complete) file in the commit, extract functions
# 3. Map hunk changes to functions and add them to developer expertise map under their date


# 1. Parse Logs
# Run log script
targetDir = "../../smods"

# {email (author key) :  { date_of_commit: [functionsWorkedOn[(function, linesChanged)], functionsCalled[function, times_called]] }
# email mapped to date, date mapped to a 2-list of lists of 2-tuples
# Times called is a list not a dictionary because a function can have the same name but be at different spots
expertiseMap: defaultdict[str, defaultdict[str, list]]
expertiseMap = defaultdict(lambda: defaultdict(lambda: [[], []]))

# Update function expertise values for a file change in a commit
def extractFunctions(log, file, hunks, email, date):

    # Extract functions from a file corresponding to a change hunk
    functionJSON: defaultdict[str, list[dict[str, int | str]]]

    fullNewFile = subprocess.run(['git', 'show', f'{log}:{file}'], 
    cwd=targetDir, capture_output=True, text=True) #, check=True)
    if fullNewFile.returncode != 0: 
        return

    with tempfile.NamedTemporaryFile(mode='w', suffix ='.lua', delete=False) as luaInput:
        luaInput.write(fullNewFile.stdout)
        luaInputPath = luaInput.name

    try:
        funcsJSON = subprocess.run(['parse_lua.lua', luaInputPath],#, input = fullNewFile.stdout,
        capture_output=True, text=True, check=True)
        #parsedFuncs = defaultdict(list, json.loads(funcsJSON.stdout))
        functionJSON = json.loads(funcsJSON.stdout)
    except subprocess.CalledProcessError as e:
        print(f"File not found {file}: {e.stderr}")
    finally: 
        os.remove(luaInputPath)

    # Match hunk changes to function map and update expertise
    for hunk in hunks:
        hunkStart = hunk[0]
        hunkEnd = hunk[0] + hunk[1] - 1

        for functionDefinition in functionJSON['definitions']:
            if functionDefinition['line_start'] <= hunkEnd and functionDefinition['line_end'] >= hunkStart:
                linesChanged = min(hunkEnd, functionDefinition['line_end']) - max(hunkStart, functionDefinition['line_start']) + 1 # either the whole function or a subsection
                expertiseMap[email][date][0].append((functionDefinition['name'], linesChanged))
        for functionCall in functionJSON['calls']:
            if hunkStart <= functionCall['line'] <= hunkEnd:
                expertiseMap[email][date][1].append((functionCall['name'], functionCall['line']))


# 1. Parse log metadata with regex
scriptPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commit_csv.sh")
try:
    logs = subprocess.run([scriptPath], cwd=targetDir, capture_output=True, text=True, check=True)
except subprocess.CalledProcessError:
    sys.exit(1)

currentLog = None
email = None
date = None
currentFile = None
currentLogHunks: list[tuple[int, int]]

for line in logs.stdout.split("\n"):

     # ----------- Begin parsing log ---------------
    commitMatch = re.match(r'^commit ([0-9a-f]{40})', line)
    if commitMatch:
        if currentFile and currentLogHunks:
            extractFunctions(currentLog, currentFile, currentLogHunks, email, date)
            break
        
        currentLog = commitMatch.group(1)
        currentFile = None
        currentLogHunks = []
        continue 

    # Iterate until commit line is found
    if not currentLog:
        continue

    authorMatch = re.match(r'^Author: (.+?) <(.+?)>', line)
    if authorMatch:
        email = authorMatch.group(2)
        continue

    dateMatch = re.match(r'^Date:\s+(.+)', line)
    if dateMatch:
        date = dateMatch.group(1)
        continue

    # Find file change header
    fileMatch = re.match(r'^\+\+\+ b/(.*)', line)
    if fileMatch:
        if currentFile and currentLogHunks:
            extractFunctions(currentLog, currentFile, currentLogHunks, email, date)
            currentLogHunks = []
        currentFile = fileMatch.group(1)
        continue
        
    # Find all hunks for that file change
    hunkMatch = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
    if currentFile and hunkMatch:
        hunkNewStartLine = int(hunkMatch.group(3))
        hunkNewCount = int(hunkMatch.group(4)) if hunkMatch.group(4) else 1
        currentLogHunks.append((hunkNewStartLine, hunkNewCount))

if currentFile and currentLogHunks:
    extractFunctions(currentLog, currentFile, currentLogHunks, email, date)

pprint(expertiseMap)

# Keyed access instead of 0/1:
# expertiseMap = defaultdict(lambda: defaultdict(lambda: {"functionsWorkedOn": [], "functionsCalled": []}))
# expertiseMap[email][date]["functionsWorkedOn"].append((functionName, linesChanged))

