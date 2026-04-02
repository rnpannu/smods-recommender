import json
import math
import argparse
import sys
import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from collections import defaultdict
userMapFile = "user_map.json"

# Compute time decay
def getDecay(dateStr, windowDays):
    try:
        commitDate = parsedate_to_datetime(dateStr)
        daysAgo = max((datetime.now(timezone.utc) - commitDate).total_seconds() / 86400, 0)
    except Exception:
        return 1.0
    return max(0.0, 1.0 - daysAgo / windowDays)

def scoreDeveloper(changeHistory, queryFuncs, modWeight, callWeight, decayWindow):
    totalScore = 0.0
    expertise = defaultdict(lambda: {'totalHits': 0, 'modScore': 0.0, 'callScore': 0.0, 'decay' : 0.0})

    for log, entry in changeHistory.items():

        timeDecay = getDecay(entry['date'], decayWindow)

        modDict = {normalizeName(funcKey): value for funcKey, value in entry['definitions'].items()}
        callDict = {normalizeName(funcKey): value for funcKey, value in entry['calls'].items()}

        for func in queryFuncs:
            linesChanged = modDict.get(func, 0)
            calls = callDict.get(func, 0)
            if not linesChanged and not calls:
                continue

            expertise[func]['totalHits'] += 1
            expertise[func]['modScore']  += modWeight  * linesChanged * timeDecay
            expertise[func]['callScore'] += callWeight * calls * timeDecay
            expertise[func]['decay'] += timeDecay
            
            totalScore += (modWeight * linesChanged + callWeight * calls) * timeDecay

    return totalScore, dict(expertise)

# NEW --------------------
def expDecay(dateStr, halfLifeDays):
    try:
        commitDate = parsedate_to_datetime(dateStr)
        daysAgo = max(
            (datetime.now(timezone.utc) - commitDate).total_seconds() / 86400,
            0
        )
    except Exception:
        return 1.0
    return math.exp(-daysAgo / halfLifeDays)

def scoreDeveloperBetter(changeHistory, queryFuncs, modWeight, callWeight, decayWindow, diversityWeight, consistencyWeight):
    totalScore = 0.0
    # func : {hits, mod, calls}
    expertise = defaultdict(lambda: {'totalHits': 0, 'modScore': 0.0, 'callScore': 0.0, 'decay': 0.0})
    avgDecay = 0
    counter = 0
    for entry in changeHistory.values():

        timeDecay = expDecay(entry['date'], decayWindow)
        avgDecay += timeDecay
        counter += 1
        modDict = {normalizeName(funcKey): value for funcKey, value in entry['definitions'].items()}
        callDict = {normalizeName(funcKey): value for funcKey, value in entry['calls'].items()}

        for func in queryFuncs:
            linesChanged = modDict.get(func, 0)
        
            calls = callDict.get(func, 0)
            if not linesChanged and not calls:
                continue

            expertise[func]['totalHits'] += 1
            expertise[func]['modScore']  += modWeight  * linesChanged * timeDecay
            expertise[func]['callScore'] += callWeight * calls * timeDecay
            expertise[func]['decay'] += timeDecay
            #totalScore += (modWeight * linesChanged + callWeight * calls) * timeDecay
    
    
    if not expertise:
        return 0.0, {}

    baseScore = sum(d['modScore'] + d['callScore'] for d in expertise.values())

    # Diversity bonus for number of functions interacted with
    numCovered = len(expertise) 
    diversityMultiplier = 1.0 + diversityWeight * (numCovered - 1)

    consistencyBonus = sum(
        math.log1p(d['totalHits']) * consistencyWeight #log(1 + commits) x weight
        for d in expertise.values()
    )
 
    totalScore = baseScore * diversityMultiplier + consistencyBonus
    return totalScore,  dict(expertise)

def printResults(rankedList, queryFuncs, topN):

    if not rankedList:
        print('No developers found.')
        return
    print(f'Top {min(topN, len(rankedList))} of {len(rankedList)} developers\n')

    for rank, (email, score, expertise) in enumerate(rankedList[:topN], 1):
        print(f"#{rank} {email}  score: {score:.2f}")
        for func, detail in expertise.items():
            print(f"   {func}: commits={detail['totalHits']}, modifications={detail['modScore']:.2f}, calls={detail['callScore']:.2f}, decay={detail['decay']:.2f}")
        print()

def normalizeName(name):
    return name.replace(':', '.')

if os.path.exists(userMapFile):
    with open(userMapFile, 'r') as f:
        userMap: dict = json.load(f)
else:
    userMap = {}

def doStuff(map, functions, simple, mod_weight, call_weight, decay_window, diversity_weight, consistency_weight, prettyNames):
    with open(map) as expertiseJSON:
        expertiseMap = json.load(expertiseJSON)

    queryFuncs = {normalizeName(funcName) for funcName in functions}

    results = {}
    for email, changeHistory in expertiseMap.items():
        if simple:
            score, expertise = scoreDeveloper(changeHistory,
            queryFuncs,
            mod_weight,
            call_weight, 
            decay_window, )
        else: 
            score, expertise = scoreDeveloperBetter(changeHistory,
            queryFuncs,
            mod_weight,
            call_weight, 
            decay_window, 
            diversity_weight, 
            consistency_weight)

        if score > 0:
            #authorId = userMap['emails'].get(email, "33164598")
            authorId = userMap['emails'].get(email, email)
            author   = userMap['accounts'].get(authorId, {}).get('login', email)
            if not prettyNames:
                author = authorId
            
            if author in results:
                prevScore, prevExpertise = results[author]
                for func, detail in expertise.items():
                    if func in prevExpertise:
                        prevExpertise[func]['totalHits'] += detail['totalHits']
                        prevExpertise[func]['modScore']  += detail['modScore']
                        prevExpertise[func]['callScore'] += detail['callScore']
                    else:
                        prevExpertise[func] = detail
                results[author] = (prevScore + score, prevExpertise)
            else:
                results[author] = (score, expertise)

    results = sorted(
        [(author, score, expertise) for author, (score, expertise) in results.items()],
        key=lambda x: x[1], reverse=True)
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("functions", nargs="+", metavar="FUNC")
    parser.add_argument("--map",         default="expertise_map.json")
    parser.add_argument("--top",         type=int,   default=5)
    parser.add_argument("--mod-weight",  type=float, default=2.0) 
    parser.add_argument("--call-weight", type=float, default=1.0)
    parser.add_argument("--decay-window",     type=float, default=720.0) # number of days until 2/3 of value
    parser.add_argument("--diversity-weight", type=float, default=0.25)
    parser.add_argument("--consistency-weight", type=float, default=10.0)
    parser.add_argument("--simple", action="store_true")
    args = parser.parse_args()

    results = doStuff(args.map, args.functions, args.simple, args.mod_weight, args.call_weight, args.decay_window, args.diversity_weight, args.consistency_weight, True)
    printResults(results, args.functions, args.top)
