import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import ChatRequest
from app.services.embedding import embed_text
from app.services.generator import generate_stream
from app.services.retriever import retrieve
from app.services.rewriter import rewrite_question
from app.services.session import QuotaExceeded, check_quota, load_history, save_history

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    redis = request.app.state.redis
    embedding_model = request.app.state.embedding_model
    collection = request.app.state.collection

    # 1. Quota check
    try:
        await check_quota(redis, req.fingerprint, req.session_id)
    except QuotaExceeded as e:
        return JSONResponse(status_code=429, content={"error": e.message})

    # 2. Load history
    history = await load_history(redis, req.session_id)

    # 3. Rewrite question
    try:
        rewritten = await rewrite_question(req.question, history)
    except Exception:
        logger.exception("Question rewrite failed, using original")
        rewritten = req.question

    # 4. Embed & retrieve
    query_vector = embed_text(embedding_model, rewritten)
    chunks = retrieve(collection, query_vector)

    # 5. Stream generation via SSE
    async def event_generator():
        full_answer = []
        try:
            async for token in generate_stream(req.question, history, chunks):
                full_answer.append(token)
                yield {"data": json.dumps({"token": token}, ensure_ascii=False)}

            yield {"data": json.dumps({"done": True})}

            # Save history after complete generation
            answer_text = "".join(full_answer)
            await save_history(redis, req.session_id, req.question, answer_text)
        except Exception:
            logger.exception("Generation error")
            yield {"data": json.dumps({"error": "Generation failed"}, ensure_ascii=False)}

    return EventSourceResponse(event_generator())
