def parse_dotnet_build_log(path: str, output_file: str):
    """
    Parses a dotnet build log and outputs a file for each path missing code documentation.

    This function reads a dotnet build log file, extracts the paths with missing code documentation
    (identified by the "CS1591" warning), and writes them to a specified output file or returns them
    as a list if no output file is provided.

    Args:
        path (str): The path to the dotnet build log file.
        output_file (str): The path to the output file where the paths with missing documentation
            will be written. If None, the function will return the paths as a list.

    Returns:
        list: A list of paths with missing code documentation if output_file is None.

    Example usage:

        # Parse a dotnet build log and write the paths with missing documentation to an output file
        parse_dotnet_build_log("build.log", "missing_docs.txt")

        # Parse a dotnet build log and get the paths with missing documentation as a list
        paths = parse_dotnet_build_log("build.log", None)
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