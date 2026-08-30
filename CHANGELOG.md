# Changelog

## [1.1.0] — 2026-08-30

### Added
- `azrael.Refresh()` — pulls entities changed in Firestore since the bake
  (or last refresh) and merges them locally. The baked snapshot is the
  *last-pushed state*; Firestore serves only the diff layer.
- Lazy data download: the baked `azrael.db.gz` is no longer inside the wheel
  or the git tree — it is a GitHub Release asset fetched automatically on
  first query (via `eyecore>=1.1.0`). Wheels drop from ~52 MB to kilobytes.
- `scripts/bake.py` stamps `meta.generated_at` so delta sync knows its epoch.

### Changed
- Requires `eyecore>=1.1.0`.
- Re-baked from a fresh Firestore export (post magic/herbs/rituals split).

## [1.0.0] — 2026-05-17

Initial release: typed getters, FTS5 search, fuzzy match, topic graph,
14 Project Gutenberg corpuses, baked 50 MB database shipped in-wheel.
