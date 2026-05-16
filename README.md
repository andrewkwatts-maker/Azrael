# azrael

Mythology encyclopedia for Python — gods, creatures, heroes, places, items, sacred texts, and more from world mythologies.

## Features

- Thousands of entities spanning Greek, Norse, Egyptian, Celtic, Hindu, Mesopotamian, Japanese, and more
- Full-text search with FTS5 fallback to LIKE
- Fuzzy name matching and random sampling
- Topic graph for related entity discovery
- On-demand corpus checkout from Project Gutenberg (downloaded once, cached locally)
- Optional LLM integration for intelligent queries

## Installation

```bash
pip install azrael
```

## Quick start

```python
import azrael

# Look up by type
god      = azrael.GetGod("Odin")
creature = azrael.GetCreature("Hydra")
hero     = azrael.GetHero("Achilles")
place    = azrael.GetPlace("Valhalla")
item     = azrael.GetItem("Mjolnir")

# Generic lookup and full-text search
entry    = azrael.Get("Fenrir")
results  = azrael.Search("trickster")

# Browse by mythology or type
norse    = azrael.ByMythology("norse")
deities  = azrael.ByType("deity", "greek")
all_gods = azrael.AllGods("egyptian")

# Random, fuzzy, and statistics
random_  = azrael.GetRandom("creature")
matches  = azrael.GetFuzzy("thor")
popular  = azrael.GetMost("mythology")
total    = azrael.Count()

# Topic graph
related  = azrael.GetRelated("Zeus")
topics   = azrael.GetTopics("greek")
tree     = azrael.GetTopicTree("olympian")

# Corpus — downloads from Project Gutenberg on first use
azrael.FetchCorpus("gutenberg-iliad")
hits     = azrael.SearchCorpus("wooden horse")
sources  = azrael.ListCorpuses()
```

## Available corpuses

| Corpus ID | Text |
|---|---|
| `gutenberg-iliad` | Homer's Iliad |
| `gutenberg-odyssey` | Homer's Odyssey |
| `gutenberg-theogony` | Hesiod's Theogony |
| `gutenberg-metamorphoses` | Ovid's Metamorphoses |
| `gutenberg-aeneid` | Virgil's Aeneid |
| `gutenberg-homeric-hymns` | Homeric Hymns |
| `gutenberg-prose-edda` | Snorri Sturluson's Prose Edda |
| `gutenberg-volsunga-saga` | Volsunga Saga |
| `gutenberg-mabinogion` | The Mabinogion (Welsh myths) |
| `gutenberg-celtic-myth` | Celtic Myth and Legend |
| `gutenberg-egyptian-myth` | Egyptian Myth and Legend |
| `gutenberg-1001-nights` | One Thousand and One Nights |
| `gutenberg-ramayana` | The Ramayana |
| `gutenberg-mahabharata` | The Mahabharata |

## Part of the Eyes of Azrael suite

| Package | Description |
|---|---|
| [`eyecore`](https://github.com/EyesOfAzrael/eyecore) | Shared foundation (DB, graph, corpus, LLM) |
| [`clio`](https://github.com/EyesOfAzrael/clio) | Historical figures and events |
| [`apocrypha`](https://github.com/EyesOfAzrael/apocrypha) | Conspiracy theories and hidden histories |
| [`augur`](https://github.com/EyesOfAzrael/augur) | News aggregation and topic analysis |

## License

MIT — see [LICENSE](LICENSE)
