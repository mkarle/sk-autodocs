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
    def get_code_files(self, paths: List[str]) -> List[CodeFile]:
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
        # Create a temporary directory to clone the repository into
        temp_dir = tempfile.mkdtemp()

        # Clone the repository into the temporary directory
        os.system(f"git clone {github_url} {temp_dir}")

        return self.get_local_files_in_dir(temp_dir)

    def get_local_files_in_dir(self, local_dir: str) -> List[CodeFile]:
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
        return list(
            filter(
                lambda file: file.language in supported_filetypes_to_lanaguage.values(),
                files,
            )
        )

    def get_code_files_from_file_of_paths(self, file_of_paths: str) -> List[CodeFile]:
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
        code_files = []
        for path, members in paths_with_members.items():
            new_files = self.get_code_files([path])
            for code_file in new_files:
                code_file.members_missing_docstrings = members
            code_files.extend(new_files)
        return code_files

    def remove_duplicates(self, code_files: List[CodeFile]) -> List[CodeFile]:
        return list(set(code_files))


class CodeWriter:
    def __init__(self, output_directory: str):
        self.output_directory = output_directory

    async def read_file(self, code_file: CodeFile) -> str:
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
        try:
            # Create the output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(os.path.abspath(output_path), "w") as f:
                f.write(code_file.code)

            return True
        except Exception as e:
            print(f"Error writing to {output_path}: {e}")
            return False
