import json
import csv
import io

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import Paper, Conference
from .semantic import semantic_search, build_index
from .rag import build_prompt, call_llm


# ── Public views ─────────────────────────────────────────────────────────────

def home(request):
    return render(request, 'papers/index.html')


# ── Auth views ────────────────────────────────────────────────────────────────

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            return render(request, 'papers/admin_login.html', {'error': 'Invalid credentials or not an admin.'})
    return render(request, 'papers/admin_login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


# ── Admin dashboard ───────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
def admin_dashboard(request):
    total_papers      = Paper.objects.count()
    total_conferences = Conference.objects.count()
    recent_papers     = Paper.objects.select_related('conference').order_by('-created_at')[:10]
    context = {
        'total_papers':      total_papers,
        'total_conferences': total_conferences,
        'recent_papers':     recent_papers,
    }
    return render(request, 'papers/admin_dashboard.html', context)


# ── API: Semantic Search ──────────────────────────────────────────────────────

def search_papers(request):
    query      = request.GET.get('q', '').strip()
    conference = request.GET.get('conference', '').strip() or None
    year       = request.GET.get('year', '').strip() or None

    if not query:
        return JsonResponse({'results': [], 'llm_answer': ''})

    papers_with_scores = semantic_search(query, top_k=5, conference=conference, year=year)

    results = []
    for rank, (p, score) in enumerate(papers_with_scores, start=1):
        results.append({
            'rank':       rank,
            'title':      p.title,
            'authors':    p.authors,
            'abstract':   p.abstract,
            'conference': p.conference.name,
            'year':       p.conference.year,
            'doi_url':    p.doi_url,
            'score':      round(score, 4),
        })

    prompt     = build_prompt(query, papers_with_scores)
    llm_answer = call_llm(prompt) if papers_with_scores else ''

    return JsonResponse({'results': results, 'llm_answer': llm_answer})


# ── API: Add single paper ─────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def add_paper(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    title    = data.get('title', '').strip()
    authors  = data.get('authors', '').strip()
    abstract = data.get('abstract', '').strip()
    conf_name= data.get('conference', '').strip()
    year     = data.get('year', '')
    doi_url  = data.get('doi_url', '').strip()

    if not all([title, authors, abstract, conf_name, year]):
        return JsonResponse({'error': 'All fields except DOI are required.'}, status=400)

    try:
        year = int(year)
    except ValueError:
        return JsonResponse({'error': 'Year must be an integer.'}, status=400)

    conference, _ = Conference.objects.get_or_create(name=conf_name, year=year)
    paper = Paper.objects.create(
        title=title,
        authors=authors,
        abstract=abstract,
        conference=conference,
        doi_url=doi_url,
    )

    # Rebuild FAISS index so new paper is searchable immediately
    build_index()

    return JsonResponse({'success': True, 'id': paper.id, 'message': f'Paper "{title}" added successfully.'})


# ── API: Delete paper ─────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
@require_http_methods(['DELETE'])
def delete_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    title = paper.title
    paper.delete()
    build_index()
    return JsonResponse({'success': True, 'message': f'Paper "{title}" deleted.'})


# ── API: Bulk upload (CSV / JSON) ─────────────────────────────────────────────

@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def bulk_upload(request):
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'error': 'No file provided.'}, status=400)

    filename = uploaded_file.name.lower()
    created  = 0
    errors   = []

    try:
        if filename.endswith('.csv'):
            text    = uploaded_file.read().decode('utf-8-sig')
            reader  = csv.DictReader(io.StringIO(text))
            for i, row in enumerate(reader, start=2):
                try:
                    year = int(row.get('year', 0))
                    conf, _ = Conference.objects.get_or_create(
                        name=row['conference'].strip(), year=year)
                    Paper.objects.create(
                        title=row['title'].strip(),
                        authors=row.get('authors', '').strip(),
                        abstract=row.get('abstract', '').strip(),
                        doi_url=row.get('doi_url', '').strip(),
                        conference=conf,
                    )
                    created += 1
                except Exception as e:
                    errors.append(f"Row {i}: {e}")

        elif filename.endswith('.json'):
            data = json.loads(uploaded_file.read().decode('utf-8'))
            if not isinstance(data, list):
                return JsonResponse({'error': 'JSON must be a list of paper objects.'}, status=400)
            for i, item in enumerate(data, start=1):
                try:
                    year = int(item.get('year', 0))
                    conf, _ = Conference.objects.get_or_create(
                        name=item['conference'].strip(), year=year)
                    Paper.objects.create(
                        title=item['title'].strip(),
                        authors=item.get('authors', '').strip(),
                        abstract=item.get('abstract', '').strip(),
                        doi_url=item.get('doi_url', '').strip(),
                        conference=conf,
                    )
                    created += 1
                except Exception as e:
                    errors.append(f"Item {i}: {e}")
        else:
            return JsonResponse({'error': 'Only .csv and .json files are supported.'}, status=400)

        if created > 0:
            build_index()

        return JsonResponse({
            'success': True,
            'created': created,
            'errors':  errors,
            'message': f'{created} paper(s) imported successfully. {len(errors)} error(s).',
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── API: List papers (for dashboard table) ────────────────────────────────────

@login_required(login_url='admin_login')
def list_papers(request):
    papers = Paper.objects.select_related('conference').order_by('-created_at')[:50]
    data   = [{
        'id':         p.id,
        'title':      p.title,
        'authors':    p.authors,
        'conference': p.conference.name,
        'year':       p.conference.year,
        'created_at': p.created_at.strftime('%Y-%m-%d'),
    } for p in papers]
    return JsonResponse({'papers': data, 'total': Paper.objects.count()})


# ── API: Stats ────────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
def stats(request):
    import os
    from django.conf import settings as dj_settings
    indexed = 0
    if os.path.exists(dj_settings.FAISS_INDEX_PATH):
        try:
            import faiss
            idx = faiss.read_index(dj_settings.FAISS_INDEX_PATH)
            indexed = idx.ntotal
        except Exception:
            pass
    return JsonResponse({
        'total_papers':      Paper.objects.count(),
        'total_conferences': Conference.objects.count(),
        'indexed':           indexed,
    })
