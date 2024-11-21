import sys
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Any, Optional, cast

import tomlkit
from packaging.utils import NormalizedName, canonicalize_name
from tomlkit import TOMLDocument
from tomlkit.exceptions import NonExistentKey
from tomlkit.items import Array

from poetry_to_uv.poetry import PoetryDependencyExporter
from poetry_to_uv.typing import PoetryResolvedDependencies, UVResolvedDependencies
from poetry_to_uv.validation import PoetryPyProject

log = getLogger(__name__)


@dataclass
class PoetryToUv:
    pyproject_path: Path
    output_file: Optional[Path] = None

    def _load_project_file(self) -> TOMLDocument:
        with open(self.pyproject_path, "rb") as f:
            return tomlkit.load(f)

    def _save_project_file(self, config: TOMLDocument) -> None:
        # TODO: Update to `self.pyproject_path`.
        if self.output_file:
            with open(self.output_file, mode="wt", encoding="utf-8") as fp:
                tomlkit.dump(config, fp)
        else:
            tomlkit.dump(config, sys.stdout)

    def get_poetry_resolved_dependencies(
        self, extras: Optional[list[str]] = None, groups: Optional[list[str]] = None
    ) -> PoetryResolvedDependencies:
        """
        Makes a call to poetry and extras the resolved dependencies for all groups and extras.

        :return:
            A list of resolved dependencies.
        """
        poetry_dependency_exporter = PoetryDependencyExporter(
            path=self.pyproject_path,
            extras=extras,
            groups=groups,
        )
        return poetry_dependency_exporter.export()

    def resolve_dependency(
        self,
        dependency: str,
        poetry_resolved_dependencies: dict[NormalizedName, str],
        **kwargs: Any,
    ) -> str:
        pyproject_resolved_dependency = poetry_resolved_dependencies.get(
            canonicalize_name(dependency)
        )
        if not pyproject_resolved_dependency:
            log.warning("Failed to resolve dependency for `%s`", dependency)
        return pyproject_resolved_dependency

    def _process_main_dependencies(
        self,
        pyproject: PoetryPyProject,
        poetry_resolved_dependencies: PoetryResolvedDependencies,
    ) -> UVResolvedDependencies:
        """
        With the Poetry formatted PyProject file and the resolved Poetry dependencies,
        convert them to UV-resolved dependencies.

        :param pyproject:
        :param poetry_resolved_dependencies:
        :return:
        """
        pyproject_resolved_dependencies: UVResolvedDependencies = {}
        for dependency in pyproject.tool.poetry.get_dependencies:
            resolved_dep = self.resolve_dependency(dependency, poetry_resolved_dependencies)
            pyproject_resolved_dependencies[dependency] = resolved_dep

        return pyproject_resolved_dependencies

    def _process_group_dependencies(
        self,
        pyproject: PoetryPyProject,
        poetry_resolved_dependencies: PoetryResolvedDependencies,
    ) -> dict[str, UVResolvedDependencies]:
        """
        With the Poetry formatted PyProject file and the resolved Poetry dependencies,
        convert them to UV-resolved dependencies.

        :param pyproject:
        :param poetry_resolved_dependencies:
        :return:
        """
        pyproject_resolved_dependencies_group: dict[str, UVResolvedDependencies] = {}
        for dependency_group, dependencies in pyproject.tool.poetry.group.items():
            pyproject_resolved_dependencies_group[dependency_group] = {}
            for dependency in dependencies["dependencies"]:
                resolved_dep = self.resolve_dependency(dependency, poetry_resolved_dependencies)
                pyproject_resolved_dependencies_group[dependency_group][
                    canonicalize_name(dependency)
                ] = resolved_dep

        return pyproject_resolved_dependencies_group

    def _process_extra_dependencies(
        self,
        pyproject: PoetryPyProject,
        poetry_resolved_dependencies: PoetryResolvedDependencies,
    ) -> dict[str, UVResolvedDependencies]:
        """
        With the Poetry formatted PyProject file and the resolved Poetry dependencies,
        convert them to UV-resolved dependencies.

        :param pyproject:
        :param poetry_resolved_dependencies:
        :return:
        """
        pyproject_resolved_dependencies_group: dict[str, UVResolvedDependencies] = {}
        for dependency_group, dependencies in pyproject.tool.poetry.get_extras.items():
            pyproject_resolved_dependencies_group[dependency_group] = {}
            for dependency in dependencies:
                resolved_dep = self.resolve_dependency(dependency, poetry_resolved_dependencies)
                pyproject_resolved_dependencies_group[dependency_group][
                    canonicalize_name(dependency)
                ] = resolved_dep

        return pyproject_resolved_dependencies_group

    def _convert_poetry_to_uv_pyproject(
        self,
        pyproject_config: TOMLDocument,
        main_dependencies: UVResolvedDependencies,
        extra_dependencies: dict[str, UVResolvedDependencies],
        group_dependencies: dict[str, UVResolvedDependencies],
    ) -> TOMLDocument:
        """
        Coverts a Poetry formatted PyProject file to a UV formatted PyProject file.

        :return:
        """
        # Convert the old `[tool][poetry]` into `[project]`
        tool_poetry = pyproject_config["tool"]["poetry"]
        pyproject_config.add("project", tool_poetry)

        # Remove the Poetry formatted dependencies.
        try:
            pyproject_config.get("project").remove("source")
        except NonExistentKey:
            pass
        try:
            pyproject_config.get("project").remove("group")
        except NonExistentKey:
            pass
        try:
            pyproject_config.get("project").remove("extras")
        except NonExistentKey:
            pass
        tool = pyproject_config.get("tool")
        try:
            tool.remove("poetry")
        except AttributeError:
            tool.pop("poetry")

        # Add the `dependencies` to the `[project]`.
        pyproject_config = self._write_main_dependencies(
            pyproject_config=pyproject_config, main_dependencies=main_dependencies
        )
        pyproject_config = self._write_optional_dependencies(
            pyproject_config=pyproject_config,
            extra_dependencies=extra_dependencies,
            group_dependencies=group_dependencies,
        )

        return pyproject_config

    def _write_main_dependencies(
        self, pyproject_config: TOMLDocument, main_dependencies: UVResolvedDependencies
    ) -> TOMLDocument:
        sorted_main_dependencies = dict(sorted(main_dependencies.items()))

        uv_dependencies = tomlkit.array()
        for dependency, version in sorted_main_dependencies.items():
            uv_dependencies.add_line(f"{dependency} == {version}")

        pyproject_config["project"]["dependencies"] = uv_dependencies

        return pyproject_config

    def _write_optional_dependencies(
        self,
        pyproject_config: TOMLDocument,
        extra_dependencies: dict[str, UVResolvedDependencies],
        group_dependencies: dict[str, UVResolvedDependencies],
    ) -> TOMLDocument:
        """
        In the pip-compile world, there doesn't seem to be a difference between "extras" and
        "groups" in that you get in Poetry - They're all marked as "extras".

        :return:
        """
        sorted_extra_dependencies = dict(sorted(extra_dependencies.items()))
        sorted_group_dependencies = dict(sorted(group_dependencies.items()))

        all_dependency_groups: dict[str, Array] = {}

        # Process the group dependencies.
        for dependency_group, dependencies in sorted_group_dependencies.items():
            uv_dependencies = tomlkit.array()
            for dependency, version in dependencies.items():
                uv_dependencies.add_line(f"{dependency} == {version}")
            all_dependency_groups[dependency_group] = uv_dependencies

        # Process the extra dependencies.
        for dependency_group, dependencies in sorted_extra_dependencies.items():
            uv_dependencies = tomlkit.array()
            for dependency, version in dependencies.items():
                uv_dependencies.add_line(f"{dependency} == {version}")
            all_dependency_groups[dependency_group] = uv_dependencies

        pyproject_config["project"]["optional-dependencies"] = tomlkit.item(all_dependency_groups)

        return pyproject_config

    def __call__(self):
        pyproject_config = self._load_project_file()
        pyproject: PoetryPyProject = cast(
            PoetryPyProject, PoetryPyProject(**pyproject_config.unwrap())
        )

        # Get all the projects resolved dependencies, including any transient ones (which we don't
        # care as UV will later re-resolve for us).
        poetry_resolved_dependencies = self.get_poetry_resolved_dependencies(
            extras=list(pyproject.tool.poetry.get_extras.keys()),
            groups=list(pyproject.tool.poetry.get_groups.keys()),
        )

        # Now resolve the dependencies everywhere.
        main_dependencies = self._process_main_dependencies(pyproject, poetry_resolved_dependencies)
        group_dependencies = self._process_group_dependencies(
            pyproject, poetry_resolved_dependencies
        )
        extra_dependencies = self._process_extra_dependencies(
            pyproject, poetry_resolved_dependencies
        )

        # Update the pyproject config.
        pyproject_config = self._convert_poetry_to_uv_pyproject(
            pyproject_config,
            main_dependencies=main_dependencies,
            group_dependencies=group_dependencies,
            extra_dependencies=extra_dependencies,
        )

        self._save_project_file(pyproject_config)
