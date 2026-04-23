# Smart Conference Assistant

A Django-based semantic paper search engine for academic conferences, with:
- **Semantic search** powered by sentence-transformers + FAISS
- **RAG (Retrieval-Augmented Generation)** using the professor's LLM API at `http://cmsai:8000/generate/`
- **Admin dashboard** for bulk CSV/JSON upload, manual paper entry, and deletion
- **Login-protected** admin area

1. Go to http://127.0.0.1:8000
2. Type something like: `transformer attention mechanism` and hit Search
3. You'll see ranked papers with similarity scores + the LLM's AI summary (if the LLM is reachable)
4. Click **Why this matches** on any card to expand
5. Toggle **Best Match** to collapse to just the top result
6. Go to `/login/` dashboard to add more papers


