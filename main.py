import json
import os
import re
import urllib.request as request
import urllib.parse as parse

pattern = re.compile(r"(.+)-([\d.]+)-shaded\.jar")


def read_properties(path: str) -> dict:
    with open(path, "r") as file:
        return json.load(file)


def read_folder(path: str) -> list[dict]:
    properties_arr = []
    for file in os.listdir(path):
        properties = read_properties(os.path.join(path, file))
        properties_arr.append(properties)
    return properties_arr


def fetch_from_official(jenkins_name: str) -> (str, str):
    api_url = f"https://ci.codemc.io/job/BetterGUI-MC/job/{parse.quote(jenkins_name)}/api/json?tree=builds[url]"
    print(f"Jenkins URL: {api_url}")
    api_res = json.load(request.urlopen(api_url))
    build_urls = [build["url"] for build in api_res["builds"]]
    for build_url in build_urls:
        normalized_build_url = build_url[0:-1] if build_url.endswith("/") else build_url
        build_api_url = f"{normalized_build_url}/api/json?tree=artifacts[fileName,relativePath]"
        print(f"Build URL: {build_api_url}")
        build_res = json.load(request.urlopen(build_api_url))
        artifacts = build_res["artifacts"]
        for artifact in artifacts:
            file_name = artifact["fileName"]
            relative_path = artifact["relativePath"]
            matcher = re.search(pattern, file_name)
            try:
                version = matcher.group(2)
                artifact_url = f"{normalized_build_url}/artifact/{relative_path}"
                print(f"Found: {file_name}")
                return version, artifact_url
            except:
                continue
    raise Exception("No download link & version found")


def convert(properties: dict, file_extension: str = ".jar") -> (str, dict):
    prop_name = properties["name"]
    name = prop_name
    print(f"Adding {name}")
    values = {
        "file-name": name + file_extension,
        "description": properties["description"],
        "authors": properties["author"],
        "source-code": properties["code"],
        "wiki": properties["wiki"]
    }

    prop_type = properties["type"] if "type" in properties else ""
    if prop_type == "official":
        jenkins_name = properties["jenkins"]
        version, download_link = fetch_from_official(jenkins_name)
        values["version"] = version
        values["direct-link"] = download_link
    else:
        values["version"] = properties["version"]
        values["direct-link"] = properties["download"]

    return name, values


def write(path: str, properties_dict: dict):
    with open(path, "w") as file:
        json_str = json.dumps(properties_dict, separators=(",", ":"))
        file.write(json_str)


def main():
    arr = read_folder("addons")
    converted = {}
    for properties in arr:
        name, values = convert(properties)
        converted[name] = values
    write("addons.json", converted)


if __name__ == '__main__':
    main()
