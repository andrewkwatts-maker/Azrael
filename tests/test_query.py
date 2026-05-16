"""Unit tests for azrael._query — all queries run against an in-memory SQLite DB."""
import pytest
import azrael
from azrael._query import (
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
)


# ---------------------------------------------------------------------------
# Get — exact / fuzzy name lookup
# ---------------------------------------------------------------------------

def test_get_exact(patch_base):
    """Get with exact name (correct case) returns the matching entity."""
    result = Get("Zeus")
    assert result is not None
    assert result["name"] == "Zeus"


def test_get_fuzzy(patch_base):
    """Get with lowercase name still finds the entity (case-insensitive)."""
    result = Get("zeus")
    assert result is not None
    assert result["name"] == "Zeus"


def test_get_partial(patch_base):
    """Get with a substring matches via the LIKE fallback."""
    result = Get("eus")
    assert result is not None
    assert result["name"] == "Zeus"


def test_get_none(patch_base):
    """Get with an unknown name returns None."""
    result = Get("Nonexistent9999")
    assert result is None


# ---------------------------------------------------------------------------
# Search — FTS / LIKE fallback
# ---------------------------------------------------------------------------

def test_search(patch_base):
    """Search returns at least one result for a domain keyword present in search_text.

    The in-memory FTS table only has entity names as search_text, so we search
    for a known name fragment and rely on the LIKE fallback when FTS raises
    OperationalError (the 'name' column is not in the entities_fts schema).
    """
    results = Search("Zeus")
    assert isinstance(results, list)
    assert len(results) >= 1
    names = [r["name"] for r in results]
    assert "Zeus" in names


def test_search_returns_list_on_no_match(patch_base):
    """Search with a non-matching term returns an empty list, never None."""
    results = Search("xyzzy_no_match_99")
    assert isinstance(results, list)


# ---------------------------------------------------------------------------
# ByMythology
# ---------------------------------------------------------------------------

def test_by_mythology(patch_base):
    """ByMythology('greek') returns at least 3 results, all with mythology=='greek'."""
    results = ByMythology("greek")
    assert len(results) >= 3
    for r in results:
        assert r["mythology"] == "greek"


def test_by_mythology_case_insensitive(patch_base):
    """ByMythology is case-insensitive."""
    results = ByMythology("GREEK")
    assert len(results) >= 3


def test_by_mythology_no_results(patch_base):
    """ByMythology with unknown value returns empty list."""
    results = ByMythology("atlantean")
    assert results == []


# ---------------------------------------------------------------------------
# ByType
# ---------------------------------------------------------------------------

def test_by_type(patch_base):
    """ByType('deity') returns Zeus and Odin."""
    results = ByType("deity")
    assert len(results) == 2
    names = {r["name"] for r in results}
    assert "Zeus" in names
    assert "Odin" in names


def test_by_type_filtered(patch_base):
    """ByType('deity', 'greek') returns only Zeus."""
    results = ByType("deity", "greek")
    assert len(results) == 1
    assert results[0]["name"] == "Zeus"


def test_by_type_no_results(patch_base):
    """ByType with an absent type returns empty list."""
    results = ByType("spirit")
    assert results == []


# ---------------------------------------------------------------------------
# Convenience type helpers
# ---------------------------------------------------------------------------

def test_allgods(patch_base):
    """AllGods() returns at least 2 entities."""
    results = AllGods()
    assert len(results) >= 2
    for r in results:
        assert r["type"] == "deity"


def test_allgods_filtered(patch_base):
    """AllGods('greek') returns only greek deities."""
    results = AllGods("greek")
    assert len(results) >= 1
    for r in results:
        assert r["mythology"] == "greek"
        assert r["type"] == "deity"


def test_allcreatures(patch_base):
    """AllCreatures() returns at least 1 result, all with type=='creature'."""
    results = AllCreatures()
    assert len(results) >= 1
    for r in results:
        assert r["type"] == "creature"


def test_allheroes(patch_base):
    """AllHeroes() returns at least 1 result."""
    results = AllHeroes()
    assert len(results) >= 1
    for r in results:
        assert r["type"] == "hero"


# ---------------------------------------------------------------------------
# Count
# ---------------------------------------------------------------------------

def test_count_all(patch_base):
    """Count() without filter returns total entity count (5 in test DB)."""
    assert Count() == 5


def test_count_typed(patch_base):
    """Count('deity') returns 2 (Zeus and Odin)."""
    assert Count("deity") == 2


def test_count_zero_for_missing_type(patch_base):
    """Count with an absent type returns 0."""
    assert Count("spirit") == 0


# ---------------------------------------------------------------------------
# GetRandom
# ---------------------------------------------------------------------------

def test_getrandom(patch_base):
    """GetRandom() returns a dict with a 'name' key."""
    result = GetRandom()
    assert result is not None
    assert isinstance(result, dict)
    assert "name" in result


def test_getrandom_typed(patch_base):
    """GetRandom('deity') always returns an entity whose type is 'deity'."""
    result = GetRandom("deity")
    assert result is not None
    assert result["type"] == "deity"


def test_getrandom_mythology(patch_base):
    """GetRandom(mythology='greek') always returns a greek entity."""
    result = GetRandom(mythology="greek")
    assert result is not None
    assert result["mythology"] == "greek"


def test_getrandom_typed_and_mythology(patch_base):
    """GetRandom with both type and mythology filters correctly."""
    result = GetRandom("deity", "greek")
    assert result is not None
    assert result["type"] == "deity"
    assert result["mythology"] == "greek"


def test_getrandom_no_match_returns_none(patch_base):
    """GetRandom for a type with no entities returns None."""
    result = GetRandom("spirit")
    assert result is None


# ---------------------------------------------------------------------------
# GetFuzzy
# ---------------------------------------------------------------------------

def test_getfuzzy(patch_base):
    """GetFuzzy('Ach') finds Achilles via the LIKE fallback."""
    results = GetFuzzy("Ach")
    assert isinstance(results, list)
    assert len(results) >= 1
    names = [r["name"] for r in results]
    assert "Achilles" in names


def test_getfuzzy_case_insensitive(patch_base):
    """GetFuzzy is case-insensitive."""
    results = GetFuzzy("ach")
    names = [r["name"] for r in results]
    assert "Achilles" in names


def test_getfuzzy_no_match(patch_base):
    """GetFuzzy with no match returns empty list."""
    results = GetFuzzy("xyzzy_nope_9999")
    assert results == []


# ---------------------------------------------------------------------------
# GetMost
# ---------------------------------------------------------------------------

def test_getmost_mythology(patch_base):
    """GetMost('mythology') returns a list that includes 'greek'."""
    results = GetMost("mythology")
    assert isinstance(results, list)
    assert len(results) >= 1
    keys = {r["mythology"] for r in results}
    assert "greek" in keys


def test_getmost_type(patch_base):
    """GetMost('type') returns a list that includes 'deity'."""
    results = GetMost("type")
    assert isinstance(results, list)
    assert len(results) >= 1
    keys = {r["type"] for r in results}
    assert "deity" in keys


def test_getmost_count_field(patch_base):
    """GetMost results each have a 'count' key with an integer value."""
    results = GetMost("mythology")
    for r in results:
        assert "count" in r
        assert isinstance(r["count"], int)
        assert r["count"] >= 1


def test_getmost_invalid_field(patch_base):
    """GetMost with an unsupported field raises ValueError."""
    with pytest.raises(ValueError):
        GetMost("name")


# ---------------------------------------------------------------------------
# GetAll
# ---------------------------------------------------------------------------

def test_getall(patch_base):
    """GetAll() without filters returns all 5 entities."""
    results = GetAll()
    assert isinstance(results, list)
    assert len(results) == 5


def test_getall_filtered_type(patch_base):
    """GetAll('deity') returns the 2 deity entities."""
    results = GetAll("deity")
    assert len(results) == 2
    for r in results:
        assert r["type"] == "deity"


def test_getall_filtered_mythology(patch_base):
    """GetAll(mythology='norse') returns only Odin."""
    results = GetAll(mythology="norse")
    assert len(results) == 1
    assert results[0]["name"] == "Odin"


def test_getall_filtered_type_and_mythology(patch_base):
    """GetAll('deity', 'greek') returns only Zeus."""
    results = GetAll("deity", "greek")
    assert len(results) == 1
    assert results[0]["name"] == "Zeus"


def test_getall_no_match(patch_base):
    """GetAll with non-existent type returns empty list."""
    results = GetAll("spirit")
    assert results == []


# ---------------------------------------------------------------------------
# Typed helpers defined in azrael.__init__
# ---------------------------------------------------------------------------

def test_typed_helper_getgod(patch_base):
    """azrael.GetGod('Zeus') returns the Zeus entity."""
    result = azrael.GetGod("Zeus")
    assert result is not None
    assert result["name"] == "Zeus"
    assert result["type"] == "deity"


def test_typed_helper_getcreature(patch_base):
    """azrael.GetCreature('Hydra') returns the Hydra entity."""
    result = azrael.GetCreature("Hydra")
    assert result is not None
    assert result["name"] == "Hydra"
    assert result["type"] == "creature"


def test_typed_helper_gethero(patch_base):
    """azrael.GetHero('Achilles') returns the Achilles entity."""
    result = azrael.GetHero("Achilles")
    assert result is not None
    assert result["name"] == "Achilles"
    assert result["type"] == "hero"


def test_typed_helper_getplace(patch_base):
    """azrael.GetPlace('Olympus') finds Mount Olympus via LIKE."""
    result = azrael.GetPlace("Olympus")
    assert result is not None
    assert result["type"] == "place"


def test_typed_helper_wrong_type_returns_none(patch_base):
    """GetGod with a creature name returns None (type mismatch)."""
    result = azrael.GetGod("Hydra")
    assert result is None


def test_typed_helper_domain_fallback(patch_base):
    """_typed falls back to domains_text LIKE when name doesn't match."""
    # "lightning" is in Zeus's domains; lookup as a god should find Zeus
    result = azrael.GetGod("lightning")
    assert result is not None
    assert result["name"] == "Zeus"
