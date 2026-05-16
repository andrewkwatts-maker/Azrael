"""Core query engine backed by a baked SQLite database — delegates to EntityDB."""
from __future__ import annotations

from pathlib import Path

from eyecore import EntityDB

_BASE_PATH = Path(__file__).parent / "_data" / "azrael.db.gz"


class _AzraelDB(EntityDB):
    def __init__(self) -> None:
        from ._corpus_registry import AZRAEL_DEFAULT_CORPUSES
        super().__init__("azrael", _BASE_PATH, AZRAEL_DEFAULT_CORPUSES)


_db = _AzraelDB()


# ── Public thin wrappers ──────────────────────────────────────────────────────

def Get(name: str) -> dict | None:
    """Find any entity by exact name, then fuzzy name match."""
    return _db.get(name)


def _typed(query: str, *types: str) -> dict | None:
    return _db._typed(query, *types)


def Search(query: str, limit: int = 20, mythology: str | None = None) -> list[dict]:
    """Full-text search across all entities, ranked by relevance."""
    return _db.search(query, limit, mythology)


def ByMythology(mythology: str, limit: int = 500) -> list[dict]:
    """Return all entities from a given mythology."""
    return _db.by_mythology(mythology, limit)


ByCategory = ByMythology
ByEra = ByMythology


def ByType(entity_type: str, mythology: str | None = None, limit: int = 500) -> list[dict]:
    """Return all entities of a given type, optionally filtered."""
    return _db.by_type(entity_type, mythology, limit)


def AllGods(mythology: str | None = None, limit: int = 500) -> list[dict]:
    return ByType("deity", mythology, limit)


def AllCreatures(mythology: str | None = None, limit: int = 500) -> list[dict]:
    return ByType("creature", mythology, limit)


def AllHeroes(mythology: str | None = None, limit: int = 500) -> list[dict]:
    return ByType("hero", mythology, limit)


def Count(entity_type: str | None = None) -> int:
    """Count entities, optionally filtered by type."""
    return _db.count(entity_type)


def GetRandom(entity_type: str | None = None, mythology: str | None = None) -> dict | None:
    """Return a random entity, optionally filtered by type and/or mythology."""
    return _db.get_random(entity_type, mythology)


def GetFuzzy(query: str, limit: int = 5) -> list[dict]:
    """Fuzzy name search — prefix FTS matching with LIKE fallback."""
    return _db.get_fuzzy(query, limit)


def GetMost(field: str = "mythology", limit: int = 10) -> list[dict]:
    """Top groupings by entity count.

    GetMost("mythology") -> [{mythology: "greek", count: 1200}, ...]
    GetMost("type")      -> [{type: "deity", count: 2222}, ...]
    """
    return _db.get_most(field, limit)


def GetAll(entity_type: str | None = None, mythology: str | None = None) -> list[dict]:
    """Return every matching entity with no row limit. Large result sets possible."""
    return _db.get_all(entity_type, mythology)


def GetTopics(query: str | None = None, limit: int = 50) -> list[dict]:
    """List topics, optionally filtered by name query."""
    return _db.get_topics(query, limit)


def GetRelated(name_or_id: str, relation: str | None = None) -> list[dict]:
    """Get topics/entities related to the given topic."""
    return _db.get_related(name_or_id, relation)


def GetTopicTree(root: str) -> dict:
    """Return the full subtree for a topic as a nested dict."""
    return _db.get_topic_tree(root)


def SearchCorpus(query: str, corpus: str | None = None, limit: int = 20) -> list[dict]:
    """Search across downloaded text corpuses."""
    return _db.search_corpus(query, corpus, limit)


def FetchCorpus(name: str) -> str:
    """Download and index a named corpus. Returns local path string."""
    return _db.fetch_corpus(name)


def ListCorpuses() -> list[dict]:
    """List all available corpuses and their download status."""
    return _db.list_corpuses()
