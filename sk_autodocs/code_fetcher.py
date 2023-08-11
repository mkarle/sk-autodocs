import os
import tempfile
from typing import List, Mapping, Dict


class CodeFetcher:
    def __init__(
        self,
        supported_filetypes_to_language: Mapping[str, str],
        ignore_directory_list: List[str],
        ignore_file_list: List[str],
    ):
        self.supported_filetypes_to_lanaguage = supported_filetypes_to_language
        self.ignore_directory_list = ignore_directory_list
        self.ignore_file_list = ignore_file_list

    """Fetches code from a github repo or local directory and returns a dict of language -> code files"""

    def get_code_files(self, paths: List[str]) -> Dict[str, List[str]]:
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

    """Gets files from a github repository"""

    def get_github_files(self, github_url: str) -> str:
        # Create a temporary directory to clone the repository into
        temp_dir = tempfile.mkdtemp()

        # Clone the repository into the temporary directory
        os.system(f"git clone {github_url} {temp_dir}")

        return self.get_local_files(temp_dir)

    """Gets files from a local directory"""

    def get_local_files(self, local_path: str) -> str:
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

    """Filters files based on file extension. Supports .py, .cs, and .java"""

    def filter_code_files_by_language(self, files: List[str]) -> str:
        filtered_files = {}
        for extension, language in self.supported_filetypes_to_lanaguage.items():
            filtered_list = [file for file in files if file.endswith(extension)]
            if len(filtered_list) > 0:
                filtered_files[language] = filtered_list
        return filtered_files

    """Gets code files from a file of paths"""

    def get_code_files_from_file_of_paths(
        self, file_of_paths: str
    ) -> Dict[str, List[str]]:
        if file_of_paths is None:
            return {}
        with open(file_of_paths, "r") as f:
            paths = f.readlines()

        list_code_files_by_language = [self.get_code_files(path) for path in paths]
        return self.merge_dictionaries(list_code_files_by_language)

    """Merges two dictionaries of language -> code files"""

    def merge_dictionaries(
        self, list_of_dicts: List[Dict[str, List[str]]]
    ) -> Dict[str, List[str]]:
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

    """ Remove duplicates from dictionary of language -> code files"""
    def remove_duplicates(self, code_files_by_language: Dict[str, List[str]]):
        for language, files in code_files_by_language.items():
            code_files_by_language[language] = list(set(files))
        return code_files_by_language
