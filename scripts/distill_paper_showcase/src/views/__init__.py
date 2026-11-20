"""View modules for compiled distill paper showcase.

Each view exposes: render(bundle: dict) -> None
"""

from . import abstract, chapters, charts, citations, consolidated, overview

__all__ = [
    "abstract",
    "chapters",
    "charts",
    "citations",
    "consolidated",
    "overview",
]
