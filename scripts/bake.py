#!/usr/bin/env python3
"""Bake mythology data into azrael.db (SQLite) via the Firestore REST API.

Usage:
    python scripts/bake.py                          # pull from Firebase
    python scripts/bake.py --source /path/to/dir   # use local JSON export
    python scripts/bake.py --api-key KEY            # override API key
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Install bake deps: pip install 'azrael[bake]'")

from eyecore import compress_db, GRAPH_SCHEMA

ROOT = Path(__file__).parent.parent
DATA_OUT = ROOT / "src" / "azrael" / "_data" / "azrael.db"

PROJECT_ID = "eyesofazrael"
# Public client API key — safe to embed, identical to what ships in the website JS
DEFAULT_API_KEY = "AIzaSyB7bFdte6f81-bNMsdITgnnnWq7aBNMXRw"
_BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

COLLECTIONS: dict[str, str] = {
    "deities": "deity",
    "creatures": "creature",
    "heroes": "hero",
    "places": "place",
    "items": "item",
    "concepts": "concept",
    "symbols": "symbol",
    "archetypes": "archetype",
    "cosmology": "cosmology",
    "magic": "magic",
    "herbs": "herb",
    "rituals": "ritual",
    "texts": "text",
    "mythologies": "mythology",
    "beings": "being",
    "figures": "figure",
    "teachings": "teaching",
    "events": "event",
    "path": "path",
}

TYPE_FIXES: dict[str, str] = {"deitie": "deity"}

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    mythology TEXT,
    domains_text TEXT,
    search_text TEXT,
    data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_name ON entities(name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_mythology ON entities(mythology COLLATE NOCASE);
CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
    id UNINDEXED,
    search_text,
    tokenize='unicode61 remove_diacritics 1'
);
CREATE TABLE IF NOT EXISTS entity_topics (
    entity_id TEXT NOT NULL REFERENCES entities(id),
    topic_id  TEXT NOT NULL REFERENCES topics(id),
    PRIMARY KEY (entity_id, topic_id)
);
"""


# ── Firestore REST helpers ────────────────────────────────────────────────────

def _parse_value(val: dict):
    if "stringValue" in val:
        return val["stringValue"]
    if "integerValue" in val:
        return int(val["integerValue"])
    if "doubleValue" in val:
        return float(val["doubleValue"])
    if "booleanValue" in val:
        return val["booleanValue"]
    if "nullValue" in val:
        return None
    if "timestampValue" in val:
        return val["timestampValue"]
    if "arrayValue" in val:
        return [_parse_value(v) for v in val["arrayValue"].get("values", [])]
    if "mapValue" in val:
        return {k: _parse_value(v) for k, v in val["mapValue"].get("fields", {}).items()}
    return None


def _doc_to_dict(doc: dict) -> dict:
    result = {k: _parse_value(v) for k, v in doc.get("fields", {}).items()}
    result["id"] = doc["name"].rsplit("/", 1)[-1]
    return result


def _fetch_collection(session: requests.Session, collection: str, api_key: str) -> list[dict]:
    import time
    url = f"{_BASE}/{collection}"
    docs: list[dict] = []
    page_token: str | None = None
    while True:
        params: dict = {"key": api_key, "pageSize": 300}
        if page_token:
            params["pageToken"] = page_token
        for attempt in range(5):
            resp = session.get(url, params=params, timeout=30)
            if resp.status_code == 429:
                wait = 2 ** attempt
                print(f"(rate limited, waiting {wait}s)", end=" ", flush=True)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            break
        else:
            resp.raise_for_status()
        data = resp.json()
        for doc in data.get("documents", []):
            docs.append(_doc_to_dict(doc))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return docs


# ── DB helpers ────────────────────────────────────────────────────────────────

def _coerce_type(raw: str | None, fallback: str) -> str:
    if not raw:
        return fallback
    return TYPE_FIXES.get(raw, raw)


def _str_list(val) -> str:
    if not val:
        return ""
    if isinstance(val, list):
        return " ".join(str(v) for v in val if v)
    return str(val)


def _first_str(*candidates) -> str | None:
    for c in candidates:
        if isinstance(c, str) and c:
            return c
    return None


def _domains_text(e: dict) -> str:
    parts = [
        _str_list(e.get("domains")),
        _str_list(e.get("abilities")),
        _str_list(e.get("powers")),
        _str_list(e.get("attributes")),
        _str_list(e.get("significance")),
        _str_list(e.get("tags")),
    ]
    return " ".join(p for p in parts if p).lower()


def _safe_str(val) -> str:
    if isinstance(val, str):
        return val
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, list):
        return _str_list(val)
    return ""


def _search_text(e: dict) -> str:
    desc = (e.get("description") or e.get("shortDescription") or e.get("longDescription") or "")
    alt_names = e.get("alternativeNames") or []
    alt = " ".join(
        a.get("name", "") for a in alt_names if isinstance(a, dict)
    )
    parts = [
        _safe_str(e.get("name", "")),
        _safe_str(e.get("mythology") or e.get("primaryMythology") or ""),
        _safe_str(desc),
        _str_list(e.get("domains")),
        _str_list(e.get("abilities")),
        _str_list(e.get("titles")),
        _str_list(e.get("attributes")),
        _str_list(e.get("searchTerms")),
        _str_list(e.get("tags")),
        _safe_str(e.get("subtitle", "")),
        alt,
    ]
    return " ".join(p for p in parts if p)


def _init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    db = sqlite3.connect(str(db_path))
    for stmt in GRAPH_SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            db.execute(s)
    for stmt in CREATE_SQL.strip().split(";"):
        s = stmt.strip()
        if s:
            db.execute(s)
    db.commit()
    return db


def _insert_batch(db: sqlite3.Connection, rows: list, fts_rows: list) -> None:
    db.executemany(
        "INSERT OR REPLACE INTO entities"
        "(id, name, type, mythology, domains_text, search_text, data) "
        "VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    db.executemany(
        "INSERT INTO entities_fts(id, search_text) VALUES (?,?)",
        fts_rows,
    )
    db.commit()


def _build_topic_graph(db: sqlite3.Connection, all_rows: list) -> None:
    from eyecore import TopicGraph
    graph = TopicGraph(db)

    mythologies: set[str] = set()
    types: set[str] = set()
    myth_type_pairs: set[tuple[str, str]] = set()
    entity_domain_words: list[tuple[str, set[str]]] = []

    for eid, name, etype, myth, domains_text, srch, data_json in all_rows:
        if myth:
            mythologies.add(myth)
        if etype:
            types.add(etype)
        if myth and etype:
            myth_type_pairs.add((myth, etype))
        words = set(w for w in (domains_text or "").split() if len(w) > 2)
        if words:
            entity_domain_words.append((eid, words))

    for myth in mythologies:
        graph.upsert_topic(f"myth:{myth}", myth, type="mythology")

    for etype in types:
        graph.upsert_topic(f"type:{etype}", etype, type="entity_type")

    for myth, etype in myth_type_pairs:
        graph.upsert_link(f"type:{etype}", f"myth:{myth}", relation="belongs_to")

    domain_topic_ids: dict[str, str] = {}
    for eid, words in entity_domain_words:
        for word in words:
            topic_id = f"domain:{word}"
            if topic_id not in domain_topic_ids:
                graph.upsert_topic(topic_id, word, type="domain")
                domain_topic_ids[topic_id] = word

    entity_topic_rows: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for eid, name, etype, myth, domains_text, srch, data_json in all_rows:
        if myth:
            pair = (eid, f"myth:{myth}")
            if pair not in seen:
                entity_topic_rows.append(pair)
                seen.add(pair)
        if etype:
            pair = (eid, f"type:{etype}")
            if pair not in seen:
                entity_topic_rows.append(pair)
                seen.add(pair)
        words = set(w for w in (domains_text or "").split() if len(w) > 2)
        for word in words:
            pair = (eid, f"domain:{word}")
            if pair not in seen:
                entity_topic_rows.append(pair)
                seen.add(pair)

    if entity_topic_rows:
        db.executemany(
            "INSERT OR IGNORE INTO entity_topics(entity_id, topic_id) VALUES (?,?)",
            entity_topic_rows,
        )

    graph.commit()
    db.commit()
    print(f"  Topics: {len(mythologies)} mythologies, {len(types)} types, {len(domain_topic_ids)} domains")


# ── Bake functions ────────────────────────────────────────────────────────────

def bake_from_firebase(db_path: Path, api_key: str) -> None:
    session = requests.Session()
    db = _init_db(db_path)
    total = 0
    all_rows: list = []
    for col_name, entity_type in COLLECTIONS.items():
        print(f"  {col_name}...", end=" ", flush=True)
        try:
            entities = _fetch_collection(session, col_name, api_key)
        except requests.HTTPError as exc:
            print(f"SKIP ({exc.response.status_code})")
            continue
        rows, fts_rows = [], []
        for e in entities:
            eid = _first_str(e.get("id")) or ""
            if not eid:
                continue
            etype = _coerce_type(_first_str(e.get("type")), entity_type)
            e["type"] = etype
            myth = _first_str(e.get("mythology"), e.get("primaryMythology"), e.get("category"), e.get("era"))
            name = _first_str(e.get("name")) or eid
            srch = _search_text(e)
            row = (eid, name, etype, myth, _domains_text(e), srch, json.dumps(e, ensure_ascii=False))
            rows.append(row)
            fts_rows.append((eid, srch))
            all_rows.append(row)
        _insert_batch(db, rows, fts_rows)
        print(len(rows))
        total += len(rows)
    size = db_path.stat().st_size / 1_048_576
    print(f"\nDone: {total} entities -> {db_path} ({size:.1f} MB)")
    print("Building topic graph...")
    _build_topic_graph(db, all_rows)
    db.close()
    compress_db(db_path)


def bake_from_local(source_dir: Path, db_path: Path) -> None:
    if not source_dir.exists():
        sys.exit(f"Source not found: {source_dir}")
    db = _init_db(db_path)
    total = 0
    all_rows: list = []
    for col_name, entity_type in COLLECTIONS.items():
        col_dir = source_dir / col_name
        if not col_dir.exists():
            print(f"  SKIP {col_name} (not found)")
            continue
        files = [f for f in col_dir.glob("*.json") if not f.name.startswith("_")]
        print(f"  {col_name}: {len(files)} -> {entity_type}")
        rows, fts_rows = [], []
        for jf in files:
            try:
                e = json.loads(jf.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(e, dict):
                continue
            eid = e.get("id") or jf.stem
            e["id"] = eid
            etype = _coerce_type(e.get("type"), entity_type)
            e["type"] = etype
            myth = _first_str(e.get("mythology"), e.get("primaryMythology"))
            name = _first_str(e.get("name")) or eid
            srch = _search_text(e)
            row = (eid, name, etype, myth, _domains_text(e), srch, json.dumps(e, ensure_ascii=False))
            rows.append(row)
            fts_rows.append((eid, srch))
            all_rows.append(row)
        _insert_batch(db, rows, fts_rows)
        total += len(rows)
    size = db_path.stat().st_size / 1_048_576
    print(f"\nDone: {total} entities -> {db_path} ({size:.1f} MB)")
    print("Building topic graph...")
    _build_topic_graph(db, all_rows)
    db.close()
    compress_db(db_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bake mythology data into azrael.db")
    parser.add_argument("--source", metavar="DIR", help="Local JSON export directory (skips Firebase)")
    parser.add_argument("--api-key", default=os.getenv("FIREBASE_API_KEY", DEFAULT_API_KEY),
                        metavar="KEY", help="Firebase public API key")
    parser.add_argument("--out", default=str(DATA_OUT), metavar="PATH",
                        help=f"Output path (default: {DATA_OUT})")
    args = parser.parse_args()
    out = Path(args.out)
    if args.source:
        bake_from_local(Path(args.source), out)
    else:
        bake_from_firebase(out, args.api_key)


if __name__ == "__main__":
    main()
