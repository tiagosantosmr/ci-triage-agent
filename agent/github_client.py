"""Thin wrapper around the `gh` CLI. No token management of our own: this
assumes `gh auth login` has already happened, same as a human running it."""

import json
import subprocess
from dataclasses import dataclass


class GhError(RuntimeError):
    pass


def _run_gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise GhError(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


@dataclass
class PullRequest:
    number: int
    title: str
    url: str
    base_ref: str
    head_ref: str
    head_sha: str


def get_pr(repo: str, pr_number: int) -> PullRequest:
    out = _run_gh(
        "pr", "view", str(pr_number),
        "--repo", repo,
        "--json", "number,title,url,baseRefName,headRefName,headRefOid",
    )
    data = json.loads(out)
    return PullRequest(
        number=data["number"],
        title=data["title"],
        url=data["url"],
        base_ref=data["baseRefName"],
        head_ref=data["headRefName"],
        head_sha=data["headRefOid"],
    )


def list_open_prs(repo: str) -> list[int]:
    out = _run_gh("pr", "list", "--repo", repo, "--state", "open", "--json", "number")
    return [item["number"] for item in json.loads(out)]


def comment_on_pr(repo: str, pr_number: int, body: str) -> None:
    _run_gh("pr", "comment", str(pr_number), "--repo", repo, "--body", body)
