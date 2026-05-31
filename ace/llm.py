"""Provider-agnostic LLM wrapper.

The rest of the codebase only ever calls ``complete(system, user)``. Swapping
providers or models is a one-line change in ``.env`` (LLM_PROVIDER / LLM_MODEL),
so the ACE logic never needs to know who is serving tokens.
"""
import os

DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
}


def _provider() -> str:
    return os.environ.get("LLM_PROVIDER", "gemini").lower()


def _model() -> str:
    return os.environ.get("LLM_MODEL", DEFAULT_MODELS[_provider()])


def complete(system: str, user: str) -> str:
    """Return the model's text completion for a system + user prompt."""
    provider = _provider()
    if provider == "gemini":
        return _gemini(system, user)
    if provider == "anthropic":
        return _anthropic(system, user)
    if provider == "openai":
        return _openai(system, user)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}")


def _gemini(system: str, user: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        model=_model(),
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0,
        ),
    )
    return (resp.text or "").strip()


def _anthropic(system: str, user: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=_model(),
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def _openai(system: str, user: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model=_model(),
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()
