"""The `heroe` typo in the baked snapshot.

The published data-v1.1.0 asset stores 142 heroes under the misspelt type
`heroe` next to 1,044 correct `hero` rows, so every query filtering
`type = 'hero'` silently returned a short answer. Release assets are
immutable, so the fix is two-sided: the bake and the delta path normalise the
spelling away from now on, and the query layer treats `heroe` as `hero` so the
142 rows in the *already shipped* snapshot are reachable without a re-bake.
"""
import azrael
from azrael._query import (
    AllHeroes,
    ByType,
    Count,
    GetAll,
    GetRandom,
    _TYPE_ALIASES,
    _TYPE_FIXES,
    _expand_types,
)


# ── the normalisation map ─────────────────────────────────────────────────────

def test_bake_and_delta_share_one_type_fix_map():
    """scripts/bake.py and Refresh() must fold the same typos, or a re-bake and
    a sync would disagree about what a hero is called."""
    from pathlib import Path

    # Read rather than import: scripts/bake.py requires `requests` at import time.
    bake_path = Path(__file__).resolve().parents[1] / "scripts" / "bake.py"
    src = bake_path.read_text(encoding="utf-8")
    assert '"heroe": "hero"' in src
    assert '"deitie": "deity"' in src
    assert _TYPE_FIXES["heroe"] == "hero"
    assert _TYPE_FIXES["deitie"] == "deity"


def test_aliases_derive_from_the_fix_map():
    assert _TYPE_ALIASES["hero"] == ("hero", "heroe")
    assert _TYPE_ALIASES["deity"] == ("deity", "deitie")
    assert _expand_types("hero") == ("hero", "heroe")
    assert _expand_types("hero", "deity") == ("hero", "heroe", "deity", "deitie")
    assert _expand_types("creature") == ("creature",)


# ── the shipped snapshot stays queryable ──────────────────────────────────────

def test_by_type_hero_includes_misspelt_rows(patch_typo_base):
    names = {r["name"] for r in ByType("hero")}
    assert names == {"Achilles", "Abe no Seimei"}


def test_all_heroes_includes_misspelt_rows(patch_typo_base):
    assert {r["name"] for r in AllHeroes()} == {"Achilles", "Abe no Seimei"}


def test_count_hero_includes_misspelt_rows(patch_typo_base):
    assert Count("hero") == 2


def test_get_all_hero_includes_misspelt_rows(patch_typo_base):
    assert len(GetAll("hero")) == 2


def test_by_type_hero_still_honours_the_mythology_filter(patch_typo_base):
    assert [r["name"] for r in ByType("hero", "japanese")] == ["Abe no Seimei"]
    assert [r["name"] for r in ByType("hero", "greek")] == ["Achilles"]


def test_get_random_hero_can_return_a_misspelt_row(patch_typo_base):
    assert GetRandom("hero", "japanese")["name"] == "Abe no Seimei"


def test_gethero_finds_a_misspelt_row(patch_typo_base):
    result = azrael.GetHero("Abe no Seimei")
    assert result is not None
    assert result["name"] == "Abe no Seimei"


def test_other_types_are_not_widened(patch_typo_base):
    """Only declared aliases expand — a misspelt hero is not a creature."""
    assert Count("creature") == 1
    assert azrael.GetCreature("Abe no Seimei") is None
