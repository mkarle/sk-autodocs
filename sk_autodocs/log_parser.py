from typing import Dict, List
import json
import re


def parse_dotnet_build_log(path: str, output_file: str = None) -> Dict[str, List[str]]:
    """
    Parse a .NET build log file to find missing XML comments for publicly visible types or members.
    
    This function reads a .NET build log file, extracts the paths and members with missing XML comments,
    and returns a dictionary with the paths as keys and a list of members as values. Optionally, the
    dictionary can be written to a JSON file.

    Args:
        path (str): The path to the .NET build log file.
        output_file (str, optional): The path to the output JSON file. If not provided, the function
                                      will return the dictionary without writing to a file.

    Returns:
        Dict[str, List[str]]: A dictionary with paths as keys and a list of members with missing
                              XML comments as values.

    Example:
        >>> log_path = "path/to/build.log"
        >>> output_path = "path/to/output.json"
        >>> missing_comments = parse_dotnet_build_log(log_path, output_path)
        >>> print(missing_comments)
        {
            "path/to/file1.cs": ["Member1", "Member2"],
            "path/to/file2.cs": ["Member3", "Member4"]
        }
    """
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