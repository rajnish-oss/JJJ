from urllib.parse import urlparse
import re
from html import unescape

import requests


REQUEST_TIMEOUT = (5, 12)
MAX_CONTENT_CHARS = 7000


def _normalize_link(link):
    if isinstance(link, dict):
        link = link.get("href") or link.get("url") or link.get("link")

    if not isinstance(link, str):
        return None

    link = link.strip().strip('"').strip("'")
    if not link.startswith(("http://", "https://")):
        return None

    parsed = urlparse(link)
    if not parsed.scheme or not parsed.netloc:
        return None

    return link


def _extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return re.sub(r"\s+", " ", unescape(match.group(1))).strip()[:300]


def _html_to_text_excerpt(html: str) -> str:
    html = re.sub(r"<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style\b[^<]*(?:(?!</style>)<[^<]*)*</style>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    return text[:MAX_CONTENT_CHARS]

def scrapeInfoContent(links):
    scraped_data = []
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
    )

    for link in links:
        normalized_link = _normalize_link(link)
        if normalized_link is None:
            continue

        try:
            response = session.get(normalized_link, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            html = response.text
            scraped_data.append(
                {
                    "link": normalized_link,
                    "title": _extract_title(html),
                    "content": _html_to_text_excerpt(html),
                }
            )
        except Exception as exc:
            print(f"Skipping unreadable link {normalized_link}: {exc}")

    return scraped_data

    return scraped_data