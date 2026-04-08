import logging
from contextlib import asynccontextmanager

import chromadb
import redis.asyncio as aioredis
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Loading embedding model: %s", settings.models.embedding)
    app.state.embedding_model = SentenceTransformer(settings.models.embedding)
    logger.info("Embedding model loaded")

    logger.info("Connecting to Redis: %s", settings.redis.url)
    app.state.redis = aioredis.from_url(settings.redis.url, decode_responses=True)
    logger.info("Redis connected")

    logger.info("Initializing Chroma client")
    app.state.chroma = chromadb.PersistentClient(path="./chroma_db")
    app.state.collection = app.state.chroma.get_collection("knowledge_base")
    logger.info("Chroma collection loaded")

    yield

    # Shutdown
    await app.state.redis.close()
    logger.info("Shutdown complete")


app = FastAPI(title="Tron Bot Backend", lifespan=lifespan)

# CORS
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IP rate limiting
from app.middleware.rate_limit import IPRateLimitMiddleware  # noqa: E402

app.add_middleware(IPRateLimitMiddleware)

# Router
from app.routers.chat import router as chat_router  # noqa: E402

app.include_router(chat_router, prefix="/api")
