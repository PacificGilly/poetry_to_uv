from typing import Any, Optional

from packaging.utils import NormalizedName, canonicalize_name
from pydantic.dataclasses import dataclass as pydantic_dataclass


@pydantic_dataclass
class PoetryConfig:
    description: str
    dependencies: dict[str, Any]
    group: Optional[dict[str, Any]] = None
    extras: Optional[dict[str, Any]] = None

    @property
    def get_dependencies(self) -> dict[NormalizedName, str]:
        """
        Reformats dependencies with extras.

        e.g.
        moto = {'extras': ['sqs'], 'version': '*'} -> moto[sqs]

        :return:
        """
        dependencies: dict[NormalizedName, str] = {}
        for dependency, version in self.dependencies.items():
            if isinstance(version, str):
                dependencies[canonicalize_name(dependency)] = version
            elif isinstance(version, dict):
                extras = version.get("extras")
                sub_version = version.get("version")
                if not extras:
                    dependency_normalized = canonicalize_name(dependency)
                else:
                    dependency_combined = f"{dependency}[{','.join(sorted(extras))}]"
                    dependency_normalized = canonicalize_name(dependency_combined)
                dependencies[dependency_normalized] = sub_version or "*"
            else:
                raise RuntimeError(f"Unknown dependency version: `{version}`")

        return dependencies

    @property
    def get_groups(self) -> dict[NormalizedName, str]:
        if not isinstance(self.group, dict):
            return {}
        return self.group

    @property
    def get_extras(self) -> dict[NormalizedName, str]:
        if not isinstance(self.extras, dict):
            return {}
        return self.extras


@pydantic_dataclass
class PyProjectTool:
    poetry: PoetryConfig


@pydantic_dataclass
class PoetryPyProject:
    tool: PyProjectTool
