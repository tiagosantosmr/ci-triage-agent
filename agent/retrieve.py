"""RAG over a target repo's own git history. The commit that fixed the
negative-price parsing bug in triage-demo, for example, should be one of
the top hits when triaging a new failure that looks similar."""

import subprocess
from pathlib import Path

from langchain_core.documents import Document

CACHE_DIR = Path.home() / ".cache" / "ci-triage-agent" / "repos"

_COMMIT_SEP = "\x1e"  # ASCII record separator, unlikely to appear in a diff


def clone_or_update(repo: str) -> Path:
    """repo is 'owner/name'. Returns the local clone path, cloning to
    ~/.cache/ci-triage-agent/repos/<owner>/<name> if it isn't there yet."""
    local_path = CACHE_DIR / repo
    if local_path.exists():
        subprocess.run(["git", "fetch", "--all"], cwd=local_path, check=True, capture_output=True)
        return local_path

    local_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["gh", "repo", "clone", repo, str(local_path)],
        check=True, capture_output=True, text=True,
    )
    return local_path


def load_commit_documents(local_path: Path, branch: str = "main") -> list[Document]:
    """One Document per commit on `branch`: message + diff, so retrieval can
    match on either what a commit says it did or what it actually changed."""
    log = subprocess.run(
        ["git", "log", branch, f"--pretty=format:{_COMMIT_SEP}%H%n%s%n%b%n---DIFF---"],
        cwd=local_path, check=True, capture_output=True, text=True,
    ).stdout

    documents = []
    for entry in log.split(_COMMIT_SEP):
        entry = entry.strip()
        if not entry:
            continue
        header, _, rest = entry.partition("\n")
        sha = header.strip()
        message, _, _ = rest.partition("---DIFF---")

        diff = subprocess.run(
            ["git", "show", sha, "--stat", "-p"],
            cwd=local_path, check=True, capture_output=True, text=True,
        ).stdout

        documents.append(
            Document(
                page_content=f"{message.strip()}\n\n{diff}",
                metadata={"sha": sha, "message": message.strip()},
            )
        )
    return documents
