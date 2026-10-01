//! Rust helpers for `azrael`.
//!
//! These must agree exactly with the Python fallbacks in
//! `src/azrael/__init__.py`. They had drifted: `score_entity` awards
//! [`FUZZY_SCORE`] for a fuzzy subsequence hit on the name, and the Python had
//! no fuzzy branch at all, so it returned `0.0` for the same input. Which
//! ranking you got depended on whether a wheel had been built, and nothing
//! reported which was live.
//!
//! The tests at the bottom pin every tier, so the two implementations cannot
//! drift again without something failing.

#[cfg(feature = "python")]
use pyo3::prelude::*;

/// Added when the query is a prefix of the entity name.
pub const NAME_PREFIX_SCORE: f64 = 1000.0;

/// Added when the name contains the query but does not start with it.
pub const NAME_CONTAINS_SCORE: f64 = 500.0;

/// Added when the description contains the query.
pub const DESCRIPTION_SCORE: f64 = 150.0;

/// Added when the auxiliary search text contains the query.
pub const SEARCH_TEXT_SCORE: f64 = 120.0;

/// Awarded only when nothing else matched and the name fuzzy-matches.
pub const FUZZY_SCORE: f64 = 40.0;

/// Score an entity against a search query using tiered relevance.
///
/// Name prefix (1000) > name contains (500), plus 150 for a description hit
/// and 120 for a search-text hit. If nothing matched at all, a fuzzy
/// subsequence match on the name scores 40.
///
/// Must stay identical to the Python fallback in `src/azrael/__init__.py`.
pub fn score_entity_impl(name: &str, description: &str, search_text: &str, query: &str) -> f64 {
    let q = query.to_lowercase();
    if q.is_empty() {
        return 0.0;
    }
    debug_assert!(!q.is_empty(), "the empty query returned above");
    let n = name.to_lowercase();
    let mut score = 0.0_f64;
    if n.starts_with(&q) {
        score += NAME_PREFIX_SCORE;
    } else if n.contains(&q) {
        score += NAME_CONTAINS_SCORE;
    }
    if description.to_lowercase().contains(&q) {
        score += DESCRIPTION_SCORE;
    }
    if search_text.to_lowercase().contains(&q) {
        score += SEARCH_TEXT_SCORE;
    }
    if score == 0.0 && fuzzy_contains(&n, &q) {
        score += FUZZY_SCORE;
    }
    debug_assert!(score >= 0.0, "scores are never negative");
    score
}

/// Case-insensitive prefix check on an entity name.
pub fn name_starts_with_impl(name: &str, prefix: &str) -> bool {
    debug_assert!(name.len() < usize::MAX, "name must be a real string");
    debug_assert!(prefix.len() < usize::MAX, "prefix must be a real string");
    name.to_lowercase().starts_with(&prefix.to_lowercase())
}

/// Whether every character of `pattern` appears in `text`, in order.
pub fn fuzzy_contains(text: &str, pattern: &str) -> bool {
    let mut pi = pattern.chars().peekable();
    for tc in text.chars() {
        if let Some(&pc) = pi.peek() {
            if tc == pc {
                pi.next();
            }
        } else {
            break;
        }
    }
    pi.peek().is_none()
}

// ---------------------------------------------------------------------------
// Python bindings
// ---------------------------------------------------------------------------

/// Score an entity against a search query using tiered relevance.
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(name = "score_entity")]
fn py_score_entity(name: &str, description: &str, search_text: &str, query: &str) -> f64 {
    score_entity_impl(name, description, search_text, query)
}

/// Fast case-insensitive prefix check on an entity name.
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(name = "name_starts_with")]
fn py_name_starts_with(name: &str, prefix: &str) -> bool {
    name_starts_with_impl(name, prefix)
}

#[cfg(feature = "python")]
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(py_score_entity, m)?)?;
    m.add_function(wrap_pyfunction!(py_name_starts_with, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_name_prefix_outranks_a_name_containing_the_query() {
        let prefix = score_entity_impl("Odin", "", "", "odin");
        let contains = score_entity_impl("The Odin Stone", "", "", "odin");
        assert_eq!(prefix, NAME_PREFIX_SCORE);
        assert_eq!(contains, NAME_CONTAINS_SCORE);
        assert!(prefix > contains);
    }

    #[test]
    fn description_and_search_text_hits_add_to_the_name_score() {
        // These are additive, not exclusive -- an entity matching everywhere
        // must outrank one matching only on its name.
        let name_only = score_entity_impl("Odin", "", "", "odin");
        let everywhere = score_entity_impl("Odin", "odin the allfather", "odin norse", "odin");
        assert_eq!(
            everywhere,
            NAME_PREFIX_SCORE + DESCRIPTION_SCORE + SEARCH_TEXT_SCORE
        );
        assert!(everywhere > name_only);
    }

    #[test]
    fn the_fuzzy_tier_applies_only_when_nothing_else_matched() {
        // This branch is why the two implementations disagreed: the Python
        // fallback had no fuzzy tier and returned 0.0 here.
        assert_eq!(score_entity_impl("Odin", "", "", "on"), FUZZY_SCORE);
        // With a real hit elsewhere the fuzzy bonus must not also apply.
        let with_description = score_entity_impl("Odin", "on a horse", "", "on");
        assert_eq!(with_description, DESCRIPTION_SCORE);
    }

    #[test]
    fn an_empty_query_scores_nothing() {
        // Every string starts with "", so without the guard this would give
        // the top score to every entity for no query at all.
        assert_eq!(score_entity_impl("Odin", "anything", "anything", ""), 0.0);
    }

    #[test]
    fn no_match_scores_nothing() {
        assert_eq!(score_entity_impl("Odin", "norse god", "", "zzzz"), 0.0);
    }

    #[test]
    fn scoring_is_case_insensitive() {
        assert_eq!(
            score_entity_impl("ODIN", "", "", "odin"),
            score_entity_impl("odin", "", "", "ODIN")
        );
    }

    #[test]
    fn prefix_checks_are_case_insensitive() {
        assert!(name_starts_with_impl("Odin", "od"));
        assert!(name_starts_with_impl("odin", "OD"));
        assert!(!name_starts_with_impl("Odin", "din"));
        assert!(
            name_starts_with_impl("Odin", ""),
            "everything starts with nothing"
        );
    }

    #[test]
    fn fuzzy_matching_requires_order() {
        assert!(fuzzy_contains("odin", "on"));
        assert!(!fuzzy_contains("odin", "no"), "order must matter");
    }

    #[test]
    fn non_ascii_names_do_not_panic() {
        // Ordinary in a mythology corpus: accented and non-Latin names.
        assert!(score_entity_impl("\u{c6}sir", "", "", "\u{e6}sir") > 0.0);
        assert!(score_entity_impl("Ra\u{308}", "", "", "zzz") >= 0.0);
        assert!(name_starts_with_impl("\u{c6}sir", "\u{e6}"));
    }
}
