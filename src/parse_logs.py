import csv
import os
import subprocess
import json
import re
import tempfile
from pprint import pprint
from collections import defaultdict

# 1. Extract commit history from logs
# 2. For each (complete) file in the commit, extract functions
# 3. Map hunk changes to functions and add them to developer expertise map under their date

# Expertise map: {author(email) : {date : [functionsWorkedOn[(func_name, lines_worked_on)], functionsCalled[(func_name, line_called)]}}
# email mapped to date, date mapped to a 2-list of lists of 2-tuples

# Parse Logs i) run log script -> ii) regex matching
targetDir = "../../smods"

expertiseMap: defaultdict[str, defaultdict[str, list]]
expertiseMap = defaultdict(lambda: defaultdict(lambda: [[], []]))

# Update function expertise values for a file change in a commit
def extractFunctions(log, file, hunks, email, date):

    # Extract functions from a file corresponding to a change hunk
    functionJSON: defaultdict[str, list[dict[str, int | str]]]

    try:
        funcsJSON = subprocess.run(['./parse_log_file.sh', targetDir, f'{log}:{file}'],
        capture_output=True, text=True, check=True)
        functionJSON = json.loads(funcsJSON.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Child process error {file}: {e.stderr}")
        print(f"File: {file}, Hash: {log}")

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

# Helper function for printing the final expertise map
def defaultdict_to_dict(d):
    if isinstance(d, defaultdict):
        d = {k: defaultdict_to_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        d = [defaultdict_to_dict(i) for i in d]
    elif isinstance(d, tuple):
        d = list(d)
    return d

# Parse log metadata with regex
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

counter = 0
for line in logs.stdout.split("\n"):
    
    if counter >= 50:
        break
    commitMatch = re.match(r'^commit ([0-9a-f]{40})', line)
    if commitMatch:
        if currentFile and currentLogHunks:
            extractFunctions(currentLog, currentFile, currentLogHunks, email, date)
            
        currentLog = commitMatch.group(1)
        currentFile = None
        currentLogHunks = []
        counter += 1
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

with open("expertise_map.json", "w") as f:
    json.dump(defaultdict_to_dict(expertiseMap), f, indent=2)
# Keyed access instead of 0/1:
# expertiseMap = defaultdict(lambda: defaultdict(lambda: {"functionsWorkedOn": [], "functionsCalled": []}))
# expertiseMap[email][date]["functionsWorkedOn"].append((functionName, linesChanged))

