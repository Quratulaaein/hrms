from app.embedding_engine import embed_text
from app.vector_store import search_vectors

def find_best_candidates_for_role(role_description: str, top_k=10):
    vector = embed_text(role_description)
    return search_vectors(vector, top_k)
