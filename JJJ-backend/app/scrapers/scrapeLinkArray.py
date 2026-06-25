from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse


MAX_LINKS_PER_PAGE = 120
MAX_TOTAL_LINKS = 180
PRIORITY_HINTS = (
    "about",
    "about-us",
    "mission",
    "platform",
    "issues",
    "policy",
    "campaign",
    "press",
    "news",
    "contact",
)


def _is_useful_link(base_host: str, href: str) -> bool:
    parsed = urlparse(href)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    # Prioritize internal links where campaign/info pages usually live.
    if parsed.netloc != base_host and not parsed.netloc.endswith(f".{base_host}"):
        return False

    return True


def _priority_score(href: str, text: str) -> int:
    haystack = f"{href} {text}".lower()
    return sum(1 for token in PRIORITY_HINTS if token in haystack)


def collect_links_from_pages(page_urls):
    """Given a list of page URLs, open each one and
    collect all links (href + text). Returns a list of dicts.
    """
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)  # or Chrome(), Edge(), etc.

    all_links = []
    seen = set()

    try:
        for url in page_urls:
            if len(all_links) >= MAX_TOTAL_LINKS:
                break

            driver.get(url)
            base_host = urlparse(url).netloc

            # Find all <a> elements on the page
            link_elements = driver.find_elements(By.TAG_NAME, "a")
            candidates = []

            for el in link_elements:
                href = el.get_attribute("href")
                text = el.text.strip()

                # Only keep links that actually have an href
                if not href or not _is_useful_link(base_host, href):
                    continue

                key = (url, href)
                if key in seen:
                    continue

                seen.add(key)
                candidates.append(
                    {
                        "page_url": url,  # page where we found this link
                        "href": href,
                        "text": text[:200],
                        "score": _priority_score(href, text),
                    }
                )

            candidates.sort(key=lambda x: x["score"], reverse=True)
            for item in candidates[:MAX_LINKS_PER_PAGE]:
                item.pop("score", None)
                all_links.append(item)
                if len(all_links) >= MAX_TOTAL_LINKS:
                    break

    finally:
        driver.quit()

    return all_links

