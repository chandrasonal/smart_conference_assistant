# papers/rag.py
import requests
from django.conf import settings


def build_prompt(query: str, papers_with_scores: list) -> str:
    lines = [
        "You are a conference paper assistant.",
        f"User query: {query}",
        "",
        "Here are retrieved papers:",
    ]
    for rank, (p, score) in enumerate(papers_with_scores, start=1):
        lines += [
            f"[{rank}] Title: {p.title}",
            f"Authors: {p.authors}",
            f"Conference: {p.conference.name} {p.conference.year}",
            f"Abstract: {p.abstract}",
            f"Similarity score: {score:.3f}",
            "",
        ]

    lines.append(
        "Task: Based ONLY on these abstracts:\n"
        "1) Identify the single best match and explain why.\n"
        "2) List the other papers in ranked order with a short reason each.\n"
        "For every paper you mention include title, authors, conference+year, "
        "and a 'why this matches' sentence.\n"
        "Do NOT invent any new metadata. Only use what is in the abstracts above."
    )
    return "\n".join(lines)


def call_llm(prompt: str) -> str:
    """
    Calls the professor's LLM API at settings.LLM_API_URL.
    Returns the generated text, or an error string on failure.
    """
    payload = {
        "prompt": prompt,
        "max_tokens": 1024,
    }
    try:
        resp = requests.post(settings.LLM_API_URL, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Professor's API returns {"response": "..."}
        return data.get("response", "")
    except requests.exceptions.ConnectionError:
        return (
            "[LLM Unavailable] The professor's LLM server is not reachable at "
            f"{settings.LLM_API_URL}. Semantic search results are still shown above."
        )
    except requests.exceptions.Timeout:
        return "[LLM Timeout] The LLM server took too long to respond."
    except Exception as e:
        return f"[LLM Error] {str(e)}"
