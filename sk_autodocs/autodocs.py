import os
import asyncio
from typing import Dict, List
import semantic_kernel as sk
from semantic_kernel import SKFunctionBase
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
)
from semantic_kernel.orchestration.context_variables import ContextVariables
from sk_autodocs.code_fetcher import CodeFetcher
import click
import shutil

semantic_skills_dir = "sk_autodocs/plugins"
supported_filetypes_to_lanaguage = {".py": "Python", ".cs": "C#", ".java": "Java"}
ignore_directory_list = [
    ".venv",
    "bin",
    "build",
    "dist",
    "node_modules",
    "obj",
    "Debug",
    "tst",
    "tests",
    "IntegrationTests",
]
ignore_file_list = ["__init__.py", "Program.cs", "AssemblyInfo.cs"]
language_to_docstyle = {"C#": ".NET XML", "Python": "google style", "Java": "javadoc"}


async def run_autodocs(
    code_files_by_language: Dict[str, List[str]], output_directory: str = None
):
    kernel = setup_kernel()

    output_directory = prepare_output_directory(output_directory)

    autodocs_plugin = kernel.skills.get_function("AutoDocs", "Rewrite")

    coroutines = [
        process_code_file(autodocs_plugin, file, language, output_directory)
        for language, files in code_files_by_language.items()
        for file in files
    ]
    return await asyncio.gather(*coroutines)


def get_code_files(paths: List[str], file_of_paths: str = None) -> Dict[str, List[str]]:
    code_fetcher = CodeFetcher(
        supported_filetypes_to_lanaguage,
        ignore_directory_list=ignore_directory_list,
        ignore_file_list=ignore_file_list,
    )
    paths_by_language = code_fetcher.get_code_files(paths)
    code_files_from_file = code_fetcher.get_code_files_from_file_of_paths(file_of_paths)
    code_files_by_language = code_fetcher.merge_dictionaries(
        [paths_by_language, code_files_from_file]
    )
    code_files_by_language = code_fetcher.remove_duplicates(code_files_by_language)
    return code_files_by_language


async def read_code_file(file: str) -> str:
    click.echo("Reading " + os.path.abspath(file))
    try:
        with open(os.path.abspath(file), "r") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file}: {e}")
        return False


async def write_code_file(file: str, code: str, output_directory: str = None):
    output_path = os.path.join(output_directory, file)
    click.echo("Writing to " + output_path)
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(os.path.abspath(output_path), "w") as f:
            f.write(code)
        return True
    except Exception as e:
        print(f"Error writing to {file}: {e}")
        return False


async def process_code_file(
    plugin: SKFunctionBase, file: str, language: str, output_directory: str = None
):
    docstyle = language_to_docstyle[language]
    click.echo(f"Processing {file} with {language} and {docstyle}")

    code = await read_code_file(file)
    if not code:
        return

    context_variables = ContextVariables(
        code, {"language": language, "docstyle": docstyle}
    )

    rewritten_code_context = await plugin.invoke_async(variables=context_variables)

    if rewritten_code_context.error_occurred:
        click.echo(
            f"Error processing {file}: {rewritten_code_context._last_error_description}"
        )
        return

    await write_code_file(file, rewritten_code_context.result, output_directory)


def setup_kernel() -> sk.Kernel:
    kernel = sk.Kernel()

    # Configure AI service used by the kernel. Load settings from the .env file.

    deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
    kernel.add_chat_service(
        deployment, AzureChatCompletion(deployment, endpoint, api_key)
    )

    kernel.import_semantic_skill_from_directory(semantic_skills_dir, "AutoDocs")

    return kernel


def prepare_output_directory(output_directory: str = None) -> str:
    if output_directory is None:
        output_directory = os.getcwd()
    elif not os.path.isabs(output_directory):
        output_directory = os.path.join(os.getcwd(), output_directory)

    # Normalize the output directory path
    output_directory = os.path.normpath(output_directory)

    return output_directory
