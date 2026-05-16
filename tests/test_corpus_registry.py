"""Tests for the azrael corpus registry — validates structure and content."""
from azrael._corpus_registry import AZRAEL_DEFAULT_CORPUSES


def test_registry_is_list():
    """AZRAEL_DEFAULT_CORPUSES is a non-empty list with more than 5 entries."""
    assert isinstance(AZRAEL_DEFAULT_CORPUSES, list)
    assert len(AZRAEL_DEFAULT_CORPUSES) > 5


def test_registry_structure():
    """Every entry has the required keys with valid source_type values."""
    valid_source_types = {"gutenberg", "url", "git"}
    for entry in AZRAEL_DEFAULT_CORPUSES:
        assert "id" in entry, f"Missing 'id' in: {entry}"
        assert "name" in entry, f"Missing 'name' in: {entry}"
        assert "source_type" in entry, f"Missing 'source_type' in: {entry}"
        assert "source" in entry, f"Missing 'source' in: {entry}"
        assert entry["source_type"] in valid_source_types, (
            f"Invalid source_type '{entry['source_type']}' in: {entry['name']}"
        )


def test_gutenberg_entries_have_numeric_source():
    """All gutenberg entries use a numeric string as their source (book ID)."""
    for entry in AZRAEL_DEFAULT_CORPUSES:
        if entry["source_type"] == "gutenberg":
            assert entry["source"].isdigit(), (
                f"'{entry['name']}' gutenberg source should be a numeric book ID, "
                f"got: {entry['source']!r}"
            )


def test_registry_ids_are_unique():
    """All corpus IDs are unique within the registry."""
    ids = [entry["id"] for entry in AZRAEL_DEFAULT_CORPUSES]
    assert len(ids) == len(set(ids)), "Duplicate corpus IDs found in registry"


def test_registry_names_are_nonempty_strings():
    """All registry entries have non-empty string names."""
    for entry in AZRAEL_DEFAULT_CORPUSES:
        assert isinstance(entry["name"], str)
        assert entry["name"].strip(), f"Empty name in entry: {entry}"


def test_registry_contains_greek_sources():
    """Registry should include at least one Greek mythology source."""
    greek_entries = [
        e for e in AZRAEL_DEFAULT_CORPUSES
        if "greek" in e.get("topics", [])
    ]
    assert len(greek_entries) >= 1, "Expected at least one Greek mythology source"


def test_registry_contains_norse_sources():
    """Registry should include at least one Norse mythology source."""
    norse_entries = [
        e for e in AZRAEL_DEFAULT_CORPUSES
        if "norse" in e.get("topics", [])
    ]
    assert len(norse_entries) >= 1, "Expected at least one Norse mythology source"
