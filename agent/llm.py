"""Picks a chat model from whichever provider key is set. Kept intentionally
thin: swapping providers should mean changing this one function, nothing else."""

import os


def get_model(temperature: float = 0):
    if os.environ.get("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini", temperature=temperature)

    if os.environ.get("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model="claude-sonnet-4-5", temperature=temperature)

    raise RuntimeError(
        "No LLM API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY."
    )
