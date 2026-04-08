import anthropic

from app.config import settings

client = anthropic.Anthropic()

REWRITE_SYSTEM_PROMPT = """你是一个查询重写助手。你的任务是将用户的提问改写为更适合向量检索的独立查询。

规则：
1. 如果用户的提问包含指代（如"那个"、"第二个"、"它"），根据对话历史补全为完整的独立问题。
2. 如果用户的提问已经是完整的独立问题，进行适当优化使其更适合语义检索。
3. 只输出重写后的查询，不要输出其他内容。"""


async def rewrite_question(question: str, history: list[dict]) -> str:
    """Rewrite user question using Claude Sonnet for better retrieval."""
    messages = []
    for entry in history:
        messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": question})

    response = client.messages.create(
        model=settings.models.rewriter,
        max_tokens=256,
        system=REWRITE_SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text
