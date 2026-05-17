use pyo3::prelude::*;

/// Score an entity against a search query using tiered relevance.
/// Tiers: name prefix (1000) > name contains (500) > description contains (150) > fuzzy name (40).
#[pyfunction]
fn score_entity(name: &str, description: &str, search_text: &str, query: &str) -> f64 {
    let q = query.to_lowercase();
    let n = name.to_lowercase();
    if q.is_empty() { return 0.0; }
    let mut score = 0.0_f64;
    if n.starts_with(&q)   { score += 1000.0; }
    else if n.contains(&q) { score += 500.0; }
    let d = description.to_lowercase();
    if d.contains(&q)      { score += 150.0; }
    let s = search_text.to_lowercase();
    if s.contains(&q)      { score += 120.0; }
    if score == 0.0 && fuzzy_contains(&n, &q) { score += 40.0; }
    score
}

/// Fast case-insensitive prefix check on entity name.
#[pyfunction]
fn name_starts_with(name: &str, prefix: &str) -> bool {
    name.to_lowercase().starts_with(&prefix.to_lowercase())
}

fn fuzzy_contains(text: &str, pattern: &str) -> bool {
    let mut pi = pattern.chars().peekable();
    for tc in text.chars() {
        if let Some(&pc) = pi.peek() { if tc == pc { pi.next(); } }
        else { break; }
    }
    pi.peek().is_none()
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(score_entity, m)?)?;
    m.add_function(wrap_pyfunction!(name_starts_with, m)?)?;
    Ok(())
}
