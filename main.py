#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx[http2]",
# ]
# ///

import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote
import httpx

# Compile pattern once at module level
ARTIFACT_PATTERN = re.compile(r"(.+)-([\d.]+)-shaded\.jar")

# Semaphore to prevent hitting the Jenkins server with too many concurrent connections.
# This keeps the crawler highly stable and avoids transient connection timeouts or rate-limiting.
CONCURRENCY_LIMIT = 8
jenkins_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)


class JenkinsAPIError(Exception):
    """Custom exception for Jenkins API related errors."""
    pass


async def read_properties(path: Path) -> dict:
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
        content = await asyncio.to_thread(path.read_text, encoding="utf-8")
        return json.loads(content)
    except FileNotFoundError:
        print(f"Error: File not found: {path}", file=sys.stderr)
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}", file=sys.stderr)
        raise


async def read_folder(path_str: str) -> list[dict]:
    """Read all JSON property files from a folder asynchronously.

    Args:
        path_str: Path to the folder containing property files

    Returns:
        List of dictionaries containing properties from each file
    """
    folder_path = Path(path_str)

    if not folder_path.exists():
        print(f"Warning: Folder not found: {path_str}", file=sys.stderr)
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
            print(f"Error reading {file}: {result}", file=sys.stderr)
        else:
            properties_arr.append(result)

    return properties_arr


async def fetch_from_official(client: httpx.AsyncClient, jenkins_name: str) -> tuple[str, str]:
    """Fetch version and download URL from Jenkins CI asynchronously.

    Queries only the last successful build in a single network call.
    Raises JenkinsAPIError if the job has no successful build or valid shaded jar artifact.

    Args:
        client: httpx AsyncClient instance
        jenkins_name: Name of the Jenkins job

    Returns:
        Tuple of (version, artifact_url)

    Raises:
        JenkinsAPIError: If unable to fetch or parse Jenkins data
    """
    quoted_name = quote(jenkins_name)
    direct_url = f"https://ci.codemc.io/job/BetterGUI-MC/job/{quoted_name}/lastSuccessfulBuild/api/json?tree=artifacts[fileName,relativePath],url"
    print(f"Jenkins Direct URL: {direct_url}")
    
    async with jenkins_semaphore:
        try:
            response = await client.get(direct_url, timeout=15.0)
            if response.status_code == 200:
                build_res = response.json()
                build_url = build_res.get("url", "").rstrip("/")
                artifacts = build_res.get("artifacts", [])
                
                for artifact in artifacts:
                    file_name = artifact.get("fileName", "")
                    relative_path = artifact.get("relativePath", "")
                    matcher = ARTIFACT_PATTERN.search(file_name)
                    
                    if matcher:
                        version = matcher.group(2)
                        artifact_url = f"{build_url}/artifact/{relative_path}"
                        print(f"Found: {file_name}")
                        return version, artifact_url
            
            raise JenkinsAPIError(f"HTTP {response.status_code} or no valid shaded jar artifact found")
        except Exception as e:
            if isinstance(e, JenkinsAPIError):
                raise
            raise JenkinsAPIError(f"Request failed: {e}")


async def convert(
    client: httpx.AsyncClient,
    properties: dict,
    file_extension: str = ".jar",
) -> tuple[str, dict] | None:
    """Convert properties to the output format asynchronously.

    Args:
        client: httpx AsyncClient instance
        properties: Dictionary containing addon properties
        file_extension: File extension to append to the name

    Returns:
        Tuple of (name, values_dict) or None if ignored
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
            print(f"Warning: No Jenkins name specified for official addon {name}. Ignoring addon.", file=sys.stderr)
            return None
        else:
            try:
                version, download_link = await fetch_from_official(client, jenkins_name)
                values["version"] = version
                values["direct-link"] = download_link
            except JenkinsAPIError as e:
                print(f"Warning: Failed to fetch successful build for official addon {name}: {e}. Ignoring addon.", file=sys.stderr)
                return None
    else:
        values["version"] = properties.get("version", "unknown")
        values["direct-link"] = properties.get("download", "")

    print(f"Completed {name}")
    return name, values


async def write(path_str: str, properties_dict: dict):
    """Write properties dictionary to a JSON file asynchronously.

    Args:
        path_str: Output file path
        properties_dict: Dictionary to write
    """
    try:
        json_str = json.dumps(
            properties_dict, separators=(",", ":"), ensure_ascii=False
        )
        await asyncio.to_thread(Path(path_str).write_text, json_str, encoding="utf-8")
        print(f"\nSuccessfully wrote to {path_str}")
    except IOError as e:
        print(f"Error writing to {path_str}: {e}", file=sys.stderr)
        raise


async def process_all_addons(client: httpx.AsyncClient, properties_list: list[dict]) -> dict:
    """Process all addons concurrently and merge results.

    Args:
        client: httpx AsyncClient instance
        properties_list: List of addon properties

    Returns:
        Dictionary with all processed addons merged
    """
    tasks = [convert(client, properties) for properties in properties_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    converted = {}
    for result in results:
        if isinstance(result, Exception):
            print(f"Error converting addon: {result}", file=sys.stderr)
        elif result is not None:
            name, values = result
            converted[name] = values

    # Sort dictionary alphabetically by keys (addon names)
    return dict(sorted(converted.items()))


async def main():
    """Main function to process addons and generate output JSON asynchronously."""
    print("Starting async addon processing...\n")

    # Read all property files
    properties_list = await read_folder("addons")

    if not properties_list:
        print("No addon properties found. Exiting.", file=sys.stderr)
        return

    print(f"Found {len(properties_list)} addon(s) to process\n")

    # Enable HTTP2 support for faster multiplexing
    limits = httpx.Limits(max_keepalive_connections=15, max_connections=40)
    async with httpx.AsyncClient(http2=True, limits=limits) as client:
        converted = await process_all_addons(client, properties_list)

    if converted:
        await write("addons.json", converted)
        print(f"\nProcessed {len(converted)} addon(s) successfully")
    else:
        print("No addons were successfully processed.", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
