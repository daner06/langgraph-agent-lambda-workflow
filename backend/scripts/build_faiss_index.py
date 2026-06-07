#!/usr/bin/env python
"""
Build a FAISS vector index from the curated research documents (supports .md, .txt, .rst, .pdf).

Usage (from repo root or backend/):
    python -m backend.scripts.build_faiss_index
    # or
    cd backend && python scripts/build_faiss_index.py --docs-dir docs --index-dir faiss_index

For PDFs, text is extracted per-page and the source metadata includes page numbers (e.g. "report.pdf (p. 2)").

Requires AWS credentials with Bedrock embedding model access (same as the agent).
"""

import argparse
import os
from pathlib import Path
from typing import List

from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


def find_documents(docs_dir: Path) -> List[Path]:
    exts = {".md", ".txt", ".rst", ".pdf"}
    files: List[Path] = []
    for p in docs_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    return sorted(files)


def load_documents(paths: List[Path]) -> List[Document]:
    docs: List[Document] = []
    for path in paths:
        suffix = path.suffix.lower()
        try:
            if suffix == ".pdf":
                reader = PdfReader(str(path))
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        docs.append(
                            Document(
                                page_content=page_text,
                                metadata={
                                    "source": f"{path.name} (p.{i+1})",
                                    "path": str(path),
                                    "page": i + 1,
                                },
                            )
                        )
            else:
                text = path.read_text(encoding="utf-8")
                docs.append(
                    Document(
                        page_content=text,
                        metadata={"source": path.name, "path": str(path)},
                    )
                )
        except Exception as e:
            print(f"WARNING: failed to read {path}: {e}")
    return docs


def chunk_documents(docs: List[Document], chunk_size: int = 700, chunk_overlap: int = 120) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)


def build_index(docs_dir: Path, index_dir: Path, embedding_model: str) -> None:
    print(f"Scanning documents in: {docs_dir}")
    files = find_documents(docs_dir)
    print(f"Found {len(files)} document file(s)")

    raw_docs = load_documents(files)
    if not raw_docs:
        print("No documents found. Nothing to index.")
        return

    chunks = chunk_documents(raw_docs)
    print(f"Split into {len(chunks)} chunks (target ~{700} chars)")

    print(f"Embedding with Bedrock model: {embedding_model} (region eu-west-2)")
    embeddings = BedrockEmbeddings(
        model_id=embedding_model,
        region_name="eu-west-2",
    )

    print("Building FAISS index (this calls Bedrock and may take a minute)...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    index_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(index_dir))
    print(f"✅ Saved FAISS index to: {index_dir.resolve()}")
    print(f"   Files: index.faiss, index.pkl")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-dir", default="docs", help="Directory containing .md/.txt/.pdf research documents")
    parser.add_argument("--index-dir", default="faiss_index", help="Output directory for the FAISS index")
    parser.add_argument(
        "--embedding-model",
        default=os.environ.get("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0"),
        help="Bedrock embedding model ID",
    )
    args = parser.parse_args()

    # Resolve relative to this script's location (backend/scripts/ -> backend/)
    script_dir = Path(__file__).resolve().parent
    backend_dir = script_dir.parent

    docs_path = (backend_dir / args.docs_dir).resolve()
    index_path = (backend_dir / args.index_dir).resolve()

    if not docs_path.exists():
        print(f"ERROR: docs directory not found: {docs_path}")
        raise SystemExit(1)

    build_index(docs_path, index_path, args.embedding_model)


if __name__ == "__main__":
    main()
