"""Tests for :mod:`glints_scraper.parsers`."""
from __future__ import annotations

from typing import cast

from parsel import Selector

from glints_scraper.parsers import (
    JOB_CARD_SELECTOR,
    OVERVIEW_LABELS,
    clean_text,
    join_texts,
    overview_field,
    parse_job_card,
    parse_job_detail,
)

# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------


def test_clean_text_none() -> None:
    """``clean_text`` returns ``""`` for ``None``."""
    assert clean_text(None) == ""


def test_clean_text_whitespace() -> None:
    """``clean_text`` strips surrounding whitespace."""
    assert clean_text("  hello  ") == "hello"


def test_clean_text_newlines() -> None:
    """``clean_text`` preserves internal newlines."""
    assert clean_text("line1\nline2\n") == "line1\nline2"


# ---------------------------------------------------------------------------
# join_texts
# ---------------------------------------------------------------------------


def test_join_texts_empty() -> None:
    """``join_texts`` returns ``""`` for an empty list."""
    assert join_texts([]) == ""


def test_join_texts_filters_whitespace() -> None:
    """``join_texts`` strips each fragment and drops empty ones."""
    fragments = ["  Jakarta  ", "", "  ", "Indonesia"]
    assert join_texts(fragments) == "Jakarta Indonesia"


def test_join_texts_custom_separator() -> None:
    """``join_texts`` honours a custom separator."""
    assert join_texts(["a", "b", "c"], separator=", ") == "a, b, c"


# ---------------------------------------------------------------------------
# parse_job_card
# ---------------------------------------------------------------------------


def test_parse_job_card_extracts_all_fields(job_card_html: str) -> None:
    """``parse_job_card`` returns the four canonical fields for the first card."""
    selector = cast(Selector, Selector(text=job_card_html))
    first_card = selector.css(JOB_CARD_SELECTOR)[0]
    result = parse_job_card(first_card)

    assert result["job_title"] == "Data Analyst"
    assert (
        result["job_url"]
        == "https://glints.com/id/opportunities/jobs/12345/data-analyst-pt-abc"
    )
    assert result["company_name"] == "PT ABC Tech"
    assert result["job_location"] == "Jakarta"


def test_parse_job_card_iterates_all_cards(job_card_html: str) -> None:
    """All four fixture cards parse without raising."""
    selector = cast(Selector, Selector(text=job_card_html))
    cards = selector.css(JOB_CARD_SELECTOR)

    assert len(cards) >= 3, "fixture must contain at least 3 cards"

    for card in cards:
        result = parse_job_card(card)
        # title may legitimately be empty for a malformed card; everything
        # else must be present as a string-or-None type.
        assert "job_title" in result
        assert "job_url" in result
        assert "company_name" in result
        assert "job_location" in result


def test_parse_job_card_handles_relative_url(job_card_html: str) -> None:
    """Relative ``href`` values are absolutised against the default base URL."""
    selector = cast(Selector, Selector(text=job_card_html))
    card = selector.css(JOB_CARD_SELECTOR)[0]
    result = parse_job_card(card)
    assert result["job_url"] is not None
    assert result["job_url"].startswith("https://glints.com")


def test_parse_job_card_handles_absolute_url(job_card_html: str) -> None:
    """Already-absolute URLs are returned as-is, without double prefixing."""
    selector = cast(Selector, Selector(text=job_card_html))
    # Card 2 in the fixture uses an absolute URL.
    card = selector.css(JOB_CARD_SELECTOR)[1]
    result = parse_job_card(card)
    assert (
        result["job_url"]
        == "https://glints.com/id/opportunities/jobs/67890/backend-engineer-pt-xyz"
    )


def test_parse_job_card_custom_base_url() -> None:
    """A custom ``base_url`` is honoured when absolutising relative links."""
    html = """
    <html><body>
      <div class="CompactJobCard">
        <a class="JobCardTitle" href="/foo">Title</a>
        <a class="CompanyLinkResolver" aria-label="Job card company name: Co">Co</a>
        <div class="CardJobLocation"><div>Jakarta</div></div>
      </div>
    </body></html>
    """
    selector = cast(Selector, Selector(text=html))
    card = selector.css(JOB_CARD_SELECTOR)[0]
    result = parse_job_card(card, base_url="https://example.test")
    assert result["job_url"] == "https://example.test/foo"


def test_parse_job_card_missing_company() -> None:
    """A card without ``aria-label`` falls back to ``""`` for the company."""
    html = """
    <html><body>
      <div class="CompactJobCard">
        <a class="JobCardTitle" href="/jobs/1">Engineer</a>
        <a class="CompanyLinkResolver">Inner Text Only</a>
        <div class="CardJobLocation"><div>Jakarta</div></div>
      </div>
    </body></html>
    """
    selector = cast(Selector, Selector(text=html))
    card = selector.css(JOB_CARD_SELECTOR)[0]
    result = parse_job_card(card)
    # When aria-label is missing we get "" (not None).
    assert result["company_name"] == ""


def test_parse_job_card_strips_aria_label_prefix() -> None:
    """The standard Glints ``aria-label`` prefix is stripped off."""
    html = """
    <html><body>
      <div class="CompactJobCard">
        <a class="JobCardTitle" href="/jobs/1">Engineer</a>
        <a class="CompanyLinkResolver" aria-label="Job card company name: PT Bar">PT Bar</a>
        <div class="CardJobLocation"><div>Jakarta</div></div>
      </div>
    </body></html>
    """
    selector = cast(Selector, Selector(text=html))
    card = selector.css(JOB_CARD_SELECTOR)[0]
    result = parse_job_card(card)
    assert result["company_name"] == "PT Bar"


def test_parse_job_card_multiline_location(job_card_html: str) -> None:
    """Multi-line locations are joined into a single space-separated string."""
    selector = cast(Selector, Selector(text=job_card_html))
    # Card 3 in the fixture has Jakarta + Selatan.
    card = selector.css(JOB_CARD_SELECTOR)[2]
    result = parse_job_card(card)
    assert result["job_location"] == "Jakarta Selatan"


def test_parse_job_card_missing_location() -> None:
    """A card without a location block yields ``""`` for the location field."""
    html = """
    <html><body>
      <div class="CompactJobCard">
        <a class="JobCardTitle" href="/jobs/1">Engineer</a>
        <a class="CompanyLinkResolver" aria-label="Job card company name: Co">Co</a>
      </div>
    </body></html>
    """
    selector = cast(Selector, Selector(text=html))
    card = selector.css(JOB_CARD_SELECTOR)[0]
    result = parse_job_card(card)
    assert result["job_location"] == ""


def test_parse_job_card_whitespace_title() -> None:
    """Stray whitespace inside the title element is trimmed by ``clean_text``."""
    html = """
    <html><body>
      <div class="CompactJobCard">
        <a class="JobCardTitle" href="/jobs/1">
          Senior Data Analyst
        </a>
        <a class="CompanyLinkResolver" aria-label="Job card company name: Co">Co</a>
        <div class="CardJobLocation"><div>Jakarta</div></div>
      </div>
    </body></html>
    """
    selector = cast(Selector, Selector(text=html))
    card = selector.css(JOB_CARD_SELECTOR)[0]
    result = parse_job_card(card)
    assert result["job_title"] == "Senior Data Analyst"


# ---------------------------------------------------------------------------
# parse_job_detail
# ---------------------------------------------------------------------------


def test_parse_job_detail_full(job_detail_html: str) -> None:
    """All six canonical fields are populated for a complete detail page."""
    selector = cast(Selector, Selector(text=job_detail_html))
    result = parse_job_detail(selector)

    assert result["job_description"].startswith(
        "We are looking for a Data Analyst"
    )
    assert "2+ years of experience with Python and SQL" in result["job_description"]
    assert result["skill_tags"] == "Python, SQL, Tableau"
    assert "IDR" in result["job_salary"]
    # The flat-div fixture has no labels -> overview fields fall back to "".
    assert result["job_education"] == ""
    assert result["job_method"] == ""
    assert result["job_experience"] == ""


def test_parse_job_detail_description_multiparagraph(job_detail_html: str) -> None:
    """Paragraphs in the description block are joined with newlines."""
    selector = cast(Selector, Selector(text=job_detail_html))
    result = parse_job_detail(selector)
    description = result["job_description"]
    lines = description.split("\n")
    assert len(lines) >= 3
    assert lines[0] == "We are looking for a Data Analyst to join our team."
    assert "2+ years of experience with Python and SQL" in description


def test_parse_job_detail_skill_tags_comma_separated(job_detail_html: str) -> None:
    """Skill tags are joined with ``", "``."""
    selector = cast(Selector, Selector(text=job_detail_html))
    result = parse_job_detail(selector)
    assert result["skill_tags"] == "Python, SQL, Tableau"


def test_parse_job_detail_salary_with_currency(job_detail_html: str) -> None:
    """Salary text contains a currency marker (IDR)."""
    selector = cast(Selector, Selector(text=job_detail_html))
    result = parse_job_detail(selector)
    assert "IDR" in result["job_salary"]


def test_parse_job_detail_missing_description() -> None:
    """Detail page with no description block yields ``""`` for that field."""
    html = """
    <html><body>
      <h1>Engineer</h1>
    </body></html>
    """
    selector = cast(Selector, Selector(text=html))
    result = parse_job_detail(selector)
    assert result["job_description"] == ""
    assert result["job_education"] == ""
    assert result["job_method"] == ""
    assert result["job_experience"] == ""
    assert result["job_salary"] == ""
    assert result["skill_tags"] == ""


# ---------------------------------------------------------------------------
# overview_field (label-based, resilient to reorder)
# ---------------------------------------------------------------------------


def test_overview_field_by_label() -> None:
    """Direct lookup by label text returns the matching value."""
    html = """
    <html><body>
      <div class="JobOverViewInfoContainer">
        <div>
          <span>Minimal pendidikan</span>
          <div>S1</div>
        </div>
        <div>
          <span>Tipe pekerjaan</span>
          <div>Hybrid</div>
        </div>
        <div>
          <span>Pengalaman kerja</span>
          <div>2-3 tahun</div>
        </div>
      </div>
    </body></html>
    """
    selector = cast(Selector, Selector(text=html))
    assert (
        overview_field(selector, OVERVIEW_LABELS["education"]) == "S1"
    )
    assert (
        overview_field(selector, OVERVIEW_LABELS["work_method"])
        == "Hybrid"
    )
    assert (
        overview_field(selector, OVERVIEW_LABELS["experience"])
        == "2-3 tahun"
    )


def test_overview_field_resilient_to_reorder(
    job_detail_reordered_html: str,
) -> None:
    """Overview children are mapped correctly even when reordered."""
    selector = cast(Selector, Selector(text=job_detail_reordered_html))
    assert (
        overview_field(selector, OVERVIEW_LABELS["education"]) == "S1"
    )
    assert (
        overview_field(selector, OVERVIEW_LABELS["work_method"])
        == "Remote"
    )
    assert (
        overview_field(selector, OVERVIEW_LABELS["experience"])
        == "5+ tahun"
    )


def test_overview_field_missing_label_returns_empty() -> None:
    """No overview container -> empty string for any label."""
    html = "<html><body><h1>No overview here</h1></body></html>"
    selector = cast(Selector, Selector(text=html))
    assert (
        overview_field(selector, OVERVIEW_LABELS["education"]) == ""
    )


def test_overview_field_case_insensitive() -> None:
    """Label lookup is case-insensitive (trims and lowercases both sides)."""
    html = """
    <html><body>
      <div class="JobOverViewInfoContainer">
        <div><span>minimal pendidikan</span><div>D3</div></div>
      </div>
    </body></html>
    """
    selector = cast(Selector, Selector(text=html))
    assert (
        overview_field(selector, OVERVIEW_LABELS["education"]) == "D3"
    )


def test_overview_field_unknown_label() -> None:
    """Unknown label returns empty without raising."""
    html = """
    <html><body>
      <div class="JobOverViewInfoContainer">
        <div><span>Minimal pendidikan</span><div>S1</div></div>
      </div>
    </body></html>
    """
    selector = cast(Selector, Selector(text=html))
    assert overview_field(selector, "Tidak ada label ini") == ""


def test_overview_field_empty_label() -> None:
    """Empty label string is a no-op returning empty."""
    html = "<html><body></body></html>"
    selector = cast(Selector, Selector(text=html))
    assert overview_field(selector, "") == ""
