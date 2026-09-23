# ci-triage-agent

An agent that triages failing CI runs on a real GitHub repo. It reads the
failure, retrieves similar past fixes from the target repo's own git
history, classifies the failure, and acts on it:

- **real bug, high confidence** — writes a patch, runs the target repo's
  test suite in an isolated clone, and opens a PR only if the suite passes.
- **flaky test / dependency issue / unclear** — comments on the PR with its
  reasoning instead of touching code.

Built against [triage-demo](https://github.com/tiagosantosmr/triage-demo),
a small real repo with real git history and four open PRs, each with a
known, labeled failure type, used as this project's eval set.

## Setup

```
pip install -e ".[dev]"
export OPENAI_API_KEY=...   # or ANTHROPIC_API_KEY, see agent/llm.py
```

Requires the `gh` CLI, authenticated with `repo` scope, for reading CI
status and opening PRs/comments.

## Usage

```
python -m agent.cli triage --repo tiagosantosmr/triage-demo --pr 1
python -m agent.cli triage --repo tiagosantosmr/triage-demo --all-open
```

## Eval

```
python -m eval.run_eval
```

Runs the classifier against `eval/labeled_prs.json` (the four triage-demo
PRs, hand-labeled with their true cause) and reports accuracy.
