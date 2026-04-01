import json
import os
import argparse
import http.client

parser = argparse.ArgumentParser()
parser.add_argument("--map",         default="expertise_map.json")
parser.add_argument("--out",         default="user_map.json")
parser.add_argument("--repo",         default="Steamodded/smods")
parser.add_argument("--token", required=True)
args = parser.parse_args()

conn = http.client.HTTPSConnection("api.github.com")
headers = {
    "Authorization": "Bearer " + args.token,
    "X-GitHub-Api-Version": "2026-03-10",
    "Accept": "application/vnd.github+json",
    "User-Agent": "smods-recommender",
}

with open(args.map) as expertiseJSON:
    expertiseMap = json.load(expertiseJSON)
if os.path.exists(args.out):
    with open(args.out) as userJSON:
        userMap = json.load(userJSON)
else:
    userMap = {}

if 'emails' not in userMap:
    userMap['emails'] = {}
if 'accounts' not in userMap:
    userMap['accounts'] = {}


def resolveCommit(hash, email):
    conn.request("GET", "/repos/" + args.repo + "/commits/" + hash, headers=headers)

    response = conn.getresponse()
    data = response.read().decode()
    conn.close()

    commit = json.loads(data)
    author = commit["author"]
    if author == None:
        print("WARNING: Unkown account (" + email + "), please resolve manually")
        return "Unk"
    id = str(author["id"])
    if id not in userMap['accounts']:
        login = author["login"]
        url = author["html_url"]
        userMap['accounts'][id] = { 'login': login, 'url': url }
    return id

def saveMap():
    temp = args.out + '.tmp'
    with open(temp, 'w') as tempFile:
        json.dump(userMap, tempFile, indent=2)
    os.replace(temp, args.out)

for key, value in expertiseMap.items():
    if key not in userMap['emails']:
        hash = next(iter(value))
        userMap['emails'][key] = resolveCommit(hash, key)
        saveMap()

