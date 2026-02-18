import faiss
import numpy as np
import json
from pathlib import Path

VECTOR_DIM = 384
DB_PATH = Path("data/vector_db")
DB_PATH.mkdir(parents=True, exist_ok=True)

index = faiss.IndexFlatIP(VECTOR_DIM)
metadata = []

def add_vector(vector, meta: dict):
    global index, metadata
    index.add(np.array([vector]).astype("float32"))
    metadata.append(meta)

def search_vectors(vector, top_k=5):
    scores, ids = index.search(
        np.array([vector]).astype("float32"),
        top_k
    )

    results = []
    for i in ids[0]:
        if i < len(metadata):
            results.append(metadata[i])

    return results

def save_db():
    faiss.write_index(index, str(DB_PATH / "index.faiss"))
    with open(DB_PATH / "meta.json", "w") as f:
        json.dump(metadata, f)

def load_db():
    global index, metadata
    if (DB_PATH / "index.faiss").exists():
        index = faiss.read_index(str(DB_PATH / "index.faiss"))
        with open(DB_PATH / "meta.json") as f:
            metadata = json.load(f)
