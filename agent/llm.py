"""Picks a chat model from whichever provider is configured. Kept
intentionally thin: swapping providers should mean changing this one
function, nothing else.

Checked in order:
1. LLM_BASE_URL + LLM_API_KEY - any OpenAI-compatible endpoint (a self-hosted
   proxy, Nebius, DeepInfra, etc). LLM_MODEL picks the model string it sends.
2. OPENAI_API_KEY - OpenAI directly.
3. ANTHROPIC_API_KEY - Anthropic directly.
"""

import os


def get_model(temperature: float = 0):
    if os.environ.get("LLM_BASE_URL") and os.environ.get("LLM_API_KEY"):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            base_url=os.environ["LLM_BASE_URL"],
            api_key=os.environ["LLM_API_KEY"],
            model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
            temperature=temperature,
        )

    if os.environ.get("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini", temperature=temperature)

    if os.environ.get("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model="claude-sonnet-4-5", temperature=temperature)

    raise RuntimeError(
        "No LLM configured. Set LLM_BASE_URL + LLM_API_KEY (any OpenAI-compatible "
        "provider), or OPENAI_API_KEY, or ANTHROPIC_API_KEY."
    )
