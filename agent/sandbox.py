"""Runs a target repo's test suite in an isolated worktree, so the agent can
verify a proposed patch actually fixes things before it ever opens a PR."""

import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestResult:
    passed: bool
    output: str


@contextmanager
def isolated_checkout(repo_path: Path, ref: str):
    """A disposable `git worktree` checked out to `ref`. Isolated from
    `repo_path` itself: edits here can't corrupt the cached clone."""
    with tempfile.TemporaryDirectory(prefix="ci-triage-agent-") as tmp:
        worktree = Path(tmp) / "worktree"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), ref],
            cwd=repo_path, check=True, capture_output=True, text=True,
        )
        try:
            yield worktree
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=repo_path, capture_output=True,
            )


def run_tests(worktree: Path) -> TestResult:
    venv = worktree / ".venv"
    subprocess.run(["python3", "-m", "venv", str(venv)], check=True, capture_output=True)

    pip = venv / "bin" / "pip"
    pytest_bin = venv / "bin" / "pytest"

    subprocess.run([str(pip), "install", "-q", "--upgrade", "pip", "setuptools"], check=True, capture_output=True)

    install = subprocess.run(
        [str(pip), "install", "-q", "-e", ".[dev]"],
        cwd=worktree, capture_output=True, text=True,
    )
    if install.returncode != 0:
        return TestResult(passed=False, output=install.stdout + install.stderr)

    test_run = subprocess.run(
        [str(pytest_bin), "-q"],
        cwd=worktree, capture_output=True, text=True,
    )
    return TestResult(passed=test_run.returncode == 0, output=test_run.stdout + test_run.stderr)
