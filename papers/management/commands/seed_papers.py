"""
Management command: python manage.py seed_papers

Seeds the database with sample conference papers and rebuilds the FAISS index.
Run once after 'python manage.py migrate'.
"""
from django.core.management.base import BaseCommand
from papers.models import Conference, Paper
from papers.semantic import build_index

SAMPLE_PAPERS = [
    {
        "conference": "NeurIPS", "year": 2023,
        "title": "Attention Is All You Need: Revisiting Transformers for Long-Context Reasoning",
        "authors": "A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones",
        "abstract": "We propose a novel sequence-to-sequence architecture relying entirely on self-attention, eliminating recurrence and convolution. The model achieves state-of-the-art results on machine translation benchmarks while significantly reducing training time. Multi-head attention allows the model to jointly attend to information from different representation subspaces.",
    },
    {
        "conference": "ICML", "year": 2023,
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": "J. Devlin, M. Chang, K. Lee, K. Toutanova",
        "abstract": "BERT introduces a deep bidirectional language representation model pre-trained on unlabeled text by jointly conditioning on both left and right context in all layers. It achieves state-of-the-art on eleven NLP tasks with minimal task-specific architecture modifications.",
    },
    {
        "conference": "ACL", "year": 2022,
        "title": "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness",
        "authors": "T. Dao, D. Fu, S. Ermon, A. Rudra, C. Ré",
        "abstract": "FlashAttention is an IO-aware exact attention algorithm using tiling to reduce memory reads/writes between GPU HBM and SRAM, enabling 2-4x speedups and up to 20x memory reduction without approximation.",
    },
    {
        "conference": "ICLR", "year": 2022,
        "title": "Scaling Laws for Neural Language Models: Emergent Abilities at Scale",
        "authors": "T. Brown, B. Mann, N. Ryder, M. Subbiah, J. Kaplan",
        "abstract": "We study empirical scaling laws for language model performance. Loss scales as a power-law with model size, dataset size, and compute — with trends spanning more than seven orders of magnitude.",
    },
    {
        "conference": "AAAI", "year": 2021,
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "authors": "P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin",
        "abstract": "We explore retrieval-augmented generation (RAG) for knowledge-intensive NLP. RAG models combine parametric knowledge from a pre-trained language model with non-parametric knowledge retrieved from a dense vector index of Wikipedia, achieving state-of-the-art on open-domain QA tasks.",
    },
    {
        "conference": "CVPR", "year": 2023,
        "title": "DINOv2: Learning Robust Visual Features without Supervision",
        "authors": "M. Oquab, T. Darcet, T. Moutakanni, H. Vo, M. Szafraniec",
        "abstract": "We revisit existing approaches for self-supervised learning from images and propose DINOv2, a method trained on a curated large dataset of diverse images. The resulting features excel on image-level visual recognition tasks, dense prediction tasks, and depth estimation without fine-tuning.",
    },
    {
        "conference": "EMNLP", "year": 2023,
        "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
        "authors": "J. Wei, X. Wang, D. Schuurmans, M. Bosma, B. Ichter, F. Xia",
        "abstract": "We explore how generating a chain of thought — a series of intermediate reasoning steps — significantly improves the ability of large language models to perform complex reasoning tasks including arithmetic, symbolic, and commonsense reasoning.",
    },
    {
        "conference": "KDD", "year": 2022,
        "title": "Graph Neural Networks for Node Classification in Heterogeneous Graphs",
        "authors": "X. Wang, H. Ji, C. Shi, B. Wang, Y. Ye, P. Cui",
        "abstract": "We propose a graph neural network framework specifically designed for heterogeneous graphs, where nodes and edges can be of different types. Our model uses type-specific transformations and hierarchical aggregation to learn rich node representations for downstream classification tasks.",
    },
]


class Command(BaseCommand):
    help = 'Seed the database with sample conference papers and rebuild the FAISS index.'

    def handle(self, *args, **options):
        if Paper.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Database already has papers. Skipping seed. '
                'Run with --force to re-seed.'))
            return

        created = 0
        for d in SAMPLE_PAPERS:
            conf, _ = Conference.objects.get_or_create(name=d['conference'], year=d['year'])
            Paper.objects.create(
                title=d['title'],
                authors=d['authors'],
                abstract=d['abstract'],
                conference=conf,
            )
            created += 1

        self.stdout.write(f'Created {created} papers. Building FAISS index…')
        build_index()
        self.stdout.write(self.style.SUCCESS('Done! FAISS index built.'))
