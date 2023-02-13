import json
import os


def read_properties(path: str) -> dict:
    with open(path, "r") as file:
        return json.load(file)


def read_folder(path: str) -> list[dict]:
    properties_arr = []
    for file in os.listdir(path):
        properties = read_properties(os.path.join(path, file))
        properties_arr.append(properties)
    return properties_arr


def convert(properties: dict, file_extension: str = ".jar") -> (str, dict):
    prop_name = properties["name"]
    name = prop_name
    values = {
        "file-name": name + file_extension,
        "version": properties["version"],
        "description": properties["description"],
        "authors": properties["author"],
        "source-code": properties["code"],
        "direct-link": properties["download"],
        "wiki": properties["wiki"]
    }

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
