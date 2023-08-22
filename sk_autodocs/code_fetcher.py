import os
import tempfile
from typing import List, Mapping, Dict

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


class CodeFile:
    """
    A class representing a code file.

    Attributes:
        language (str): The programming language of the code file.
        docstyle (str): The documentation style used in the code file.
        path (str): The file path of the code file.
        code (str): The content of the code file.
        members_missing_docstrings (List[str]): A list of members missing docstrings.

    Example usage:
        code_file = CodeFile(path="path/to/codefile.py")
        print(code_file.language)  # Output: "Python"
    """

    language: str
    docstyle: str
    path: str
    code: str
    members_missing_docstrings: List[str]

    def __init__(
        self,
        path: str = None,
        code: str = None,
        members_missing_docstrings: List[str] = None,
    ):
        self.path = path
        self.language = None
        self.docstyle = None
        for extension, language in supported_filetypes_to_lanaguage.items():
            if path.endswith(extension):
                self.language = language
                self.docstyle = language_to_docstyle[language]
                break
        self.code = code
        self.members_missing_docstrings = members_missing_docstrings

    def __repr__(self):
        return f"Path: {self.path}"

    def __eq__(self, other):
        if isinstance(other, CodeFile):
            return self.path == other.path
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__repr__())


class CodeFetcher:
    """
    A class to fetch code files from local directories or GitHub repositories.

    Example usage:
        code_fetcher = CodeFetcher()
        code_files = code_fetcher.get_code_files(["path/to/local/directory"])
        print(len(code_files))  # Output: Number of code files found
    """

    def get_code_files(self, paths: List[str]) -> List[CodeFile]:
        """
        Get code files from a list of paths.

        Args:
            paths (List[str]): A list of paths to search for code files.

        Returns:
            List[CodeFile]: A list of CodeFile objects found in the given paths.
        """
        files = []
        for path in paths:
            if not path:
                continue
            if path.startswith("https://github.com"):
                files.extend(self.get_github_files(path))
            elif os.path.isdir(path):
                files.extend(self.get_local_files_in_dir(path))
            else:
                files.append(CodeFile(path))

        return self.filter_code_files_by_language(files)

    def get_github_files(self, github_url: str) -> List[CodeFile]:
        """
        Get code files from a GitHub repository.

        Args:
            github_url (str): The URL of the GitHub repository.

        Returns:
            List[CodeFile]: A list of CodeFile objects found in the GitHub repository.
        """
        # Create a temporary directory to clone the repository into
        temp_dir = tempfile.mkdtemp()

        # Clone the repository into the temporary directory
        os.system(f"git clone {github_url} {temp_dir}")

        return self.get_local_files_in_dir(temp_dir)

    def get_local_files_in_dir(self, local_dir: str) -> List[CodeFile]:
        """
        Get code files from a local directory.

        Args:
            local_dir (str): The path of the local directory.

        Returns:
            List[CodeFile]: A list of CodeFile objects found in the local directory.
        """
        # Walk the directory and get all files
        # Ignore directories from the ignore list
        files = []
        for root, dirs, filenames in os.walk(local_dir):
            for filename in filenames:
                if not any(
                    ignore in root for ignore in ignore_directory_list
                ) and not any(ignore in filename for ignore in ignore_file_list):
                    files.append(CodeFile(path=os.path.join(root, filename)))
        return files

    def filter_code_files_by_language(self, files: List[CodeFile]) -> List[CodeFile]:
        """
        Filter code files by supported languages.

        Args:
            files (List[CodeFile]): A list of CodeFile objects.

        Returns:
            List[CodeFile]: A list of CodeFile objects with supported languages.
        """
        return list(
            filter(
                lambda file: file.language in supported_filetypes_to_lanaguage.values(),
                files,
            )
        )

    def get_code_files_from_file_of_paths(self, file_of_paths: str) -> List[CodeFile]:
        """
        Get code files from a file containing a list of paths.

        Args:
            file_of_paths (str): The path of the file containing a list of paths.

        Returns:
            List[CodeFile]: A list of CodeFile objects found in the given paths.
        """
        if file_of_paths is None:
            return []
        with open(file_of_paths, "r") as f:
            paths = f.readlines()
        code_files = []
        code_files.extend(self.get_code_files(paths))
        return code_files

    def get_code_files_from_paths_with_members(
        self, paths_with_members: Dict[str, List[str]]
    ) -> List[CodeFile]:
        """
        Get code files from a dictionary of paths with members.

        Args:
            paths_with_members (Dict[str, List[str]]): A dictionary of paths with members.

        Returns:
            List[CodeFile]: A list of CodeFile objects found in the given paths.
        """
        code_files = []
        for path, members in paths_with_members.items():
            new_files = self.get_code_files([path])
            for code_file in new_files:
                code_file.members_missing_docstrings = members
            code_files.extend(new_files)
        return code_files

    def remove_duplicates(self, code_files: List[CodeFile]) -> List[CodeFile]:
        """
        Remove duplicate code files from a list.

        Args:
            code_files (List[CodeFile]): A list of CodeFile objects.

        Returns:
            List[CodeFile]: A list of unique CodeFile objects.
        """
        return list(set(code_files))


class CodeWriter:
    """
    A class to read and write code files.

    Example usage:
        code_writer = CodeWriter(output_directory="path/to/output/directory")
        code_file = CodeFile(path="path/to/codefile.py")
        code_writer.read_file(code_file)
        code_writer.write_file(code_file)
    """

    def __init__(self, output_directory: str):
        self.output_directory = output_directory

    async def read_file(self, code_file: CodeFile) -> str:
        """
        Read the content of a code file.

        Args:
            code_file (CodeFile): The CodeFile object to read.

        Returns:
            str: The content of the code file, or False if an error occurred.
        """
        try:
            with open(os.path.abspath(code_file.path), "r") as f:
                code_file.code = f.read()
                if not code_file.code:
                    return False
                return code_file.code
        except Exception as e:
            print(f"Error reading {code_file.path}: {e}")
            return False

    async def write_file(self, code_file: CodeFile) -> bool:
        """
        Write the content of a code file to the output directory.

        Args:
            code_file (CodeFile): The CodeFile object to write.

        Returns:
            bool: True if the file was written successfully, False otherwise.
        """
        if not self.output_directory:
            output_path = code_file.path
        else:
            output_path = os.path.join(
                self.output_directory,
                (
                    os.path.relpath(code_file.path, self.output_directory)
                    .strip("..\\")
                    .strip("../")
                ),
            )
        print(f"Writing to {output_path}")
        try:
            # Create the output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(os.path.abspath(output_path), "w") as f:
                f.write(code_file.code)

            return True
        except Exception as e:
            print(f"Error writing to {output_path}: {e}")
            return False
