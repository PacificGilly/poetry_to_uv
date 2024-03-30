poetry-to-uv
-----------------------------

[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Helps convert a Poetry formatted pyproject.toml file to a UV formatted pyproject.toml file (also 
compatible with pip and pip-compile)

The rationale behind this library is to make it easier to unpin the dependencies specified in your 
pyproject.toml so when you use `uv pip install -r pyproject.toml` it will ensure you keep the same
versions installed as did Poetry. Although you can manually export the resolved dependencies from 
Poetry, these will include ever single transient dependency, so it's really difficult to separate 
all of these out to ensure you only keep the existing deps.

# Installation
```
uv pip install poetry_to_uv
```

# Usage
```
usage: poetry_to_uv [-h] [--output-file OUTPUT_FILE] pyproject_path

Helps convert a Poetry formatted pyproject.toml file to a UV formatted pyproject.toml file (also compatible with pip and pip-compile). It will unpin all of your dependencies for you to ensure UV uses the exact same requirements, for your specified dependencies.

positional arguments:
  pyproject_path        Path to the Poetry formatted pyproject.toml file.

options:
  -h, --help            show this help message and exit
  --output-file OUTPUT_FILE
                        The output file to write the UV formatted pyproject.toml file. If not specified then it will print the results to the terminal.

Only meant as a helper to reduce some horrible BAU, especially if you've left all your dependencies unpinned!
```

# Known Issues
1) The new `[project]` settings are placed at the bottom of the file. So if you hate it, just as much as I do, then you'll have to manually move it to the top!
2) We rely on `poetry export` still existing, but it's currently deprecated in v1.7 of Poetry. So if you have issues, make sure to install the [Export Poetry Plugin](https://github.com/python-poetry/poetry-plugin-export).
