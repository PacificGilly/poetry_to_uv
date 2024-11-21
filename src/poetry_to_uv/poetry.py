import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from packaging.utils import canonicalize_name

from poetry_to_uv.constants import POETRY_COMMAND
from poetry_to_uv.typing import PoetryResolvedDependencies


@dataclass
class PoetryDependencyExporter:
    """
    Helper class for exporting all dependencies (top-level, transient) from Poetry.
    """

    path: Path
    extras: Optional[list[str]] = None
    groups: Optional[list[str]] = None

    def _build_command(self) -> str:
        extras_command = ""
        if self.extras:
            for extra in self.extras:
                extras_command += f"--extras {extra} "

        groups_command = ""
        if self.groups:
            for group in self.groups:
                groups_command += f"--with {group} "

        path_command = f"--directory={self.path.absolute()}"

        return f"{POETRY_COMMAND} {extras_command} {groups_command} {path_command}"

    def _process_poetry_export_command(self, poetry_response: bytes) -> PoetryResolvedDependencies:
        """
        Handles the parsing of the poetry export command.

        :param poetry_response:
            The response from the poetry export command.
        :return:
            The resolved poetry dependencies.
        """
        assert poetry_response
        decoded_poetry_response = poetry_response.decode("utf-8")
        decoded_poetry_response_rows = decoded_poetry_response.split("\n")

        dependency_mapping: PoetryResolvedDependencies = {}
        for decoded_poetry_response_row in decoded_poetry_response_rows:
            dependency_version = decoded_poetry_response_row.split(";")[0]

            if not dependency_version:
                continue

            if "@" in dependency_version:
                dependency, version = dependency_version.split("@")
            elif "==" in dependency_version:
                dependency, version = dependency_version.split("==")
            else:
                raise RuntimeError("Couldn't parse the dependency strategy delimiter.")

            dependency_mapping[canonicalize_name(dependency)] = version.strip()

        return dependency_mapping

    def export(self) -> PoetryResolvedDependencies:
        """
        Exports a simple mapping of dependency names to their version strings.

        :return:
            The mapping of the dependency name to their version strings.
        """
        poetry_export_command = self._build_command()
        poetry_response = subprocess.run(poetry_export_command.split(), capture_output=True)
        return self._process_poetry_export_command(poetry_response.stdout)
