import json
import os


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
        "version": values["version"],
        "description": values["description"],
        "author": values["authors"],
        "code": values["source-code"],
        "download": values["direct-link"],
        "wiki": values["wiki"]
    }

    with open(os.path.join("addons", to_filename(name) + ".json"), "w") as prop_file:
        prop_file.write(json.dumps(prop, indent=2))
