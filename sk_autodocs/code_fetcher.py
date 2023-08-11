import os
import tempfile
from typing import List, Mapping, Dict


class CodeFetcher:
    """
    A class to fetch code files from a GitHub repository or local directory.

    Attributes:
        supported_filetypes_to_language (Mapping[str, str]): A mapping of supported file extensions to their respective languages.
        ignore_directory_list (List[str]): A list of directory names to ignore while fetching code files.
        ignore_file_list (List[str]): A list of file names to ignore while fetching code files.

    Example usage:

        code_fetcher = CodeFetcher(
            supported_filetypes_to_language={".py": "Python", ".cs": "CSharp", ".java": "Java"},
            ignore_directory_list=[".git", "__pycache__"],
            ignore_file_list=["README.md"]
        )

        code_files = code_fetcher.get_code_files(["https://github.com/user/repo", "/path/to/local/directory"])
    """

    def __init__(
        self,
        supported_filetypes_to_language: Mapping[str, str],
        ignore_directory_list: List[str],
        ignore_file_list: List[str],
    ):
        self.supported_filetypes_to_lanaguage = supported_filetypes_to_language
        self.ignore_directory_list = ignore_directory_list
        self.ignore_file_list = ignore_file_list

    def get_code_files(self, paths: List[str]) -> Dict[str, List[str]]:
        """
        Fetches code files from a list of GitHub repositories or local directories and returns a dictionary of language -> code files.

        Args:
            paths (List[str]): A list of GitHub repository URLs or local directory paths.

        Returns:
            Dict[str, List[str]]: A dictionary of language -> code files.
        """
        files = []
        for path in paths:
            if not path:
                continue
            if path.startswith("https://github.com"):
                files.extend(self.get_github_files(path))
            elif os.path.isdir(path):
                files.extend(self.get_local_files(path))
            else:
                files.append(path)

        return self.filter_code_files_by_language(files)

    def get_github_files(self, github_url: str) -> str:
        """
        Gets files from a GitHub repository.

        Args:
            github_url (str): The URL of the GitHub repository.

        Returns:
            str: The path to the cloned repository.
        """
        # Create a temporary directory to clone the repository into
        temp_dir = tempfile.mkdtemp()

        # Clone the repository into the temporary directory
        os.system(f"git clone {github_url} {temp_dir}")

        return self.get_local_files(temp_dir)

    def get_local_files(self, local_path: str) -> str:
        """
        Gets files from a local directory.

        Args:
            local_path (str): The path to the local directory.

        Returns:
            str: The path to the local directory.
        """
        # Walk the directory and get all files
        # Ignore directories from the ignore list
        files = []
        for root, dirs, filenames in os.walk(local_path):
            for filename in filenames:
                if not any(
                    ignore in root for ignore in self.ignore_directory_list
                ) and not any(ignore in filename for ignore in self.ignore_file_list):
                    files.append(os.path.join(root, filename))
        return files

    def filter_code_files_by_language(self, files: List[str]) -> str:
        """
        Filters files based on file extension. Supports .py, .cs, and .java.

        Args:
            files (List[str]): A list of file paths.

        Returns:
            str: The path to the filtered files.
        """
        filtered_files = {}
        for extension, language in self.supported_filetypes_to_lanaguage.items():
            filtered_list = [file for file in files if file.endswith(extension)]
            if len(filtered_list) > 0:
                filtered_files[language] = filtered_list
        return filtered_files

    def get_code_files_from_file_of_paths(
        self, file_of_paths: str
    ) -> Dict[str, List[str]]:
        """
        Gets code files from a file containing paths.

        Args:
            file_of_paths (str): The path to the file containing paths.

        Returns:
            Dict[str, List[str]]: A dictionary of language -> code files.
        """
        if file_of_paths is None:
            return {}
        with open(file_of_paths, "r") as f:
            paths = f.readlines()

        list_code_files_by_language = [self.get_code_files(path) for path in paths]
        return self.merge_dictionaries(list_code_files_by_language)

    def merge_dictionaries(
        self, list_of_dicts: List[Dict[str, List[str]]]
    ) -> Dict[str, List[str]]:
        """
        Merges a list of dictionaries of language -> code files.

        Args:
            list_of_dicts (List[Dict[str, List[str]]]): A list of dictionaries of language -> code files.

        Returns:
            Dict[str, List[str]]: A merged dictionary of language -> code files.
        """
        all_code_files_by_language = {}
        for language in self.supported_filetypes_to_lanaguage.values():
            all_code_files_by_language[language] = []
            for code_files_by_language in list_of_dicts:
                if language in code_files_by_language:
                    all_code_files_by_language[language].extend(
                        code_files_by_language[language]
                    )

        # Remove empty lists
        all_code_files_by_language = {
            language: files
            for language, files in all_code_files_by_language.items()
            if len(files) > 0
        }
        return all_code_files_by_language

    def remove_duplicates(self, code_files_by_language: Dict[str, List[str]]):
        """
        Removes duplicates from a dictionary of language -> code files.

        Args:
            code_files_by_language (Dict[str, List[str]]): A dictionary of language -> code files.

        Returns:
            Dict[str, List[str]]: A dictionary of language -> code files without duplicates.
        """
        for language, files in code_files_by_language.items():
            code_files_by_language[language] = list(set(files))
        return code_files_by_language