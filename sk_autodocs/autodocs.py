import os
import asyncio
from typing import Dict, List
import semantic_kernel as sk
from semantic_kernel import SKFunctionBase
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
)
from semantic_kernel.orchestration.context_variables import ContextVariables
from sk_autodocs.code_fetcher import CodeFetcher, CodeFile, CodeWriter
import click
from retry import retry
from openai.error import RateLimitError
from signal import SIGINT, SIGTERM

semantic_skills_dir = "sk_autodocs/plugins"


async def run_autodocs(code_files: List[CodeFile], output_directory: str = None):
    """
    Run the autodocs process on the given code files.

    Args:
        code_files (List[CodeFile]): A list of code files to process.
        output_directory (str, optional): The output directory for the processed files.
            Defaults to None.
    """
    kernel = setup_kernel()

    output_directory = prepare_output_directory(output_directory)
    autodocs_plugin = kernel.skills.get_function("AutoDocs", "Rewrite")

    results = await run_tasks(code_files, autodocs_plugin, output_directory)

    await write_results(results, output_directory)


async def work(queue: asyncio.Queue, results, plugin, output_directory):
    """
    Worker function for processing code files.

    Args:
        queue (asyncio.Queue): The queue containing code files to process.
        results (list): A list to store the results of processing the code files.
        plugin (SKFunctionBase): The autodocs plugin to use for processing.
        output_directory (str): The output directory for the processed files.
    """
    while True:
        code_file = await queue.get()
        results.append(await process_code_file(code_file, plugin, output_directory))
        queue.task_done()


async def run_tasks(
    code_files: List[CodeFile],
    plugin: SKFunctionBase,
    output_directory: str = None,
    num_workers: int = 6,
):
    """
    Run tasks to process the given code files.

    Args:
        code_files (List[CodeFile]): A list of code files to process.
        plugin (SKFunctionBase): The autodocs plugin to use for processing.
        output_directory (str, optional): The output directory for the processed files.
            Defaults to None.
        num_workers (int, optional): The number of worker tasks to create.
            Defaults to 6.

    Returns:
        list: A list of results from processing the code files.
    """
    queue = asyncio.Queue(num_workers)
    results = []
    workers = [
        asyncio.create_task(work(queue, results, plugin, output_directory))
        for _ in range(num_workers)
    ]
    for code_file in code_files:
        await queue.put(code_file)
    await queue.join()
    for worker in workers:
        worker.cancel()
    return results


def get_code_files(
    path: str = None,
    file_of_paths: str = None,
    paths_with_members: Dict[str, List[str]] = None,
) -> List[CodeFile]:
    """
    Get code files from the given sources.

    Args:
        path (str, optional): A single path to a code file. Defaults to None.
        file_of_paths (str, optional): A file containing paths to code files.
            Defaults to None.
        paths_with_members (Dict[str, List[str]], optional): A dictionary mapping
            paths to lists of member names. Defaults to None.

    Returns:
        List[CodeFile]: A list of code files.
    """
    code_fetcher = CodeFetcher()
    code_files = []
    code_files += code_fetcher.get_code_files([path]) or []
    code_files += code_fetcher.get_code_files_from_file_of_paths(file_of_paths) or []
    code_files += (
        code_fetcher.get_code_files_from_paths_with_members(paths_with_members) or []
    )
    code_files = code_fetcher.remove_duplicates(code_files=code_files)
    return code_files


@retry(exceptions=RateLimitError, tries=5, delay=60, backoff=2, jitter=(1, 60))
async def rewrite_code_file(plugin: SKFunctionBase, code_file: CodeFile):
    """
    Rewrite the given code file using the autodocs plugin.

    Args:
        plugin (SKFunctionBase): The autodocs plugin to use for rewriting.
        code_file (CodeFile): The code file to rewrite.

    Returns:
        str: The rewritten code, or False if an error occurred.
    """
    context_variables = ContextVariables(
        code_file.code,
        {
            "language": code_file.language,
            "docstyle": code_file.docstyle,
            "specific_members": ", ".join(code_file.members_missing_docstrings or []),
        },
    )

    rewritten_code_context = await plugin.invoke_async(variables=context_variables)
    if rewritten_code_context.error_occurred:
        if "RateLimitError" in rewritten_code_context._last_error_description:
            click.echo(f"Got RateLimitError. Retrying {code_file.path}")
            raise RateLimitError("Rate limit exceeded")
        print(f"Error rewriting code: {rewritten_code_context._last_error_description}")
        return False
    code_file.code = rewritten_code_context.result
    return rewritten_code_context.result


async def process_code_file(
    file: CodeFile, plugin: SKFunctionBase, output_directory: str = None
):
    """
    Process the given code file using the autodocs plugin.

    Args:
        file (CodeFile): The code file to process.
        plugin (SKFunctionBase): The autodocs plugin to use for processing.
        output_directory (str, optional): The output directory for the processed files.
            Defaults to None.

    Returns:
        tuple[CodeFile, bool]: A tuple containing the code file and a boolean indicating
            whether the processing was successful.
    """
    click.echo(
        f"Processing {file} with {file.language} language and {file.docstyle} docstyle"
    )
    code_writer = CodeWriter(output_directory=output_directory)
    code = await code_writer.read_file(code_file=file)
    if not code:
        click.echo("Error reading file")
        return file, False
    rewritten_code = await rewrite_code_file(plugin, file)
    if not rewritten_code:
        click.echo("Error rewriting file")
        return file, False

    success = await code_writer.write_file(file)

    return file, success


async def write_results(results: List[tuple[CodeFile, bool]], output_directory: str):
    """
    Write the successful results to a success file and failures to a failure file.

    Args:
        results (List[tuple]): A list of tuples containing the results of processing the code files.
        output_directory (str): The output directory for the processed files.
    """

    click.echo("Processed files: " + str(len(results)))
    if output_directory is None:
        output_directory = os.getcwd()
    success_file = os.path.join(output_directory, "success.txt")
    failure_file = os.path.join(output_directory, "failure.txt")

    # Create the output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)

    success_files = []
    failure_files = []
    for file, success in results:
        if success:
            success_files.append(file.path)
        else:
            failure_files.append(file.path)

    click.echo("Success: " + str(len(success_files)))
    click.echo("Failure: " + str(len(failure_files)))

    with open(success_file, "w") as f:
        f.write("\n".join(success_files))

    with open(failure_file, "w") as f:
        f.write("\n".join(failure_files))


def setup_kernel() -> sk.Kernel:
    """
    Set up the semantic kernel.

    Returns:
        sk.Kernel: The configured semantic kernel.
    """
    kernel = sk.Kernel()

    # Configure AI service used by the kernel. Load settings from the .env file.

    deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
    kernel.add_chat_service(
        deployment, AzureChatCompletion(deployment, endpoint, api_key)
    )

    kernel.import_semantic_skill_from_directory(semantic_skills_dir, "AutoDocs")

    return kernel


def prepare_output_directory(output_directory: str = None) -> str:
    """
    Prepare the output directory for the processed files.

    Args:
        output_directory (str, optional): The output directory for the processed files.
            Defaults to None.

    Returns:
        str: The prepared output directory.
    """
    if output_directory is None:
        return None
    elif not os.path.isabs(output_directory):
        output_directory = os.path.join(os.getcwd(), output_directory)

    # Normalize the output directory path
    output_directory = os.path.normpath(output_directory)

    return output_directory
