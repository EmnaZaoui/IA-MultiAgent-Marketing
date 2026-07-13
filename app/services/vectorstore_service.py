import os
import uuid

import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIR", "data/chroma_fastriom_kb")
COLLECTION_NAME = "fastriom_features"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

_client = None
_collection = None
_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        _collection = _client.get_or_create_collection(name=COLLECTION_NAME)
    return _collection


def ingest_documents(folder_path: str) -> dict:
    """Découpe et indexe tous les fichiers .md/.txt d'un dossier dans Chroma."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
    model = get_embedding_model()
    collection = get_collection()

    md_files = [f for f in os.listdir(folder_path) if f.endswith((".md", ".txt"))]

    all_chunks, all_ids, all_metadatas = [], [], []

    for filename in sorted(md_files):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        for i, chunk in enumerate(splitter.split_text(content)):
            all_chunks.append(chunk)
            all_ids.append(str(uuid.uuid4()))
            all_metadatas.append({"source": filename, "chunk_index": i})

    if all_chunks:
        embeddings = model.encode(all_chunks, show_progress_bar=False).tolist()
        collection.add(
            ids=all_ids,
            embeddings=embeddings,
            documents=all_chunks,
            metadatas=all_metadatas,
        )

    return {"files_processed": len(md_files), "chunks_indexed": len(all_chunks)}


def search_features(query: str, k: int = 3) -> list[dict]:
    """Recherche sémantique dans la base de connaissances Fastriom.
    Sera utilisée par l'agent Strategist en Sprint 3."""
    model = get_embedding_model()
    collection = get_collection()

    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)

    output = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        output.append({"content": doc, "source": meta.get("source"), "score": float(dist)})

    return output