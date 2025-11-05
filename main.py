import asyncio
import json
import re
from pathlib import Path
from urllib.parse import quote
import urllib.request

# Compile pattern once at module level
ARTIFACT_PATTERN = re.compile(r"(.+)-([\d.]+)-shaded\.jar")


class JenkinsAPIError(Exception):
    """Custom exception for Jenkins API related errors."""

    pass


async def read_properties(path):
    """Read and parse a JSON properties file asynchronously.

    Args:
        path: Path to the JSON file

    Returns:
        Dictionary containing the properties

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(None, path.read_text, "utf-8")
        return json.loads(content)
    except FileNotFoundError:
        print(f"Error: File not found: {path}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}")
        raise


async def read_folder(path):
    """Read all JSON property files from a folder asynchronously.

    Args:
        path: Path to the folder containing property files

    Returns:
        List of dictionaries containing properties from each file
    """
    folder_path = Path(path)

    if not folder_path.exists():
        print(f"Warning: Folder not found: {path}")
        return []

    json_files = [
        f for f in folder_path.iterdir() if f.is_file() and f.suffix == ".json"
    ]

    # Read all files concurrently
    tasks = [read_properties(file) for file in json_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    properties_arr = []
    for file, result in zip(json_files, results):
        if isinstance(result, Exception):
            print(f"Error reading {file}: {result}")
        else:
            properties_arr.append(result)

    return properties_arr


async def fetch_from_official(jenkins_name):
    """Fetch version and download URL from Jenkins CI asynchronously.

    Args:
        jenkins_name: Name of the Jenkins job

    Returns:
        Tuple of (version, artifact_url)

    Raises:
        JenkinsAPIError: If unable to fetch or parse Jenkins data
    """
    api_url = f"https://ci.codemc.io/job/BetterGUI-MC/job/{quote(jenkins_name)}/api/json?tree=builds[url]"
    print(f"Jenkins URL: {api_url}")

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: urllib.request.urlopen(api_url, timeout=30)
        )
        data = response.read().decode('utf-8')
        api_res = json.loads(data)
    except urllib.error.URLError as e:
        raise JenkinsAPIError(f"Failed to fetch Jenkins API: {e}")
    except json.JSONDecodeError as e:
        raise JenkinsAPIError(f"Invalid JSON response from Jenkins: {e}")

    build_urls = [build["url"] for build in api_res.get("builds", [])]

    if not build_urls:
        raise JenkinsAPIError("No builds found")

    for build_url in build_urls:
        normalized_build_url = build_url.rstrip("/")
        build_api_url = (
            f"{normalized_build_url}/api/json?tree=artifacts[fileName,relativePath]"
        )
        print(f"Build URL: {build_api_url}")

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: urllib.request.urlopen(build_api_url, timeout=30)
            )
            data = response.read().decode('utf-8')
            build_res = json.loads(data)
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to fetch build {build_url}: {e}")
            continue

        artifacts = build_res.get("artifacts", [])

        for artifact in artifacts:
            file_name = artifact.get("fileName", "")
            relative_path = artifact.get("relativePath", "")
            matcher = ARTIFACT_PATTERN.search(file_name)

            if matcher:
                version = matcher.group(2)
                artifact_url = f"{normalized_build_url}/artifact/{relative_path}"
                print(f"Found: {file_name}")
                return version, artifact_url

    raise JenkinsAPIError("No valid artifact found in any build")


async def convert(
    properties,
    file_extension = ".jar",
):
    """Convert properties to the output format asynchronously.

    Args:
        properties: Dictionary containing addon properties
        file_extension: File extension to append to the name

    Returns:
        Tuple of (name, values_dict)
    """
    prop_name = properties.get("name", "Unknown")
    name = prop_name
    print(f"Processing {name}")

    values = {
        "file-name": name + file_extension,
        "description": properties.get("description", ""),
        "authors": properties.get("author", ""),
        "source-code": properties.get("code", ""),
        "wiki": properties.get("wiki", ""),
    }

    prop_type = properties.get("type", "")

    if prop_type == "official":
        jenkins_name = properties.get("jenkins")
        if not jenkins_name:
            print(f"Warning: No Jenkins name specified for {name}")
            values["version"] = "unknown"
            values["direct-link"] = ""
        else:
            try:
                version, download_link = await fetch_from_official(jenkins_name)
                values["version"] = version
                values["direct-link"] = download_link
            except JenkinsAPIError as e:
                print(f"Error fetching from Jenkins for {name}: {e}")
                values["version"] = "unknown"
                values["direct-link"] = ""
    else:
        values["version"] = properties.get("version", "unknown")
        values["direct-link"] = properties.get("download", "")

    print(f"Completed {name}")
    return name, values


async def write(path, properties_dict):
    """Write properties dictionary to a JSON file asynchronously.

    Args:
        path: Output file path
        properties_dict: Dictionary to write
    """
    try:
        loop = asyncio.get_event_loop()
        json_str = json.dumps(
            properties_dict, separators=(",", ":"), ensure_ascii=False
        )
        await loop.run_in_executor(None, Path(path).write_text, json_str, "utf-8")
        print(f"\nSuccessfully wrote to {path}")
    except IOError as e:
        print(f"Error writing to {path}: {e}")
        raise


async def process_all_addons(properties_list):
    """Process all addons concurrently and merge results.

    Args:
        properties_list: List of addon properties

    Returns:
        Dictionary with all processed addons merged
    """
    # Process all addons concurrently
    tasks = [convert(properties) for properties in properties_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge results
    converted = {}
    for result in results:
        if isinstance(result, Exception):
            print(f"Error converting addon: {result}")
        else:
            name, values = result
            converted[name] = values

    return converted


async def main():
    """Main function to process addons and generate output JSON asynchronously."""
    print("Starting async addon processing...\n")

    # Read all property files
    properties_list = await read_folder("addons")

    if not properties_list:
        print("No addon properties found. Exiting.")
        return

    print(f"Found {len(properties_list)} addon(s) to process\n")

    # Process all addons concurrently
    converted = await process_all_addons(properties_list)

    if converted:
        await write("addons.json", converted)
        print(f"\nProcessed {len(converted)} addon(s) successfully")
    else:
        print("No addons were successfully processed.")


if __name__ == "__main__":
    asyncio.run(main())
