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
    "--output-directory",  # TODO make this work with relative paths
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
# TODO support other logs
def autodocs(
    path: str,
    output_directory: str = None,
    file_of_paths: str = None,
    dotnet_build_log: str = None,
):
    if path is None and file_of_paths is None and dotnet_build_log is None:
        print("Please specify a path, file of paths, and/or a dotnet build log.")
        return
    paths = [path] or []
    if dotnet_build_log is not None:
        paths += log_parser.parse_dotnet_build_log(dotnet_build_log, None)
    code_files_by_language = ad.get_code_files(paths, file_of_paths)

    click.echo("Running Autodocs with the following files:")
    for language, files in code_files_by_language.items():
        click.echo(f"{language}:")
        for file in files:
            click.echo(f"\t{file}")

    click.echo("current directory: " + os.getcwd())
    asyncio.run(
        ad.run_autodocs(
            code_files_by_language=code_files_by_language,
            output_directory=output_directory,
        )
    )


"""
Parses a dotnet build log and outputs a file for each path missing code documentation.
"""


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
    print("Parsing dotnet build log")
    log_parser.parse_dotnet_build_log(path, output_file)
