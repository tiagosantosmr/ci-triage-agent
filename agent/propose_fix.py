"""Proposes a fix for a real_bug classification: regenerates the affected
file's content, not a line-level patch. Simpler to get right for a single
file, and easy to verify - just write it and run the tests."""

import re

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from agent.llm import get_model

_DIFF_FILE_RE = re.compile(r"^diff --git a/(\S+) b/\S+", re.MULTILINE)


class ProposedFix(BaseModel):
    file_path: str
    new_content: str
    explanation: str


_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You fix a real bug in a Python file. You're given the file's "
        "current (buggy) content, the diff that introduced the bug, the "
        "failing test output, and similar past fixes from this repo's git "
        "history for style reference.\n\n"
        "Return the complete corrected content of the file - not a diff, "
        "the whole file as it should be after the fix. Keep the fix as "
        "small as possible: don't refactor unrelated code.",
    ),
    (
        "human",
        "File: {file_path}\n\nCurrent (buggy) content:\n{current_content}\n\n"
        "Diff that introduced the bug:\n{diff}\n\n"
        "Failing test output:\n{ci_log}\n\n"
        "Similar past fixes in this repo, for style reference:\n{similar_fixes}",
    ),
])


def file_touched_by_diff(diff: str) -> str:
    match = _DIFF_FILE_RE.search(diff)
    if not match:
        raise ValueError("could not find a touched file in the diff")
    return match.group(1)


def propose_fix(file_path: str, current_content: str, diff: str, ci_log: str, similar_fixes: str) -> ProposedFix:
    model = get_model().with_structured_output(ProposedFix, method="function_calling")
    chain = _PROMPT | model
    return chain.invoke({
        "file_path": file_path,
        "current_content": current_content,
        "diff": diff,
        "ci_log": ci_log,
        "similar_fixes": similar_fixes,
    })
