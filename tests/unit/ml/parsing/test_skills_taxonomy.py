from ml.parsing.skills_taxonomy import extract_skills


def test_extracts_canonical_skills_case_insensitively() -> None:
    text = "Experienced with PYTHON, react.js, and Kubernetes deployments."
    assert extract_skills(text) == ["python", "react", "kubernetes"]


def test_dedupes_repeated_mentions_keeping_first_seen_order() -> None:
    text = "Python developer. Also used python for scripting and Python for ML."
    assert extract_skills(text) == ["python"]


def test_no_false_positive_on_substring_inside_another_word() -> None:
    # "go" shouldn't match inside "good" or "going"
    text = "A good developer going the extra mile."
    assert "go" not in extract_skills(text)


def test_no_skills_found_returns_empty_list() -> None:
    assert extract_skills("Nothing relevant in this sentence at all.") == []


def test_longer_surface_form_wins_over_shorter_overlapping_one() -> None:
    text = "Built UIs with React.js and vanilla JS."
    skills = extract_skills(text)
    assert "react" in skills
    assert "javascript" in skills
