from typing import TypeVar

from packaging.utils import NormalizedName

PoetryResolvedDependencies = TypeVar("PoetryResolvedDependencies", bound=dict[NormalizedName, str])
UVResolvedDependencies = TypeVar("UVResolvedDependencies", bound=dict[NormalizedName, str])
