# papers/semantic.py
import os
import numpy as np
from django.conf import settings

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model      = None
_index      = None
_paper_ids  = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def build_index():
    """Re-build the FAISS index from all papers in the DB. Call after bulk import."""
    import faiss
    from .models import Paper

    global _index, _paper_ids

    papers = list(Paper.objects.select_related('conference').all())
    if not papers:
        _index = None
        _paper_ids = None
        return

    model = _get_model()
    abstracts  = [p.abstract for p in papers]
    embeddings = model.encode(abstracts, convert_to_numpy=True, show_progress_bar=False).astype('float32')

    dim   = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

    _index     = index
    _paper_ids = np.array([p.id for p in papers])

    faiss.write_index(index, settings.FAISS_INDEX_PATH)
    np.save(settings.FAISS_IDS_PATH, _paper_ids)


def _load_index():
    """Load FAISS index from disk if not already in memory."""
    import faiss
    global _index, _paper_ids

    if _index is not None:
        return

    if os.path.exists(settings.FAISS_INDEX_PATH) and os.path.exists(settings.FAISS_IDS_PATH):
        _index     = faiss.read_index(settings.FAISS_INDEX_PATH)
        _paper_ids = np.load(settings.FAISS_IDS_PATH)
    else:
        build_index()


def semantic_search(query: str, top_k: int = 5, conference: str = None, year: str = None):
    """
    Returns list of (Paper, score) tuples ordered by semantic similarity.
    Applies optional conference / year filters after retrieval.
    """
    import faiss
    from .models import Paper

    _load_index()

    if _index is None or _index.ntotal == 0:
        return []

    model = _get_model()
    q_emb = model.encode([query], convert_to_numpy=True).astype('float32')
    faiss.normalize_L2(q_emb)

    # Retrieve more candidates so filters still return top_k
    k = min(top_k * 10, _index.ntotal)
    scores, idxs = _index.search(q_emb, k)
    idxs   = idxs[0]
    scores = scores[0]

    results = []
    for i, score in zip(idxs, scores):
        if i == -1:
            continue
        paper_id = int(_paper_ids[i])
        try:
            p = Paper.objects.select_related('conference').get(id=paper_id)
        except Paper.DoesNotExist:
            continue

        if conference and p.conference.name.lower() != conference.lower():
            continue
        if year and str(p.conference.year) != str(year):
            continue

        results.append((p, float(score)))
        if len(results) >= top_k:
            break

    return results
