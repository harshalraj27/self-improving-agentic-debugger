from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, Final, Optional

import chromadb
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer

logging.getLogger("sentence_transformers").setLevel(logging.ERROR)


class DebuggingMemory:
    _COLLECTION_NAME: Final[str] = "debugging_trajectories"
    _EMBEDDING_MODEL: Final[str] = "all-MiniLM-L6-v2"
    _MAX_QUERY_DISTANCE: Final[float] = 0.55

    def __init__(self, storage_path: str = "data/chroma_db") -> None:
        db_path = Path(storage_path)
        db_path.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=str(db_path))
        self._collection: Collection = self._client.get_or_create_collection(
            name=self._COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._embedder = SentenceTransformer(self._EMBEDDING_MODEL)

    def add_experience(
        self,
        error_trace: str,
        language: str,
        successful_patch: str,
    ) -> None:
        record_id = str(uuid.uuid4())
        embedding = self._embed(error_trace)
        self._collection.add(
            ids=[record_id],
            embeddings=[embedding],
            documents=[successful_patch],
            metadatas=[
                {
                    "language": language,
                    "error_trace": error_trace,
                }
            ],
        )

    def query_memory(
        self,
        current_error_trace: str,
        language: str,
        top_k: int = 1,
    ) -> Optional[dict[str, str]]:
        if not current_error_trace.strip():
            return None

        query_embedding = self._embed(current_error_trace)
        results: dict[str, Any] = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"language": language},
            include=["documents", "metadatas", "distances"],
        )

        ids = results.get("ids")
        distances = results.get("distances")
        documents = results.get("documents")
        metadatas = results.get("metadatas")

        if not ids or not ids[0]:
            return None

        distance = distances[0][0]
        if distance is None or distance > self._MAX_QUERY_DISTANCE:
            return None

        metadata = metadatas[0][0] if metadatas and metadatas[0] else {}
        document = documents[0][0] if documents and documents[0] else None
        if document is None:
            return None

        return {
            "error_trace": str(metadata.get("error_trace", "")),
            "successful_patch": document,
        }

    def _embed(self, text: str) -> list[float]:
        vector = self._embedder.encode(text, convert_to_numpy=True)
        return vector.tolist()
