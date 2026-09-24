"""python -m agent.cli triage --repo owner/name --pr 1
   python -m agent.cli triage --repo owner/name --all-open"""

import argparse

from agent import act, github_client
from agent.classify import classify_failure
from agent.retrieve import build_index, clone_or_update, load_commit_documents, retrieve_similar_commits


def triage_one(repo: str, pr_number: int, local_path, index) -> None:
    pr = github_client.get_pr(repo, pr_number)
    diff = github_client.get_pr_diff(repo, pr_number)
    ci_log = github_client.get_failed_log(repo, pr.head_sha)

    if not ci_log:
        print(f"PR#{pr_number}: no failed CI run found, skipping")
        return

    similar = retrieve_similar_commits(index, diff + ci_log, k=2)
    similar_text = "\n\n".join(d.page_content[:500] for d in similar)

    triage = classify_failure(pr.title, diff, ci_log)
    print(f"PR#{pr_number} [{pr.title}]: {triage.category} ({triage.confidence:.0%})")

    outcome = act.handle(repo, pr_number, local_path, triage, diff, ci_log, similar_text)
    print(f"  -> {outcome}")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    triage_parser = subparsers.add_parser("triage")
    triage_parser.add_argument("--repo", required=True)
    triage_parser.add_argument("--pr", type=int)
    triage_parser.add_argument("--all-open", action="store_true")

    args = parser.parse_args()

    local_path = clone_or_update(args.repo)
    documents = load_commit_documents(local_path)
    index = build_index(documents)

    if args.all_open:
        for pr_number in github_client.list_open_prs(args.repo):
            triage_one(args.repo, pr_number, local_path, index)
    elif args.pr:
        triage_one(args.repo, args.pr, local_path, index)
    else:
        raise SystemExit("pass --pr <number> or --all-open")


if __name__ == "__main__":
    main()
