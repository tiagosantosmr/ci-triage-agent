# ci-triage-agent

An agent that triages failing CI runs on a real GitHub repo. It reads the
failure, retrieves similar past fixes from the target repo's own git
history, classifies the failure, and acts on it:

- **real bug, high confidence** — writes a fix, runs the target repo's test
  suite in an isolated `git worktree`, and only pushes it if the suite
  actually passes.
- **flaky test / dependency issue / unclear** — comments on the PR with its
  reasoning instead of touching code.

Built against [triage-demo](https://github.com/tiagosantosmr/triage-demo),
a small real repo with real git history and four PRs, each with a genuine
failing CI run and a known, labeled failure type, used as this project's
eval set.

## Results

Run for real against all four `triage-demo` PRs (`claude-sonnet-5` via an
OpenAI-compatible proxy):

| PR | True cause | Classified as | Confidence | Action taken |
|---|---|---|---|---|
| [#1](https://github.com/tiagosantosmr/triage-demo/pull/1) | real bug | real_bug | 98% | fixed, verified in sandbox, pushed — [CI went green](https://github.com/tiagosantosmr/triage-demo/pull/1) |
| [#2](https://github.com/tiagosantosmr/triage-demo/pull/2) | flaky test | flaky_test | 95% | commented |
| [#3](https://github.com/tiagosantosmr/triage-demo/pull/3) | dependency issue | dependency_issue | 97% | commented |
| [#4](https://github.com/tiagosantosmr/triage-demo/pull/4) | unclear | unclear | 60% | commented |

**4/4 (100%)** on this eval set. The one worth paying attention to isn't the
score, it's the confidence on PR #4: that PR's test asserts a rounding
policy that contradicts the existing implementation, with no way to know
from the code alone which one is "right." A weaker model (an earlier Claude
Sonnet generation, tested during development) classified both PR #2 and
PR #4 as `real_bug` at 95% confidence each — confidently wrong on the two
cases that were designed to be ambiguous. `claude-sonnet-5` was the only one
that dropped its confidence to 60% on the genuinely unclear case instead of
guessing. That gap is the actual finding here: a triage agent is only as
useful as its ability to know when it doesn't know.

## Setup

```
pip install -e ".[dev]"
```

Configure a model in `agent/llm.py`'s priority order: either
`LLM_BASE_URL` + `LLM_API_KEY` (+ optional `LLM_MODEL`) for any
OpenAI-compatible endpoint, or `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`.
Embeddings for retrieval run locally (sentence-transformers), no API key
needed for that part.

Requires the `gh` CLI, authenticated with `repo` scope, for reading CI
status and pushing fixes/comments.

## Usage

```
python -m agent.cli triage --repo tiagosantosmr/triage-demo --pr 1
python -m agent.cli triage --repo tiagosantosmr/triage-demo --all-open
```

## Eval

```
python -m eval.run_eval
```

Runs the classifier against `eval/labeled_prs.json` and reports accuracy.
Note: once a real_bug PR has actually been fixed and pushed (like #1 above),
its CI run no longer fails, so re-running the eval against an
already-resolved PR won't reproduce the original result — the table above
is the real, one-time run against the original broken state.
