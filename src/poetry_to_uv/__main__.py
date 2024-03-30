import argparse
from pathlib import Path

from poetry_to_uv.convertor import PoetryToUv


def cli_entrypoint():
    parser = argparse.ArgumentParser(
        prog="python -m poetry_to_uv",
        description=(
            "Helps convert a Poetry formatted pyproject.toml file to a UV formatted pyproject.toml "
            "file (also compatible with pip and pip-compile). It will unpin all of your "
            "dependencies for you to ensure UV uses the exact same requirements, for your "
            "specified dependencies."
        ),
        epilog=(
            "Only meant as a helper to reduce some horrible BAU, especially if you've left all "
            "your dependencies unpinned!"
        ),
    )

    parser.add_argument(
        "pyproject_path", type=Path, help="Path to the Poetry formatted " "pyproject.toml file."
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="The output file to write the UV formatted pyproject.toml file. If "
             "not specified then it will print the results to the terminal.",
    )
    args = parser.parse_args()

    poetry_to_uv = PoetryToUv(pyproject_path=args.pyproject_path, output_file=args.output_file)
    poetry_to_uv()


if __name__ == "__main__":
    cli_entrypoint()
