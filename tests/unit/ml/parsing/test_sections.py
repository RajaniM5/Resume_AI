from ml.parsing.sections import JD_SECTION_HEADINGS, split_into_blocks, split_sections

RESUME_TEXT = """Jane Doe
jane@example.com

SUMMARY
Senior engineer.

SKILLS
Python, AWS

EXPERIENCE
Engineer, Acme
2020 - Present
- Did things

EDUCATION
B.S. Computer Science, State University, 2018
"""


def test_splits_header_and_named_sections() -> None:
    body = split_sections(RESUME_TEXT)
    assert "Jane Doe" in body["header"]
    assert body["summary"] == "Senior engineer."
    assert body["skills"] == "Python, AWS"
    assert "Engineer, Acme" in body["experience"]
    assert "State University" in body["education"]


def test_heading_variants_normalize_to_canonical_section() -> None:
    text = "WORK EXPERIENCE\nDid stuff\n\nTECHNICAL SKILLS\nPython\n"
    body = split_sections(text)
    assert body["experience"] == "Did stuff"
    assert body["skills"] == "Python"


def test_sentence_line_is_not_mistaken_for_a_heading() -> None:
    text = "Experience the difference we make.\nMore text.\n"
    body = split_sections(text)
    assert "experience" not in body
    assert body["header"] == text.strip()


def test_jd_section_headings() -> None:
    text = "Requirements\n- 5 years Python\n\nNice to have\n- AWS\n"
    body = split_sections(text, section_headings=JD_SECTION_HEADINGS)
    assert body["requirements"] == "- 5 years Python"
    assert body["preferred"] == "- AWS"


def test_split_into_blocks_separates_on_blank_lines() -> None:
    text = "Engineer, Acme\n2020 - Present\n- did stuff\n\nDeveloper, Beta\n2018 - 2020\n"
    blocks = split_into_blocks(text)
    assert len(blocks) == 2
    assert blocks[0][0] == "Engineer, Acme"
    assert blocks[1][0] == "Developer, Beta"
