import sys
import requests
import json
import time
import re
from pathlib import Path
from pprint import pprint
from datetime import datetime

SLEEP_SECONDS=2
# the file contains repositories need to be convered by this script
REPO_NAME_LIST_FILE='repo_name_list.txt'
SINCEDATE='2024-02-01'
LABLES_TO_IGNORE=[
        'HappyOpenSource Pro',
        'HappyOpenSource',
        'PaddlePaddle Hackathon',
        'Announcement',
        ]
# controls how many to display in the final matrix
COLUMNS=5
ROWS=10
# github token
TOKEN=None
# to get a token, Go to github.com Settings -> Developer Settings -> Personal Access Tokens
# and generate a token with public_repo access.
# and add this token to your '~/.gh_tokenrc' configuration:
# github_oauth = <YOUR_GITHUB_TOKEN>

def get_ghstack_token():
    pattern = 'github_oauth = (.*)'
    with open(Path('~/.gh_tokenrc').expanduser(), 'r+') as f:
        config = f.read()
    matches = re.findall(pattern, config)
    if len(matches) == 0:
        raise RuntimeError("Can't find a github oauth token")
    return matches[0]

if TOKEN is None: TOKEN = get_ghstack_token()

# headers to setup github token, otherwise, will reach rate limit very soon
headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f"token {TOKEN}",
        }

# read repo names from the external file, so the order of repos is fixed
with open(REPO_NAME_LIST_FILE, "r") as f:
    repos = f.read().rstrip().split("\n")

# for debug purpose
#repos=['Paddle', 'PaddleNLP', 'PaddleScience', 'PaddleOCR', 'docs']
print(repos, file=sys.stderr)

repo_all_issue_count={}
repo_closed_issue_count={}

ignore_labels_part=''.join(map(lambda x:f"-label:\"{x}\"", LABLES_TO_IGNORE))
for repo in repos:
    closed_issue_url = f"https://api.github.com/search/issues?q=repo:PaddlePaddle/{repo}+is:closed+type:issue+created:>={SINCEDATE}+{ignore_labels_part}"
    data = requests.get(closed_issue_url, headers=headers).json()
    pprint(data, stream=sys.stderr)
    closed_issue_count = data['total_count']
    # take a nap to lower github server load
    time.sleep(SLEEP_SECONDS)


    all_issue_url = f"https://api.github.com/search/issues?q=repo:PaddlePaddle/{repo}+type:issue+created:>={SINCEDATE}+{ignore_labels_part}"
    data = requests.get(all_issue_url, headers=headers).json()
    pprint(data, stream=sys.stderr)
    all_issue_count = data['total_count']
    # take a nap to lower github server load
    time.sleep(SLEEP_SECONDS)

    print(f"{repo}: {closed_issue_count}/{all_issue_count}", file=sys.stderr)
    repo_all_issue_count[repo] = all_issue_count
    repo_closed_issue_count[repo] = closed_issue_count

sorted_repos = list(dict(sorted(repo_all_issue_count.items(), key=lambda x: x[1], reverse=True)).keys())

print(f"- issues since: {SINCEDATE}")
today = datetime.today().strftime('%Y-%m-%d')
print(f"- executed at: {today}")
print(f"- issues ignored with labels: {'; '.join(LABLES_TO_IGNORE)}")

for row in range(ROWS):
    start = row * COLUMNS
    end = start + COLUMNS

    repo_with_links = map(lambda x:f"[{x}](https://github.com/PaddlePaddle/{x}/issues?q=is%3Aissue+created%3A%3E%3D{SINCEDATE})", sorted_repos[start:end])
    print('| ' + ' | '.join(repo_with_links) + ' |')
    if row == 0: print('| ---- ' * COLUMNS + '|')
    def fmt_cell(x):
        c = repo_closed_issue_count[x]
        a = repo_all_issue_count[x]
        r = 0.
        if a > 0: r = c/a * 100.

        return "{}/{}({:.2f}%)".format(c, a, r)

    issue_counts = map(fmt_cell, sorted_repos[start:end])
    print('| ' + ' | '.join(issue_counts) + ' |')
