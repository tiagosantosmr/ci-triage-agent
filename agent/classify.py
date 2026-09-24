"""Classifies a CI failure into one of four categories the rest of the
pipeline branches on. Structured output, not free text: everything
downstream needs to switch on this programmatically."""

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from agent.llm import get_model

Category = Literal["real_bug", "flaky_test", "dependency_issue", "unclear"]


class Triage(BaseModel):
    category: Category
    confidence: float = Field(ge=0, le=1)
    reasoning: str


_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You triage CI failures for a software team. Given the failed test "
        "output and the PR's diff, classify the failure into exactly one "
        "category:\n"
        "- real_bug: the code change introduced an actual logic error\n"
        "- flaky_test: the test is inherently unreliable (timing, ordering, "
        "environment-dependent), the code itself is likely fine\n"
        "- dependency_issue: the failure is an import/environment error, not "
        "a logic problem (e.g. a missing package)\n"
        "- unclear: you cannot confidently tell without asking a human, for "
        "example the test's stated expectation conflicts with existing "
        "behavior and it's not obvious which one is wrong\n\n"
        "Be conservative: only use real_bug at high confidence if you are "
        "sure the fix is unambiguous.",
    ),
    (
        "human",
        "PR title: {title}\n\nDiff:\n{diff}\n\nFailed CI output:\n{ci_log}",
    ),
])


def classify_failure(title: str, diff: str, ci_log: str) -> Triage:
    # method="function_calling": not every OpenAI-compatible endpoint (e.g. a
    # proxy in front of a non-OpenAI model) supports the native json_schema
    # structured-output mode, but tool calling is much more widely supported.
    model = get_model().with_structured_output(Triage, method="function_calling")
    chain = _PROMPT | model
    return chain.invoke({"title": title, "diff": diff, "ci_log": ci_log})
