"""
azrael — Mythology encyclopedia: gods, creatures, heroes, places, items, and more.

Quick start:
    import azrael
    god      = azrael.GetGod("Odin")
    creature = azrael.GetCreature("Hydra")
    results  = azrael.Search("trickster")
    related  = azrael.GetRelated("Zeus")
    topics   = azrael.GetTopics("greek")
    azrael.FetchCorpus("gutenberg-iliad")      # download The Iliad
    hits     = azrael.SearchCorpus("wooden horse")
"""
from __future__ import annotations

from ._query import (
    Get,
    Search,
    ByMythology,
    ByType,
    AllGods,
    AllCreatures,
    AllHeroes,
    Count,
    GetRandom,
    GetFuzzy,
    GetMost,
    GetAll,
    GetTopics,
    GetRelated,
    GetTopicTree,
    SearchCorpus,
    FetchCorpus,
    ListCorpuses,
    _typed,
)


def GetGod(query: str) -> dict | None:
    """Return a deity by name or domain."""
    return _typed(query, "deity")


def GetCreature(query: str) -> dict | None:
    """Return a creature by name or ability."""
    return _typed(query, "creature")


def GetHero(query: str) -> dict | None:
    """Return a hero by name."""
    return _typed(query, "hero")


def GetPlace(query: str) -> dict | None:
    """Return a place by name."""
    return _typed(query, "place")


def GetItem(query: str) -> dict | None:
    """Return an item by name."""
    return _typed(query, "item")


def GetConcept(query: str) -> dict | None:
    """Return a concept by name."""
    return _typed(query, "concept")


def GetSymbol(query: str) -> dict | None:
    """Return a symbol by name."""
    return _typed(query, "symbol")


def GetText(query: str) -> dict | None:
    """Return a sacred text by name."""
    return _typed(query, "text")


def GetMythology(query: str) -> dict | None:
    """Return a mythology collection by name."""
    return _typed(query, "mythology")


__version__ = "1.0.0a0"

__all__ = [
    "Get",
    "GetGod",
    "GetCreature",
    "GetHero",
    "GetPlace",
    "GetItem",
    "GetConcept",
    "GetSymbol",
    "GetText",
    "GetMythology",
    "Search",
    "ByMythology",
    "ByType",
    "AllGods",
    "AllCreatures",
    "AllHeroes",
    "Count",
    "GetRandom",
    "GetFuzzy",
    "GetMost",
    "GetAll",
    "GetTopics",
    "GetRelated",
    "GetTopicTree",
    "SearchCorpus",
    "FetchCorpus",
    "ListCorpuses",
]
