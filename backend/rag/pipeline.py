"""
ChromaDB RAG pipeline.

Embeds and stores all policy-relevant data (census tracts, FRED indicators,
Tavily search results) in a local vector store. Agents query this store
to retrieve the most relevant context for their specific analysis angle.

Uses sentence-transformers (runs locally, no API cost) for embeddings.
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
import pandas as pd

# Persist the vector store to disk so we only embed once
CHROMA_PATH = Path(__file__).parent.parent.parent / "data" / "chroma_db"

# all-MiniLM-L6-v2: fast, small, good quality for semantic similarity
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "urban_policy_context"

CHUNK_SIZE = 500    # characters per chunk
CHUNK_OVERLAP = 50  # characters of overlap between chunks

_client = None
_collection = None
_embedder = None


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        print("Loading embedding model (first run only)...")
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def _get_collection():
    global _client, _collection
    if _collection is None:
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks for better retrieval."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if len(c.strip()) > 20]


def ingest_documents(documents: list[dict]) -> int:
    """
    Embed and store documents in ChromaDB.

    Each document must have: {text: str, source: str, type: str}
    Returns number of chunks ingested.
    """
    collection = _get_collection()
    embedder = _get_embedder()

    all_chunks = []
    all_ids = []
    all_metadatas = []

    for doc_idx, doc in enumerate(documents):
        chunks = _chunk_text(doc["text"])
        for chunk_idx, chunk in enumerate(chunks):
            chunk_id = f"{doc['type']}_{doc_idx}_{chunk_idx}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadatas.append({
                "source": doc["source"],
                "type": doc["type"],
                "chunk_idx": chunk_idx,
            })

    if not all_chunks:
        return 0

    # Embed in batches of 64 to avoid memory issues
    batch_size = 64
    all_embeddings = []
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        embeddings = embedder.encode(batch, show_progress_bar=False).tolist()
        all_embeddings.extend(embeddings)

    # Upsert so re-running doesn't create duplicates
    collection.upsert(
        ids=all_ids,
        documents=all_chunks,
        embeddings=all_embeddings,
        metadatas=all_metadatas,
    )

    return len(all_chunks)


def retrieve(query: str, k: int = 5, doc_type: str = None) -> list[dict]:
    """
    Semantic search — returns the k most relevant chunks for a query.

    Optionally filter by doc_type: "census" | "fred" | "tavily"
    Each result has: text, source, type, similarity_score
    """
    collection = _get_collection()
    embedder = _get_embedder()

    query_embedding = embedder.encode([query], show_progress_bar=False).tolist()

    where_filter = {"type": doc_type} if doc_type else None

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(k, collection.count() or 1),
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for i, doc in enumerate(results["documents"][0]):
        output.append({
            "text": doc,
            "source": results["metadatas"][0][i]["source"],
            "type": results["metadatas"][0][i]["type"],
            "similarity_score": round(1 - results["distances"][0][i], 3),
        })
    return output


def ingest_policy_data(census_df: pd.DataFrame, fred_data: dict, tavily_results: list[dict]) -> int:
    """
    Converts all three data sources into documents and ingests them all.
    Returns total number of chunks stored.
    """
    documents = []

    # Census: one text description per tract
    for _, row in census_df.iterrows():
        text = (
            f"Census tract {row['tract_id']} in Manhattan: "
            f"Population {int(row['population']):,}. "
            f"Median household income ${int(row['median_income']):,}/year. "
            f"Median gross rent ${int(row['median_rent']):,}/month. "
            f"Severely rent-burdened (50%+ income on rent): {row['rent_burden_pct']:.1f}% of residents. "
            f"Minority population (Hispanic + Black): {row['minority_pct']:.1f}%. "
            f"Population below poverty line: {int(row['poverty_pop']):,}."
        )
        documents.append({"text": text, "source": f"census_tract_{row['tract_id']}", "type": "census"})

    # FRED: one text description per series
    for series_id, series_data in fred_data.items():
        obs = series_data.get("observations", [])
        if not obs:
            continue
        latest = obs[0]
        oldest = obs[-1]
        description = series_data["description"]
        try:
            pct_change = ((latest["value"] - oldest["value"]) / oldest["value"]) * 100
            text = (
                f"Economic indicator — {description} (FRED series {series_id}): "
                f"Most recent value {latest['value']:.2f} as of {latest['date']}. "
                f"Change over period: {pct_change:+.1f}%. "
                f"This is a key macroeconomic signal for NYC housing market analysis."
            )
        except (TypeError, ZeroDivisionError):
            text = f"Economic indicator — {description}: {latest['value']} as of {latest['date']}."
        documents.append({"text": text, "source": f"fred_{series_id}", "type": "fred"})

    # Tavily: ingest each article's content directly
    for i, result in enumerate(tavily_results):
        text = f"Policy research: {result['title']}\nSource: {result['url']}\n{result['content']}"
        documents.append({"text": text, "source": result["url"], "type": "tavily"})

    total = ingest_documents(documents)
    return total


def get_collection_count() -> int:
    return _get_collection().count()
