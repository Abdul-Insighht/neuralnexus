"""
Temporal Vector Store — Layer 3
────────────────────────────────
Time-aware FAISS vector store with source credibility weighting,
recency bias, and rich metadata for advanced RAG retrieval.
"""

import os
import json
import numpy as np
import faiss
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class VectorChunk:
    """A single chunk stored in the vector store."""
    chunk_id: str
    content: str
    source_id: str
    source_name: str
    embedding: Optional[np.ndarray] = None
    timestamp: str = ""
    quality_score: float = 0.7
    credibility_score: float = 0.7
    entity_tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """A single retrieval result with scoring breakdown."""
    chunk: VectorChunk
    similarity_score: float
    recency_score: float
    credibility_score: float
    final_score: float

    def summary(self) -> str:
        return (f"[Score: {self.final_score:.3f}] "
                f"({self.chunk.source_name}) "
                f"{self.chunk.content[:120]}...")


class TemporalVectorStore:
    """
    FAISS-backed vector store with temporal and credibility-aware retrieval.
    
    Scoring: final = sim_weight * similarity + rec_weight * recency + cred_weight * credibility
    
    Features:
      - Recency-biased retrieval (newer data scored higher)
      - Source credibility weighting
      - Entity-filtered search
      - Quality-aware filtering
    """

    def __init__(self, embedding_dim: int = 768,
                 sim_weight: float = 0.55,
                 rec_weight: float = 0.25,
                 cred_weight: float = 0.20,
                 recency_decay: float = 0.97):
        self.embedding_dim = embedding_dim
        self.sim_weight = sim_weight
        self.rec_weight = rec_weight
        self.cred_weight = cred_weight
        self.recency_decay = recency_decay

        # FAISS index (L2 → we'll convert to cosine via normalization)
        self.index = faiss.IndexFlatIP(embedding_dim)
        self.chunks: List[VectorChunk] = []
        self._chunk_counter = 0

    def add_chunks(self, texts: List[str], embeddings: np.ndarray,
                   source_id: str, source_name: str,
                   quality_score: float = 0.7,
                   credibility_score: float = 0.7,
                   timestamps: List[str] = None,
                   entity_tags_list: List[List[str]] = None,
                   metadata_list: List[Dict] = None):
        """Add multiple chunks with their embeddings."""
        if len(texts) != embeddings.shape[0]:
            raise ValueError("texts and embeddings must have same length")

        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-10)
        normalized = (embeddings / norms).astype("float32")

        for i in range(len(texts)):
            self._chunk_counter += 1
            chunk = VectorChunk(
                chunk_id=f"VC-{self._chunk_counter:06d}",
                content=texts[i],
                source_id=source_id,
                source_name=source_name,
                embedding=normalized[i],
                timestamp=timestamps[i] if timestamps else datetime.now().isoformat(),
                quality_score=quality_score,
                credibility_score=credibility_score,
                entity_tags=entity_tags_list[i] if entity_tags_list else [],
                metadata=metadata_list[i] if metadata_list else {},
            )
            self.chunks.append(chunk)

        self.index.add(normalized)

    def add_single(self, text: str, embedding: np.ndarray,
                   source_id: str, source_name: str,
                   **kwargs) -> str:
        """Add a single chunk. Returns chunk_id."""
        emb = embedding.reshape(1, -1)
        self.add_chunks(
            [text], emb, source_id, source_name,
            quality_score=kwargs.get("quality_score", 0.7),
            credibility_score=kwargs.get("credibility_score", 0.7),
            timestamps=[kwargs.get("timestamp", datetime.now().isoformat())],
            entity_tags_list=[kwargs.get("entity_tags", [])],
            metadata_list=[kwargs.get("metadata", {})],
        )
        return self.chunks[-1].chunk_id

    def search(self, query_embedding: np.ndarray, top_k: int = 8,
               min_quality: float = 0.0,
               source_filter: List[str] = None,
               entity_filter: List[str] = None) -> List[RetrievalResult]:
        """
        Search for similar chunks with temporal and credibility weighting.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            min_quality: Minimum quality score filter
            source_filter: Only include these source names
            entity_filter: Only include chunks containing these entity tags
        """
        if self.index.ntotal == 0:
            return []

        # Normalize query
        q = query_embedding.reshape(1, -1).astype("float32")
        q_norm = np.linalg.norm(q)
        if q_norm > 0:
            q = q / q_norm

        # Search more than needed to allow filtering
        fetch_k = min(top_k * 4, self.index.ntotal)
        similarities, indices = self.index.search(q, fetch_k)

        now = datetime.now()
        results = []

        for rank in range(fetch_k):
            idx = indices[0][rank]
            if idx < 0 or idx >= len(self.chunks):
                continue

            chunk = self.chunks[idx]

            # Apply filters
            if chunk.quality_score < min_quality:
                continue
            if source_filter and chunk.source_name not in source_filter:
                continue
            if entity_filter:
                if not any(tag.lower() in [e.lower() for e in chunk.entity_tags]
                           for tag in entity_filter):
                    # Also check content
                    if not any(tag.lower() in chunk.content.lower()
                               for tag in entity_filter):
                        continue

            # Similarity score (already cosine from IP + normalization)
            sim_score = float(similarities[0][rank])
            sim_score = max(0, min(1, (sim_score + 1) / 2))  # Normalize to [0, 1]

            # Recency score
            try:
                chunk_time = datetime.fromisoformat(chunk.timestamp.replace("Z", ""))
                days_old = (now - chunk_time).days
                rec_score = self.recency_decay ** max(0, days_old)
            except (ValueError, TypeError):
                rec_score = 0.5

            # Credibility score
            cred_score = chunk.credibility_score

            # Final weighted score
            final = (self.sim_weight * sim_score +
                     self.rec_weight * rec_score +
                     self.cred_weight * cred_score)

            results.append(RetrievalResult(
                chunk=chunk,
                similarity_score=sim_score,
                recency_score=rec_score,
                credibility_score=cred_score,
                final_score=final,
            ))

        # Sort by final score and return top_k
        results.sort(key=lambda r: r.final_score, reverse=True)
        return results[:top_k]

    def get_stats(self) -> Dict:
        """Return store statistics."""
        if not self.chunks:
            return {"total_chunks": 0}

        sources = {}
        for c in self.chunks:
            sources[c.source_name] = sources.get(c.source_name, 0) + 1

        return {
            "total_chunks": len(self.chunks),
            "index_size": self.index.ntotal,
            "embedding_dim": self.embedding_dim,
            "sources": sources,
            "avg_quality": np.mean([c.quality_score for c in self.chunks]),
            "avg_credibility": np.mean([c.credibility_score for c in self.chunks]),
        }

    def get_all_from_source(self, source_name: str) -> List[VectorChunk]:
        """Get all chunks from a specific source."""
        return [c for c in self.chunks if c.source_name == source_name]
