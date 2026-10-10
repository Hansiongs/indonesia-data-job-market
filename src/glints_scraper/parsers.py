"""HTML parsers and CSS selectors for Glints job pages.

This module centralises all parsel-based parsing logic. The selectors were
distilled from the legacy ``1_scrape_links.py`` and ``3_scrape_details.py``
scripts and are exposed as module constants so that downstream modules can
reuse them without duplication.

The selectors are CSS-based (rather than XPath) because they are easier to
maintain when Glints occasionally tweaks class names; substring matching
with ``[class*="..."]`` provides enough resilience for our purposes.

Overview panel extraction in :func:`overview_field` is done by
label lookup rather than positional indexing. The legacy approach
(``//div[3]//text()`` etc.) silently broke whenever Glints reordered or
added a new field; the label-based approach is resilient to that.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from parsel import Selector


# ---------------------------------------------------------------------------
# Selectors for the job listing page
# ---------------------------------------------------------------------------

#: CSS selector for individual job cards inside the listing page.
JOB_CARD_SELECTOR: Final[str] = 'div[class*="CompactJobCard"]'

#: CSS selector for the title anchor inside a job card.
JOB_CARD_LINK_SELECTOR: Final[str] = 'a[class*="JobCardTitle"]'

#: CSS selector for the company anchor inside a job card.
COMPANY_LINK_SELECTOR: Final[str] = 'a[class*="CompanyLinkResolver"]'

#: CSS selector for the location block inside a job card.
LOCATION_SELECTOR: Final[str] = 'div[class*="CardJobLocation"]'


# ---------------------------------------------------------------------------
# Selectors for the job detail page
# ---------------------------------------------------------------------------

#: CSS selector for the description block on a detail page.
JOB_DESC_SELECTOR: Final[str] = 'div[class*="JobDescriptionsc"]'

#: CSS selector for an individual skill tag.
SKILL_TAG_SELECTOR: Final[str] = 'p[class*="Skillssc__TagName"]'

#: CSS selector for the salary block on a detail page.
SALARY_SELECTOR: Final[str] = 'span[class*="BasicSalary"]'

#: CSS selector for the "Job Overview" container that holds structured fields.
OVERVIEW_CONTAINER_SELECTOR: Final[str] = 'div[class*="JobOverViewInfoContainer"]'


# ---------------------------------------------------------------------------
# Label text in the overview panel (Indonesian labels from Glints ID locale)
# ---------------------------------------------------------------------------

#: Human-readable label texts as they appear in the rendered overview panel.
#: Used by :func:`overview_field` to locate fields by text rather than by
#: DOM position.
OVERVIEW_LABELS: Final[dict[str, str]] = {
    "education": "Minimal pendidikan",
    "work_method": "Tipe pekerjaan",
    "experience": "Pengalaman kerja",
}

#: Prefix that Glints prepends to ``aria-label`` on company links in cards.
COMPANY_ARIA_LABEL_PREFIX: Final[str] = "Job card company name: "


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------


def clean_text(text: str | None) -> str:
    if text is None:
        return ""
    return text.strip()


def join_texts(texts: list[str], separator: str = " ") -> str:
    cleaned = [fragment.strip() for fragment in texts]
    return separator.join(item for item in cleaned if item)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _absolutise_url(url: str | None, base_url: str) -> str | None:
    if not url:
        return None
    if url.startswith(("http://", "https://")):
        return url
    # Strip a trailing slash on base_url so we don't end up with "//foo".
    return f"{base_url.rstrip('/')}{url}"


def _strip_company_aria_label(label: str | None) -> str:
    cleaned = clean_text(label)
    if cleaned.startswith(COMPANY_ARIA_LABEL_PREFIX):
        return cleaned[len(COMPANY_ARIA_LABEL_PREFIX):]
    return cleaned


def overview_field(selector: Selector, label: str) -> str:
    """Find an overview field by its visible label text."""
    if not label:
        return ""
    container = selector.css(OVERVIEW_CONTAINER_SELECTOR)
    if not container:
        return ""
    target = label.strip().lower()
    for label_span in container.css("span"):
        if clean_text("".join(label_span.css("::text").getall())).lower() != target:
            continue
        value_div = label_span.xpath("following-sibling::div[1]")
        if value_div:
            return clean_text("".join(value_div.css("::text").getall()))
    return ""


# ---------------------------------------------------------------------------
# Public parsing functions
# ---------------------------------------------------------------------------


def parse_job_card(
    card: Selector,
    base_url: str = "https://glints.com",
) -> dict[str, Any]:
    """Parse a single Glints job card into a canonical dictionary."""
    # 1. Title: first matching anchor's text.
    title = card.css(f"{JOB_CARD_LINK_SELECTOR}::text").get()
    job_title = clean_text(title)

    # 2. URL: first matching anchor's href, absolutised when needed.
    href = card.css(f"{JOB_CARD_LINK_SELECTOR}::attr(href)").get()
    job_url = _absolutise_url(href, base_url)

    # 3. Company: aria-label of the company link, with prefix stripped.
    company_aria = card.css(f"{COMPANY_LINK_SELECTOR}::attr(aria-label)").get()
    company_name = _strip_company_aria_label(company_aria)

    # 4. Location: every text node inside the location block, joined.
    location_parts = card.css(f"{LOCATION_SELECTOR} ::text").getall()
    job_location = join_texts(location_parts)

    return {
        "job_title": job_title,
        "job_url": job_url,
        "company_name": company_name,
        "job_location": job_location,
    }


def parse_job_detail(selector: Selector) -> dict[str, Any]:
    """Parse a Glints job detail page into a canonical dictionary."""
    # 1. Description: every <p> inside the description block, joined with
    #    newlines so the caller can preserve paragraph boundaries.
    desc_blocks = selector.css(f"{JOB_DESC_SELECTOR} p")
    if desc_blocks:
        paragraphs = [
            clean_text("".join(p.css("::text").getall())) for p in desc_blocks
        ]
        # Drop empty paragraphs but keep order.
        job_description = "\n".join(p for p in paragraphs if p)
    else:
        # Fallback: take whatever text the description block carries.
        fallback_text = " ".join(
            selector.css(f"{JOB_DESC_SELECTOR}::text").getall()
        )
        job_description = clean_text(fallback_text)

    # 2. Skill tags: every tag's text, joined with ", " for human display.
    skill_parts = selector.css(f"{SKILL_TAG_SELECTOR}::text").getall()
    skill_tags = clean_text(", ".join(s.strip() for s in skill_parts if s))

    # 3. Salary: collect all text nodes inside the salary element.
    salary_parts = selector.css(f"{SALARY_SELECTOR}::text").getall()
    job_salary = join_texts(salary_parts)

    # 4-6. Overview fields: label-based extraction (resilient to reorders).
    job_education = overview_field(
        selector, OVERVIEW_LABELS["education"]
    )
    job_method = overview_field(
        selector, OVERVIEW_LABELS["work_method"]
    )
    job_experience = overview_field(
        selector, OVERVIEW_LABELS["experience"]
    )

    return {
        "job_description": job_description,
        "skill_tags": skill_tags,
        "job_salary": job_salary,
        "job_education": job_education,
        "job_method": job_method,
        "job_experience": job_experience,
    }


__all__ = [
    "COMPANY_ARIA_LABEL_PREFIX",
    "COMPANY_LINK_SELECTOR",
    "JOB_CARD_LINK_SELECTOR",
    "JOB_CARD_SELECTOR",
    "JOB_DESC_SELECTOR",
    "LOCATION_SELECTOR",
    "OVERVIEW_CONTAINER_SELECTOR",
    "OVERVIEW_LABELS",
    "SALARY_SELECTOR",
    "SKILL_TAG_SELECTOR",
    "clean_text",
    "join_texts",
    "overview_field",
    "parse_job_card",
    "parse_job_detail",
]
