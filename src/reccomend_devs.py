import json
import math
import argparse
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from collections import defaultdict

# Compute time decay
def getDecay(dateStr, windowDays):
    try:
        commitDate = parsedate_to_datetime(dateStr)
        daysAgo = max((datetime.now(timezone.utc) - commitDate).total_seconds() / 86400, 0)
    except Exception:
        return 1.0
    return max(0.0, 1.0 - daysAgo / windowDays)

def scoreDeveloper(changeHistory, queryFuncs, modWeight, callWeight):
    totalScore = 0.0
    expertise = defaultdict(lambda: {"totalHits": 0, "modScore": 0.0, "callScore": 0.0})

    for dateStr, (modDict, callDict) in changeHistory.items():
        timeDecay = getDecay(dateStr, 100)

        for func in queryFuncs:
            linesChanged = modDict.get(func, 0)
            calls = callDict.get(func, 0)
            if not linesChanged and not calls:
                continue

            expertise[func]["totalHits"] += 1
            expertise[func]["modScore"]  += modWeight  * linesChanged * timeDecay
            expertise[func]["callScore"] += callWeight * calls * timeDecay
            
            totalScore += (modWeight * linesChanged + callWeight * calls) * timeDecay

    return totalScore, dict(expertise)

def printResults(rankedList, queryFuncs, topN):

    if not rankedList:
        print("No developers found.")
        return
    print(f"Top {min(topN, len(rankedList))} of {len(rankedList)} developers\n")

    for rank, (email, score, expertise) in enumerate(rankedList[:topN], 1):
        print(f"#{rank} {email}  score: {score:.2f}")
        for func, detail in expertise.items():
            print(f"   {func}: commits={detail['totalHits']}, modifications={detail['modScore']:.2f}, calls={detail['callScore']:.2f}")
        print()

parser = argparse.ArgumentParser()
parser.add_argument("functions", nargs="+", metavar="FUNC")
parser.add_argument("--map",         default="expertise_map.json")
parser.add_argument("--top",         type=int,   default=5)
parser.add_argument("--mod-weight",  type=float, default=2.0) 
parser.add_argument("--call-weight", type=float, default=1.0)
args = parser.parse_args()

with open(args.map) as expertiseJSON:
    expertiseMap = json.load(expertiseJSON)

queryFuncs = set(args.functions)
results = []

for email, changeHistory in expertiseMap.items():
    score, expertise = scoreDeveloper(changeHistory, queryFuncs, args.mod_weight, args.call_weight)
    if score > 0:
        results.append((email, score, expertise))

results.sort(key=lambda x: x[1], reverse=True)
printResults(results, args.functions, args.top)