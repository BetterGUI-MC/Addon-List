import json
import os

import javaproperties


def read_properties(path: str) -> dict:
    with open(path, "r") as file:
        return javaproperties.load(file)


def read_folder(path: str) -> list[dict]:
    properties_arr = []
    for file in os.listdir(path):
        properties = read_properties(os.path.join(path, file))
        properties_arr.append(properties)
    return properties_arr


def convert(properties: dict, file_extension: str = ".jar") -> (str, dict):
    name = ""
    values = {}

    prop_name = properties["NAME"]
    name = prop_name
    values["file-name"] = name + file_extension

    values["version"] = properties["VERSION"]
    values["description"] = properties["DESCRIPTION"]
    values["authors"] = [author.strip() for author in properties["AUTHOR"].split(",")]
    values["source-code"] = properties["CODE"]
    values["direct-link"] = properties["DOWNLOAD"]
    values["wiki"] = properties["WIKI"]

    return name, values


def write(path: str, properties_dict: dict):
    with open(path, "w") as file:
        json_str = json.dumps(properties_dict)
        file.write(json_str)


def main():
    arr = read_folder("addons")
    converted = {}
    for properties in arr:
        name, values = convert(properties)
        converted[name] = values
    write("addons_new.json", converted)


if __name__ == '__main__':
    main()
