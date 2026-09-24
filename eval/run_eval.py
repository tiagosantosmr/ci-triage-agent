"""Runs the classifier against the labeled PRs in triage-demo and reports
accuracy. This is the difference between "it seemed to work" and a number."""

import json
from pathlib import Path

from agent.classify import classify_failure
from agent.github_client import get_failed_log, get_pr, get_pr_diff

LABELED_PATH = Path(__file__).parent / "labeled_prs.json"


def run() -> None:
    data = json.loads(LABELED_PATH.read_text())
    repo = data["repo"]

    correct = 0
    for case in data["cases"]:
        pr_number = case["pr"]
        expected = case["true_category"]

        pr = get_pr(repo, pr_number)
        diff = get_pr_diff(repo, pr_number)
        log = get_failed_log(repo, pr.head_sha)

        result = classify_failure(pr.title, diff, log)
        is_correct = result.category == expected
        correct += is_correct

        status = "OK" if is_correct else "MISS"
        print(
            f"[{status}] PR#{pr_number} expected={expected} "
            f"got={result.category} confidence={result.confidence:.2f}"
        )

    total = len(data["cases"])
    print(f"\n{correct}/{total} correct ({correct / total:.0%})")


if __name__ == "__main__":
    run()
