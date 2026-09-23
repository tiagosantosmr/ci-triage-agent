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


def get_failed_log(repo: str, head_sha: str) -> str:
    """Concatenated failed-step logs from the most recent CI run against head_sha."""
    runs_json = _run_gh("api", f"repos/{repo}/actions/runs?head_sha={head_sha}")
    runs = json.loads(runs_json)["workflow_runs"]
    failed_runs = [r for r in runs if r["conclusion"] == "failure"]
    if not failed_runs:
        return ""

    # push and pull_request events both trigger a run for the same commit;
    # they're identical, so the first one is enough.
    run_id = failed_runs[0]["id"]
    result = subprocess.run(
        ["gh", "run", "view", str(run_id), "--repo", repo, "--log-failed"],
        capture_output=True, text=True,
    )
    return result.stdout
