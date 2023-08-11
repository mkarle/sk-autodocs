def parse_dotnet_build_log(path: str, output_file: str):
    """
    Parses a dotnet build log and outputs a file for each path missing code documentation.
    """
    with open(path, "r") as f:
        lines = f.readlines()

    # Get all the paths
    paths = []
    for line in lines:
        if "CS1591" in line:
            path = line[: line.find("(")]
            paths.append(path)

    if output_file is None:
        return paths
    # Write to file
    with open(output_file, "w") as f:
        f.write("\n".join(paths))
