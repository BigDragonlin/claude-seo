#!/usr/bin/env python3
"""Create a compact, repeatable live-audit summary for Springvive.

This helper keeps the network crawl, HTML inspection, and report data separate
so the final PDF can cite one small JSON evidence file instead of many raw
pages. It only reads public URLs listed by the site's own sitemap.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

# Reuse the repository's SSRF-safe HTTP helper rather than calling requests
# directly. The project root is added so this script works from the repo root.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from url_safety import safe_requests_get  # noqa: E402


# ---------------------------------------------------------------------------
# Sitemap loading and URL grouping
# ---------------------------------------------------------------------------

def load_sitemap_urls(path: Path) -> list[str]:
    """Return every <loc> value from a standard XML sitemap."""

    root = ET.parse(path).getroot()
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [
        node.text.strip()
        for node in root.findall("sm:url/sm:loc", namespace)
        if node.text
    ]


def language_from_url(url: str) -> str:
    """Read the first path segment as the locale code."""

    parts = [part for part in urlparse(url).path.split("/") if part]
    return parts[0] if parts else "root"


# ---------------------------------------------------------------------------
# Per-page HTML inspection
# ---------------------------------------------------------------------------

def text_word_count(soup: BeautifulSoup) -> int:
    """Count meaningful words while excluding repeated site chrome."""

    content = soup.find("main") or soup.body or soup
    for tag in content.find_all(["script", "style", "noscript"]):
        tag.decompose()
    text = content.get_text(" ", strip=True)
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text))


def collect_schema_types(value: object, output: set[str]) -> None:
    """Recursively collect every Schema.org @type value."""

    if isinstance(value, dict):
        schema_type = value.get("@type")
        if isinstance(schema_type, str):
            output.add(schema_type)
        elif isinstance(schema_type, list):
            output.update(item for item in schema_type if isinstance(item, str))
        for child in value.values():
            collect_schema_types(child, output)
    elif isinstance(value, list):
        for child in value:
            collect_schema_types(child, output)


def parse_page(url: str, status: int, html: str) -> dict[str, object]:
    """Extract the SEO signals needed by the audit report."""

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description_tag = soup.find("meta", attrs={"name": "description"})
    description = description_tag.get("content", "").strip() if description_tag else ""
    robots_tag = soup.find("meta", attrs={"name": "robots"})
    robots = robots_tag.get("content", "").strip().lower() if robots_tag else ""
    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""
    h1_values = [tag.get_text(" ", strip=True) for tag in soup.find_all("h1")]

    hreflang = {
        tag.get("hreflang", "").strip(): tag.get("href", "").strip()
        for tag in soup.find_all("link", attrs={"hreflang": True})
    }

    schema_types: set[str] = set()
    schema_errors = 0
    schema_text_parts: list[str] = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text()
        schema_text_parts.append(raw)
        try:
            collect_schema_types(json.loads(raw), schema_types)
        except json.JSONDecodeError:
            schema_errors += 1

    images = soup.find_all("img")
    missing_alt = sum(
        1 for image in images if image.get("alt") is None or not image.get("alt", "").strip()
    )
    missing_dimensions = sum(
        1 for image in images if not image.get("width") or not image.get("height")
    )

    page_text = soup.get_text(" ", strip=True)
    schema_text = " ".join(schema_text_parts)
    placeholder_patterns = [
        r"\bSpecification\s+[a-z]\b",
        r"\bValue\s+[a-z]\b",
        r"\bMain text aa\b",
    ]
    placeholders = sorted(
        {
            match.group(0)
            for pattern in placeholder_patterns
            for match in re.finditer(pattern, f"{page_text} {schema_text}", re.IGNORECASE)
        }
    )

    internal_links = sorted(
        {
            link.get("href", "").strip()
            for link in soup.find_all("a", href=True)
            if link.get("href", "").startswith("/")
        }
    )

    return {
        "url": url,
        "status": status,
        "title": title,
        "title_length": len(title),
        "description": description,
        "description_length": len(description),
        "robots": robots,
        "canonical": canonical,
        "h1": h1_values,
        "word_count": text_word_count(soup),
        "hreflang_count": len(hreflang),
        "hreflang_self": hreflang.get("en") == url,
        "schema_types": sorted(schema_types),
        "schema_json_errors": schema_errors,
        "schema_placeholders": placeholders,
        "image_count": len(images),
        "missing_alt": missing_alt,
        "missing_dimensions": missing_dimensions,
        "internal_links": internal_links,
    }


def fetch_and_parse(url: str) -> dict[str, object]:
    """Fetch one public page, then return a compact inspection record."""

    response = safe_requests_get(
        url,
        timeout=30,
        allow_redirects=True,
        headers={"User-Agent": "ClaudeSEO-Audit/2.0"},
    )
    return parse_page(url, response.status_code, response.text)


# ---------------------------------------------------------------------------
# Site-level aggregation
# ---------------------------------------------------------------------------

def duplicate_groups(pages: list[dict[str, object]], field: str) -> list[dict[str, object]]:
    """Return repeated non-empty titles or descriptions."""

    grouped: dict[str, list[str]] = defaultdict(list)
    for page in pages:
        value = str(page.get(field, "")).strip()
        if value:
            grouped[value].append(str(page["url"]))
    return [
        {"value": value, "count": len(urls), "urls": urls}
        for value, urls in grouped.items()
        if len(urls) > 1
    ]


def build_summary(
    sitemap_urls: list[str],
    pages: list[dict[str, object]],
    locale_home_pages: list[dict[str, object]],
) -> dict[str, object]:
    """Aggregate the crawl into report-ready facts."""

    sitemap_set = set(sitemap_urls)
    language_counts = Counter(language_from_url(url) for url in sitemap_urls)
    page_by_url = {str(page["url"]): page for page in pages}

    resource_page = page_by_url.get("https://www.springvivechiller.com/en/resource", {})
    discovered_articles = sorted(
        "https://www.springvivechiller.com" + href
        for href in resource_page.get("internal_links", [])
        if href.startswith("/en/resource/") and href.count("/") >= 3
    )

    chillers_page = page_by_url.get(
        "https://www.springvivechiller.com/en/products/chillers", {}
    )
    discovered_products = sorted(
        "https://www.springvivechiller.com" + href
        for href in chillers_page.get("internal_links", [])
        if href.startswith("/en/products/") and href != "/en/products/chillers"
    )

    product_pages = [
        page
        for page in pages
        if "/en/products/" in str(page["url"])
        and str(page["url"]).count("/") >= 5
    ]
    resource_articles = [
        page
        for page in pages
        if "/en/resource/" in str(page["url"])
    ]

    return {
        "generated_at": "2026-07-26",
        "sitemap": {
            "total_urls": len(sitemap_urls),
            "language_counts": dict(sorted(language_counts.items())),
            "english_urls": language_counts.get("en", 0),
            "all_https": all(url.startswith("https://") for url in sitemap_urls),
        },
        "multilingual": {
            "homepages_checked": len(locale_home_pages),
            "titles": [
                {
                    "locale": language_from_url(str(page["url"])),
                    "title": page["title"],
                    "description": page["description"],
                    "status": page["status"],
                }
                for page in locale_home_pages
            ],
            "duplicate_title_groups": duplicate_groups(locale_home_pages, "title"),
            "duplicate_description_groups": duplicate_groups(
                locale_home_pages, "description"
            ),
        },
        "crawl": {
            "pages_checked": len(pages),
            "non_200": [
                {"url": page["url"], "status": page["status"]}
                for page in pages
                if page["status"] != 200
            ],
            "missing_canonical": [
                page["url"] for page in pages if not page["canonical"]
            ],
            "canonical_mismatch": [
                {"url": page["url"], "canonical": page["canonical"]}
                for page in pages
                if page["canonical"] and page["canonical"] != page["url"]
            ],
            "noindex": [
                page["url"] for page in pages if "noindex" in page["robots"]
            ],
            "h1_issues": [
                {"url": page["url"], "h1": page["h1"]}
                for page in pages
                if len(page["h1"]) != 1
            ],
            "duplicate_titles": duplicate_groups(pages, "title"),
            "duplicate_descriptions": duplicate_groups(pages, "description"),
        },
        "content": {
            "thin_under_100": [
                {"url": page["url"], "word_count": page["word_count"]}
                for page in pages
                if page["word_count"] < 100
            ],
            "thin_under_300": [
                {"url": page["url"], "word_count": page["word_count"]}
                for page in pages
                if page["word_count"] < 300
            ],
            "product_pages_checked": len(product_pages),
            "product_pages_under_400": [
                {"url": page["url"], "word_count": page["word_count"]}
                for page in product_pages
                if page["word_count"] < 400
            ],
            "resource_articles_checked": len(resource_articles),
            "resource_articles_under_800": [
                {"url": page["url"], "word_count": page["word_count"]}
                for page in resource_articles
                if page["word_count"] < 800
            ],
        },
        "schema": {
            "types": dict(
                Counter(
                    schema_type
                    for page in pages
                    for schema_type in page["schema_types"]
                )
            ),
            "pages_without_schema": [
                page["url"] for page in pages if not page["schema_types"]
            ],
            "json_errors": [
                {"url": page["url"], "count": page["schema_json_errors"]}
                for page in pages
                if page["schema_json_errors"]
            ],
            "placeholder_pages": [
                {"url": page["url"], "values": page["schema_placeholders"]}
                for page in pages
                if page["schema_placeholders"]
            ],
        },
        "images": {
            "total_images": sum(page["image_count"] for page in pages),
            "missing_alt": sum(page["missing_alt"] for page in pages),
            "missing_dimensions": sum(
                page["missing_dimensions"] for page in pages
            ),
        },
        "discovery": {
            "resource_articles_found": discovered_articles,
            "resource_articles_missing_from_sitemap": [
                url for url in discovered_articles if url not in sitemap_set
            ],
            "products_found_on_chillers_page": discovered_products,
            "products_missing_from_sitemap": [
                url for url in discovered_products if url not in sitemap_set
            ],
        },
        "pages": pages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sitemap", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sitemap_urls = load_sitemap_urls(args.sitemap)
    english_urls = [
        url for url in sitemap_urls if language_from_url(url) == "en"
    ]

    # url_safety deliberately pins DNS in process-global state and therefore
    # must run sequentially. This also keeps pressure on the public site low.
    pages = [fetch_and_parse(url) for url in english_urls]

    # The resource listing may expose live articles that the sitemap forgot.
    # Fetch those discovered pages too, so "missing from sitemap" does not
    # become a blind spot in the content and schema sections.
    resource_page = next(
        (
            page
            for page in pages
            if page["url"] == "https://www.springvivechiller.com/en/resource"
        ),
        None,
    )
    discovered_article_urls = []
    if resource_page:
        discovered_article_urls = sorted(
            "https://www.springvivechiller.com" + href
            for href in resource_page["internal_links"]
            if href.startswith("/en/resource/") and href.count("/") >= 3
        )
    pages.extend(
        fetch_and_parse(url)
        for url in discovered_article_urls
        if url not in set(english_urls)
    )

    pages.sort(key=lambda page: str(page["url"]))

    # Sample the homepage in every locale to verify that international metadata
    # is genuinely localized instead of copied from English.
    locale_home_urls = sorted(
        url
        for url in sitemap_urls
        if len([part for part in urlparse(url).path.split("/") if part]) == 1
    )
    page_by_url = {str(page["url"]): page for page in pages}
    locale_home_pages = [
        page_by_url[url] if url in page_by_url else fetch_and_parse(url)
        for url in locale_home_urls
    ]

    summary = build_summary(sitemap_urls, pages, locale_home_pages)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({key: summary[key] for key in summary if key != "pages"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
