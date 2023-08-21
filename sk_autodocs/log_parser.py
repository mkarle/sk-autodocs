from typing import Dict, List
import json
import re


def parse_dotnet_build_log(path: str, output_file: str) -> Dict[str, List[str]]:
    with open(path, "r") as f:
        lines = f.readlines()

    # Get all the paths
    paths = {}
    for line in lines:
        if (
            "warning CS1591: Missing XML comment for publicly visible type or member"
            not in line
        ):
            continue
        # Get the path, split at "(number,number)" and take the first part
        path = re.split("\(\d+,\d+\)", line)[0].strip()
        # Get the member split at "member '" and "' ["
        member = re.split("member '", line)[1].split("' [")[0].strip()
        # Add to dictionary
        if path not in paths:
            paths[path] = []
        paths[path].append(member)
    for path, members in paths.items():
        paths[path] = list(set(members))
    if output_file is None:
        return paths
    # Write to file
    with open(output_file, "w") as f:
        f.write(json.dumps(paths))
