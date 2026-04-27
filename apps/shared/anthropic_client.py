"""
Anthropic API client with prompt caching.
All LLM calls go through here — never call anthropic directly from handlers.
"""
import anthropic
from loguru import logger

_client: anthropic.AsyncAnthropic | None = None


def get_client(api_key: str) -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=api_key)
    return _client


async def ask(
    *,
    api_key: str,
    system: str,
    user: str,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 2048,
    cache_system: bool = True,
) -> str:
    """
    Single-turn LLM call with optional prompt caching on system prompt.
    cache_system=True adds cache_control to system block (saves ~75% tokens on repeated calls).
    """
    client = get_client(api_key)

    system_block: list[anthropic.types.TextBlockParam] = [
        {
            "type": "text",
            "text": system,
            **({"cache_control": {"type": "ephemeral"}} if cache_system else {}),
        }
    ]

    logger.debug(f"Claude call: model={model} sys={len(system)} user={len(user)}")

    message = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_block,
        messages=[{"role": "user", "content": user}],
    )

    usage = message.usage
    logger.debug(
        f"Claude usage: in={usage.input_tokens} out={usage.output_tokens} "
        f"cache_read={getattr(usage, 'cache_read_input_tokens', 0)} "
        f"cache_write={getattr(usage, 'cache_creation_input_tokens', 0)}"
    )

    return message.content[0].text


async def ask_with_history(
    *,
    api_key: str,
    system: str,
    messages: list[dict],
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 2048,
    cache_system: bool = True,
) -> str:
    """Multi-turn call — pass full message history as list of {role, content}."""
    client = get_client(api_key)

    system_block = [
        {
            "type": "text",
            "text": system,
            **({"cache_control": {"type": "ephemeral"}} if cache_system else {}),
        }
    ]

    message = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_block,
        messages=messages,
    )
    return message.content[0].text
