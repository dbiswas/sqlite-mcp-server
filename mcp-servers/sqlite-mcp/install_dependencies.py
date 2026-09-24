"""Create the project virtual environment and install its locked dependencies.

The Microsoft corporate network blocks files.pythonhosted.org, which is where
public PyPI normally serves package artifacts. This installer tries Microsoft's
package-feed proxy first and falls back to public PyPI when the proxy is not
available. Package hashes in requirements.txt are enforced for either source.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path


REQUIRED_PYTHON = (3, 13, 15)
MICROSOFT_INDEX = "https://packagefeedproxy.microsoft.io/pypi/simple/"
PUBLIC_INDEX = "https://pypi.org/simple/"


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _install(python: Path, requirements: Path, index_url: str) -> bool:
    print(f"Installing locked dependencies from {index_url}", flush=True)
    env = os.environ.copy()
    # An enterprise-managed shell may set this globally. The installer always
    # supplies an explicit index, so leaving PIP_NO_INDEX enabled would prevent
    # both the Microsoft proxy and the public fallback from being used.
    env.pop("PIP_NO_INDEX", None)

    result = subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "--isolated",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--require-hashes",
            "--retries",
            "1",
            "--timeout",
            "15",
            "--index-url",
            index_url,
            "-r",
            str(requirements),
        ],
        cwd=requirements.parent,
        env=env,
        check=False,
    )
    return result.returncode == 0


def _ensure_pip(python: Path) -> bool:
    check = subprocess.run(
        [str(python), "-m", "pip", "--version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if check.returncode == 0:
        return True

    print("pip is missing from .venv; installing Python's bundled pip.", flush=True)
    result = subprocess.run(
        [str(python), "-m", "ensurepip", "--upgrade"],
        cwd=python.parent,
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install the exact, hash-locked dependencies into .venv."
    )
    parser.add_argument(
        "--index-url",
        help="Use only this package index instead of automatic proxy fallback.",
    )
    args = parser.parse_args()

    actual_python = sys.version_info[:3]
    if actual_python != REQUIRED_PYTHON:
        required = ".".join(map(str, REQUIRED_PYTHON))
        actual = ".".join(map(str, actual_python))
        print(
            f"Python {required} is required, but this command is using {actual}.",
            file=sys.stderr,
        )
        return 2

    project_dir = Path(__file__).resolve().parent
    requirements = project_dir / "requirements.txt"
    venv_dir = project_dir / ".venv"
    python = _venv_python(venv_dir)

    if not requirements.is_file():
        print(f"Missing dependency lock: {requirements}", file=sys.stderr)
        return 2

    if not python.is_file():
        print(f"Creating virtual environment at {venv_dir}", flush=True)
        venv.EnvBuilder(with_pip=True).create(venv_dir)

    if not _ensure_pip(python):
        print("Unable to install pip in the virtual environment.", file=sys.stderr)
        return 1

    indexes = [args.index_url] if args.index_url else [MICROSOFT_INDEX, PUBLIC_INDEX]
    for position, index_url in enumerate(indexes):
        if _install(python, requirements, index_url):
            print("Locked dependencies installed successfully.", flush=True)
            return 0
        if position < len(indexes) - 1:
            print(
                "The Microsoft package proxy was unavailable; trying public PyPI.",
                file=sys.stderr,
                flush=True,
            )

    print(
        "Dependency installation failed. See the README network troubleshooting section.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
