import click
import asyncio
import sk_autodocs.autodocs as ad
import sk_autodocs.log_parser as log_parser
import os

"""
Call Autodocs with a given local path or github repository.
Autodocs will modify files by adding documentation comments.
"""


@click.group(invoke_without_command=True)
@click.option(
    "--path",
    "-p",
    required=False,
    help="The path to look for the code. Can be a file, directory, or github repository.",
)
@click.option(
    "--output-directory",
    "-o",
    required=False,
    help="The directory to output the modified files. If not specified, the files will be modified in place.",
)
@click.option(
    "--file-of-paths",
    "-f",
    required=False,
    help="The path to a file containing the paths to look for the code separated by newlines. Paths can be a file, directory, or github repository.",
)
@click.option(
    "--dotnet-build-log",
    required=False,
    help="The path to a dotnet build log to parse for missing documentation warnings.",
)
def autodocs(
    path: str,
    output_directory: str = None,
    file_of_paths: str = None,
    dotnet_build_log: str = None,
):
    """
    Main entry point for the Autodocs CLI.

    Example usage:
        autodocs --path /path/to/code
        autodocs --path /path/to/code --output-directory /path/to/output
        autodocs --file-of-paths /path/to/file_of_paths
        autodocs --dotnet-build-log /path/to/dotnet_build_log

    Args:
        path (str): The path to look for the code. Can be a file, directory, or github repository.
        output_directory (str, optional): The directory to output the modified files. If not specified, the files will be modified in place.
        file_of_paths (str, optional): The path to a file containing the paths to look for the code separated by newlines. Paths can be a file, directory, or github repository.
        dotnet_build_log (str, optional): The path to a dotnet build log to parse for missing documentation warnings.
    """
    if path is None and file_of_paths is None and dotnet_build_log is None:
        print("Please specify a path, file of paths, and/or a dotnet build log.")
        return
    paths_with_members = {}
    if dotnet_build_log is not None:
        paths_with_members = log_parser.parse_dotnet_build_log(dotnet_build_log, None)
    code_files = ad.get_code_files(path, file_of_paths, paths_with_members)

    click.echo("current directory: " + os.getcwd())
    asyncio.run(
        ad.run_autodocs(
            code_files=code_files,
            output_directory=output_directory,
        )
    )


@autodocs.command("parse_dotnet_build_log")
@click.option(
    "--path",
    "-p",
    required=True,
    help="The path to the dotnet build log.",
)
@click.option(
    "--output-file",
    "-o",
    required=True,
    help="The path to the output file.",
)
def parse_dotnet_build_log(path: str, output_file: str):
    """
    Parses a dotnet build log and outputs a file for each path missing code documentation.

    Example usage:
        autodocs parse_dotnet_build_log --path /path/to/dotnet_build_log --output-file /path/to/output_file

    Args:
        path (str): The path to the dotnet build log.
        output_file (str): The path to the output file.
    """
    print("Parsing dotnet build log")
    log_parser.parse_dotnet_build_log(path, output_file)


if __name__ == "__main__":
    autodocs(
        [
            "--dotnet-build-log",
            "C:\\Users\\markkarle\\localworkspace\\mkarle\\semantic-kernel\\dotnet\\log.log",
        ]
    )
