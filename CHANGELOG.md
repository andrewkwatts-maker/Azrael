# Changelog

## [Unreleased]

### Fixed
- **CI tested the published package, not this repository.** The install step
  was `pip install --find-links dist azrael`, which only *adds* `dist/` to the
  candidate set; pip stayed free to prefer the identically versioned wheel on
  PyPI, and did. Every change in this repository since 1.1.0 went unverified —
  the suite was exercising released code. The built wheel is now installed by
  path.
- **142 heroes were unreachable.** The bake normalised `deitie` → `deity` but
  not `heroe` → `hero`, so the snapshot holds 142 rows typed `heroe` beside
  1,044 typed `hero`. `ByType("hero")`, `AllHeroes()`, `Count("hero")`,
  `GetAll("hero")`, `GetRandom("hero")` and `GetHero()` all filtered on the
  canonical spelling and silently returned a short answer. `heroe` is now
  fixed at bake time and, since the published asset cannot be edited, treated
  as an alias of `hero` by the query layer — the 142 are findable against the
  snapshot that is already installed. **The stored data is still wrong: a
  re-bake and a new release asset are needed to clean it.**
- `Refresh()` now passes the same fix map to the delta path, so a Firestore
  document still typed `heroe` is normalised on arrival instead of
  reintroducing the typo one sync at a time.

### Added
- The expected SHA-256 of the release asset is declared next to its URL and
  verified during download. Previously the only integrity check on a 58 MB
  fetch was the gzip magic number, which a truncated download passes.

### Changed
- Version bumped to 1.2.0. The working tree had diverged from the published
  1.1.0 while keeping its version number, so `pip install azrael==1.1.0` and a
  build from this checkout produced different code under one version.
- Requires `eyecore>=1.2.0` for `type_aliases` / `type_fixes`.

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
