from collections.abc import AsyncGenerator

import anthropic

from app.config import settings

client = anthropic.Anthropic()

SYSTEM_PROMPT_WITH_CONTEXT = """你是一个知识问答助手。请根据以下参考资料回答用户的问题。

参考资料：
{chunks}

规则：
1. 优先基于参考资料回答，确保准确性。
2. 如果参考资料不足以回答，可结合通用知识补充，但需注明。
3. 用中文回答，语言简洁清晰。"""

SYSTEM_PROMPT_NO_CONTEXT = """你是一个知识问答助手。

注意：未找到与问题直接相关的参考资料，以下回答基于通用知识，可能不完全准确。

规则：
1. 诚实告知用户回答未基于知识库。
2. 用中文回答，语言简洁清晰。"""


async def generate_stream(
    question: str,
    history: list[dict],
    retrieved_chunks: list[str],
) -> AsyncGenerator[str, None]:
    """Stream answer tokens from Claude Opus."""
    if retrieved_chunks:
        chunks_text = "\n\n---\n\n".join(retrieved_chunks)
        system = SYSTEM_PROMPT_WITH_CONTEXT.format(chunks=chunks_text)
    else:
        system = SYSTEM_PROMPT_NO_CONTEXT

    messages = []
    for entry in history:
        messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": question})

    with client.messages.stream(
        model=settings.models.generator,
        max_tokens=2048,
        system=system,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text
