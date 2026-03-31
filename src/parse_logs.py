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

targetDir = '../../smods'
expertiseMapFile = 'expertise_map.json'

if os.path.exists(expertiseMapFile):
    with open(expertiseMapFile, 'r') as f:
        expertiseMap: dict = json.load(f)
else:
    expertiseMap = {}
    # expertiseMap: defaultdict[str, defaultdict[str, list]]
    # expertiseMap = defaultdict(lambda: defaultdict(lambda: [str, {}, {}]))

# Update function expertise values for a file change in a commit
def extractFunctions(log, email, date, file, hunks):
    if not file.endswith('.lua'):
            return
    
    # Extract functions from a file corresponding to a change hunk
    functionJSON: defaultdict[str, list[dict[str, int | str]]]

    try:
        funcsJSON = subprocess.run(['./parse_log_file.sh', targetDir, f'{log}:{file}'],
        capture_output=True, text=True, check=True)
        functionJSON = json.loads(funcsJSON.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Child process error {file}: {e.stderr}")
        print(f"File: {file}, Hash: {log}")

    # {'email' : {'hash' : {'date' : '', 'definitions': {}, 'calls'}}}
    entry = expertiseMap.setdefault(email, {}).setdefault(log, {'date': date, 'definitions': {}, 'calls': {}})

    entry["date"] = date 

    definitions = entry['definitions']
    calls       = entry['calls']
    # Match hunk changes to function map and update expertise
    for hunk in hunks:
        hunkStart = hunk[0]
        hunkEnd = hunk[0] + hunk[1] - 1

        for funcDef in functionJSON.get('definitions', []):
            if funcDef['line_start'] <= hunkEnd and funcDef['line_end'] >= hunkStart:
                funcName = funcDef['name']
                linesChanged = min(hunkEnd, funcDef['line_end']) - max(hunkStart, funcDef['line_start']) + 1 # either the whole function or a subsection
                definitions[funcName] = definitions.get(funcName, 0) + linesChanged
                    
        for functionCall in functionJSON.get('calls', []):
            if hunkStart <= functionCall['line'] <= hunkEnd:
                funcName = functionCall['name']
                calls[funcName] = calls.get(funcName, 0) + 1


def saveMap(log):
    if log and log not in processedCommits:
        temp = expertiseMapFile + '.tmp'
        with open(temp, 'w') as tempFile:
            json.dump(expertiseMap, tempFile, indent=2)
        os.replace(temp, expertiseMapFile)
        processedCommits.add(currentLog)

def appendFileChanges(log, email, date, file, hunks):
    if log and email and date and file and hunks:
        extractFunctions(log, email, date, file, hunks)

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
scriptPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'commit_csv.sh')
try:
    logs = subprocess.run([scriptPath], cwd=targetDir, capture_output=True, text=True, check=True)
except subprocess.CalledProcessError:
    sys.exit(1)

currentLog: str | None = None
currentLogEmail: str | None = None
currentLogDate: str | None = None
currentFile: str | None = None
currentLogHunks: list[tuple[int, int]] = []

processedCommits: set[str] = set()
for hashes in expertiseMap.values():
    processedCommits.update(hashes.keys())

counter = 0
for line in logs.stdout.split('\n'):
    
    if counter > 10:
        break
    commitMatch = re.match(r'^commit ([0-9a-f]{40})', line)
    if commitMatch:
        appendFileChanges(currentLog, currentLogEmail, currentLogDate, currentFile, currentLogHunks)
        saveMap(currentLog)

        currentLog = commitMatch.group(1)
        currentFile = None
        currentLogHunks = []

        if currentLog in processedCommits:
            currentLog = None
        
        counter += 1
        continue 
    # Iterate until commit line is found
    if not currentLog:
        continue

    authorMatch = re.match(r'^Author: (.+?) <(.+?)>', line)
    if authorMatch:
        currentLogEmail = authorMatch.group(2)
        continue

    dateMatch = re.match(r'^Date:\s+(.+)', line)
    if dateMatch:
        currentLogDate = dateMatch.group(1)
        continue

    # Find file change header
    fileMatch = re.match(r'^\+\+\+ b/(.*)', line)
    if fileMatch:
        appendFileChanges(currentLog, currentLogEmail, currentLogDate, currentFile, currentLogHunks)
        currentLogHunks = []
        currentFile = fileMatch.group(1)
        continue
        
    # Find all hunks for that file change
    hunkMatch = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
    if currentFile and hunkMatch:
        hunkNewStartLine = int(hunkMatch.group(3))
        hunkNewCount = int(hunkMatch.group(4)) if hunkMatch.group(4) else 1
        currentLogHunks.append((hunkNewStartLine, hunkNewCount))

appendFileChanges(currentLog,  currentLogEmail, currentLogDate, currentFile, currentLogHunks)
saveMap(currentLog)

# Keyed access instead of 0/1:
# expertiseMap = defaultdict(lambda: defaultdict(lambda: {"functionsWorkedOn": [], "functionsCalled": []}))
# expertiseMap[email][date]["functionsWorkedOn"].append((functionName, linesChanged))
