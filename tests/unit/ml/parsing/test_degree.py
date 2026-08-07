from ml.parsing.degree import degree_rank, find_required_degree_rank, highest_degree_rank


def test_degree_rank_orders_by_seniority() -> None:
    assert degree_rank("Associate's") < degree_rank("Bachelor's")
    assert degree_rank("Bachelor's") < degree_rank("Master's")
    assert degree_rank("Master's") < degree_rank("PhD")


def test_degree_rank_handles_abbreviations() -> None:
    assert degree_rank("B.S.") == degree_rank("Bachelor's")
    assert degree_rank("M.S.") == degree_rank("Master's")
    assert degree_rank("MBA") == degree_rank("Master's")


def test_degree_rank_unrecognized_is_zero() -> None:
    assert degree_rank("Certificate") == 0


def test_highest_degree_rank_picks_max() -> None:
    assert highest_degree_rank(["Bachelor's", "Master's"]) == degree_rank("Master's")
    assert highest_degree_rank([]) == 0


def test_find_required_degree_rank_in_jd_text() -> None:
    text = "We require a Bachelor's degree in Computer Science."
    assert find_required_degree_rank(text) == degree_rank("Bachelor's")


def test_find_required_degree_rank_absent_returns_zero() -> None:
    assert find_required_degree_rank("No formal education requirement.") == 0
