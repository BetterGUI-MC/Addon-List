import json
import os
import re
import urllib.parse

s = "https://ci.codemc.io/job/BetterGUI-MC/view/Addon/job/BungeeLink/101/artifact/target/BungeeLink-3.0.jar"

def to_filename(s: str) -> str:
    new = ""
    for i in range(len(s)):
        c = s[i]
        if c.isupper() and not (i == 0 or s[i - 1].isupper() or s[i - 1] == "-"):
            new += "-" + c.lower()
        else:
            new += c.lower()
    return new


with open("addons.json", "r") as json_file:
    addons = json.load(json_file)

for name, values in addons.items():
    prop = {
        "name": name,
        "description": values["description"],
        "author": values["authors"],
        "code": values["source-code"],
        "wiki": values["wiki"],
        "type": "official"
    }
    link = values["direct-link"]
    link = urllib.parse.unquote(link, encoding='utf-8', errors='replace')
    print(link)
    matcher = re.search(r"https://ci.codemc.io/job/BetterGUI-MC(/view/Addon)?/job/([\s\w_-]+)/.+", link)
    job = matcher.group(2)
    print(job)
    prop["jenkins"] = job

    with open(os.path.join("addons", to_filename(name) + ".json"), "w") as prop_file:
        prop_file.write(json.dumps(prop, indent=2))
