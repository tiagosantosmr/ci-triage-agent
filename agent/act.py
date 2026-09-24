"""Decides what to do with a classified failure, and does it. The only
category that touches code is real_bug, and only after the fix has
actually passed in an isolated sandbox - everything else just comments."""

from pathlib import Path

from agent import github_client
from agent.classify import Triage
from agent.propose_fix import file_touched_by_diff, propose_fix
from agent.sandbox import isolated_checkout, run_tests

CONFIDENCE_THRESHOLD = 0.85


def _comment_for(triage: Triage) -> str:
    label = {
        "flaky_test": "flaky test",
        "dependency_issue": "dependency issue",
        "unclear": "unclear - needs a human",
        "real_bug": "real bug (but confidence too low to auto-fix)",
    }[triage.category]

    return (
        f"**ci-triage-agent**: classified as `{triage.category}` ({label}), "
        f"confidence {triage.confidence:.0%}.\n\n{triage.reasoning}"
    )


def handle(repo: str, pr_number: int, local_path: Path, triage: Triage, diff: str, ci_log: str, similar_fixes: str) -> str:
    """Returns a short description of what was done, for logging/CLI output."""

    if triage.category != "real_bug" or triage.confidence < CONFIDENCE_THRESHOLD:
        github_client.comment_on_pr(repo, pr_number, _comment_for(triage))
        return f"commented ({triage.category}, confidence {triage.confidence:.0%})"

    pr = github_client.get_pr(repo, pr_number)
    file_path = file_touched_by_diff(diff)
    current_content = (local_path / file_path).read_text()

    fix = propose_fix(file_path, current_content, diff, ci_log, similar_fixes)

    with isolated_checkout(local_path, f"origin/{pr.head_ref}") as worktree:
        (worktree / fix.file_path).write_text(fix.new_content)
        result = run_tests(worktree)

    if not result.passed:
        github_client.comment_on_pr(
            repo, pr_number,
            f"**ci-triage-agent**: attempted an automatic fix for this real_bug "
            f"but the sandboxed test run still failed, so nothing was pushed.\n\n"
            f"Proposed fix:\n{fix.explanation}\n\n"
            f"Test output:\n```\n{result.output[-2000:]}\n```",
        )
        return "attempted fix failed sandbox verification, commented instead"

    sha = github_client.push_fix_commit(
        local_path, pr.head_ref, fix.file_path, fix.new_content,
        message=f"Fix: {fix.explanation}",
    )
    github_client.comment_on_pr(
        repo, pr_number,
        f"**ci-triage-agent**: classified as `real_bug` (confidence {triage.confidence:.0%}), "
        f"proposed and verified a fix, pushed as {sha[:7]}.\n\n{fix.explanation}",
    )
    return f"pushed verified fix {sha[:7]}"
