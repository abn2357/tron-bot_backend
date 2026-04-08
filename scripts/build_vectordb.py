#!/usr/bin/env python3
"""Build Chroma vector DB from tronprotocol/documentation-zh."""

import logging
import re
import subprocess
from pathlib import Path

import chromadb
import yaml
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# --- Constants ---
REPO_URL = "https://github.com/tronprotocol/documentation-zh.git"
REPO_DIR = Path("./documentation-zh")
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "knowledge_base"
EMBEDDING_MODEL = "BAAI/bge-base-zh-v1.5"
MAX_CHUNK_CHARS = 1500
MIN_CHUNK_CHARS = 100
BATCH_SIZE = 100


# --- Repository ---
def ensure_repo(repo_url: str, repo_dir: Path) -> None:
    if not repo_dir.exists():
        logger.info("Cloning %s ...", repo_url)
        subprocess.run(["git", "clone", "--depth", "1", repo_url, str(repo_dir)], check=True)
    else:
        logger.info("Pulling latest changes in %s ...", repo_dir)
        subprocess.run(["git", "-C", str(repo_dir), "pull", "--ff-only"], check=True)


# --- Nav Parser ---
def parse_nav(nav: list) -> list[tuple[str, str]]:
    """Recursively extract (title, file_path) from mkdocs nav."""
    results = []
    for item in nav:
        if isinstance(item, str):
            results.append((item, item))
        elif isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, str):
                    results.append((key, value))
                elif isinstance(value, list):
                    results.extend(parse_nav(value))
    return results


def load_nav(mkdocs_path: Path) -> list[tuple[str, str]]:
    with open(mkdocs_path) as f:
        config = yaml.safe_load(f)
    return parse_nav(config["nav"])


# --- Markdown Chunker ---
def split_preserving_code_blocks(text: str) -> list[str]:
    """Split by double-newlines, keeping fenced code blocks intact."""
    code_blocks = []

    def replace_code(match):
        code_blocks.append(match.group(0))
        return f"\x00CODEBLOCK{len(code_blocks) - 1}\x00"

    processed = re.sub(r"```.*?```", replace_code, text, flags=re.DOTALL)
    parts = [p.strip() for p in processed.split("\n\n") if p.strip()]

    restored = []
    for part in parts:
        for i, cb in enumerate(code_blocks):
            part = part.replace(f"\x00CODEBLOCK{i}\x00", cb)
        restored.append(part)

    return restored


def split_large_section(title: str, body: str) -> list[tuple[str, str]]:
    """Split an oversized section into smaller chunks by paragraphs."""
    blocks = split_preserving_code_blocks(body)

    chunks = []
    current = []
    current_len = 0

    for block in blocks:
        if current_len + len(block) > MAX_CHUNK_CHARS and current:
            chunks.append("\n\n".join(current))
            current = [block]
            current_len = len(block)
        else:
            current.append(block)
            current_len += len(block)

    if current:
        chunks.append("\n\n".join(current))

    if len(chunks) == 1:
        return [(title, chunks[0])]
    return [(f"{title} ({i + 1}/{len(chunks)})", c) for i, c in enumerate(chunks)]


def split_by_headers(text: str) -> list[tuple[str, str]]:
    """Split markdown into (section_title, section_body) pairs by headers."""
    pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    sections = []
    if not matches or matches[0].start() > 0:
        intro_end = matches[0].start() if matches else len(text)
        intro_text = text[:intro_end].strip()
        if intro_text:
            sections.append(("概述", intro_text))

    for i, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((title, body))

    return sections


def chunk_markdown(text: str, source_file: str, nav_title: str) -> list[dict]:
    """Split a markdown file into chunks with metadata."""
    raw_sections = split_by_headers(text)

    sections = []
    for title, body in raw_sections:
        if len(body) > MAX_CHUNK_CHARS:
            sections.extend(split_large_section(title, body))
        else:
            sections.append((title, body))

    chunks = []
    for idx, (section_title, body) in enumerate(sections):
        if len(body) < MIN_CHUNK_CHARS:
            continue

        chunk_text = f"[来源: {source_file}] [章节: {section_title}]\n\n{body}"
        chunk_id = f"{source_file}::{section_title}::{idx}"
        chunks.append({
            "chunk_id": chunk_id,
            "text": chunk_text,
            "source": source_file,
            "section": section_title,
        })

    return chunks


# --- Build Database ---
def build_database(doc_chunks: list[dict], chroma_path: str) -> None:
    """Embed chunks and store in Chroma."""
    logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
    model = SentenceTransformer(EMBEDDING_MODEL)

    logger.info("Embedding %d chunks ...", len(doc_chunks))
    texts = [c["text"] for c in doc_chunks]
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=32,
    ).tolist()

    logger.info("Writing to Chroma at %s ...", chroma_path)
    client = chromadb.PersistentClient(path=chroma_path)

    # Delete and recreate for idempotency
    try:
        client.delete_collection(COLLECTION_NAME)
    except (ValueError, chromadb.errors.NotFoundError):
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "l2"},
    )

    ids = [c["chunk_id"] for c in doc_chunks]
    documents = [c["text"] for c in doc_chunks]
    metadatas = [{"source": c["source"], "section": c["section"]} for c in doc_chunks]

    for i in range(0, len(ids), BATCH_SIZE):
        end = min(i + BATCH_SIZE, len(ids))
        collection.add(
            ids=ids[i:end],
            embeddings=embeddings[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
        )

    logger.info("Collection '%s' created with %d entries", COLLECTION_NAME, len(ids))


# --- Main ---
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build Chroma vector DB from TRON documentation")
    parser.add_argument("--repo-url", default=REPO_URL, help="Git repo URL")
    parser.add_argument("--repo-dir", default=str(REPO_DIR), help="Local clone directory")
    parser.add_argument("--chroma-path", default=CHROMA_PATH, help="Chroma DB output path")
    parser.add_argument("--skip-clone", action="store_true", help="Skip git clone/pull")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not args.skip_clone:
        ensure_repo(args.repo_url, Path(args.repo_dir))

    nav_entries = load_nav(Path(args.repo_dir) / "mkdocs.yml")
    logger.info("Found %d files in nav", len(nav_entries))

    all_chunks = []
    docs_dir = Path(args.repo_dir) / "docs"
    for nav_title, rel_path in nav_entries:
        file_path = docs_dir / rel_path
        if not file_path.exists():
            logger.warning("File not found: %s", file_path)
            continue
        text = file_path.read_text(encoding="utf-8")
        chunks = chunk_markdown(text, rel_path, nav_title)
        logger.info("  %s -> %d chunks", rel_path, len(chunks))
        all_chunks.extend(chunks)

    logger.info("Total chunks: %d", len(all_chunks))

    build_database(all_chunks, args.chroma_path)
    logger.info("Done!")


if __name__ == "__main__":
    main()
