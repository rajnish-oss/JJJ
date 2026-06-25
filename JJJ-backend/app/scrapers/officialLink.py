from urllib.parse import quote_plus, urljoin, urlparse, parse_qs, unquote
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait


MAX_SEARCH_RESULTS = int(os.getenv("AI_AGENT_MAX_SEARCH_RESULTS", "6"))
ENRICH_METADATA = os.getenv("AI_AGENT_ENRICH_METADATA", "false").lower() == "true"
METADATA_ENRICHMENT_LIMIT = int(os.getenv("AI_AGENT_METADATA_LIMIT", "2"))


def _normalize_duckduckgo_link(link):
    if not link:
        return ""

    if link.startswith("http://") or link.startswith("https://"):
        return link

    if link.startswith("/l/?"):
        parsed = urlparse(link)
        query = parse_qs(parsed.query)
        target = query.get("uddg", [""])[0]
        if target:
            return unquote(target)

    if link.startswith("/"):
        return urljoin("https://html.duckduckgo.com", link)

    return link


def extract_page_metadata(driver):
    metadata = {
        "page_meta_description": "",
        "page_meta_keywords": "",
    }

    try:
        desc = driver.find_elements(By.XPATH, "//meta[translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='description'] | //meta[translate(@property, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='og:description']")
        if desc:
            metadata["page_meta_description"] = desc[0].get_attribute("content") or ""
    except Exception:
        pass

    try:
        keys = driver.find_elements(By.XPATH, "//meta[translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='keywords']")
        if keys:
            metadata["page_meta_keywords"] = keys[0].get_attribute("content") or ""
    except Exception:
        pass

    return metadata


def enrich_results_with_metadata(driver, results):
    if driver is None:
        print("Skipping metadata enrichment because driver is None")
        return results

    print(f"Starting metadata enrichment for {len(results)} results")
    enriched_results = []

    for i, result in enumerate(results, start=1):
        if i > METADATA_ENRICHMENT_LIMIT:
            enriched_results.append(result)
            continue

        enriched = result.copy()
        link = result.get("official_link")

        if not isinstance(link, str) or not link.startswith("http"):
            print(f"Skipping invalid link for result #{i}: {link}")
            enriched_results.append(enriched)
            continue

        try:
            print(f"Visiting result #{i}: {link}")
            driver.set_page_load_timeout(10)
            driver.get(link)
            print(f"Loaded result #{i}, extracting metadata")
            meta = extract_page_metadata(driver)
            enriched.update(meta)
            print(f"Extracted metadata for result #{i}: desc_len={len(meta.get('page_meta_description',''))}")
        except Exception as e:
            print(f"Failed to extract metadata for result #{i}: {e}")
            enriched.setdefault("page_meta_description", "")
            enriched.setdefault("page_meta_keywords", "")

        enriched_results.append(enriched)

    return enriched_results


def search_organization(org_name):
    query = f"{org_name} official website"
    duckduckgo_url = f"https://duckduckgo.com/?q={quote_plus(query)}&ia=web"
    print(f"search_organization started for: {org_name}")
    print(f"Constructed DuckDuckGo URL: {duckduckgo_url}")

    print("Initializing Selenium search path")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)

    try:
        print(f"Navigating to DuckDuckGo results for: '{org_name}'...")
        driver.set_page_load_timeout(12)
        print(f"Opening DuckDuckGo URL: {duckduckgo_url}")
        driver.get(duckduckgo_url)
        print(f"Page loaded: {driver.current_url}")

        try:
            print("Waiting for DuckDuckGo results to appear...")
            wait = WebDriverWait(driver, 6)
            wait.until(
                lambda page: len(page.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a']")) > 0
                or len(page.find_elements(By.CSS_SELECTOR, "article")) > 0
            )
            print("DuckDuckGo results appeared")
        except TimeoutException:
            print("Timed out waiting for DuckDuckGo results")

        results = []
        # DuckDuckGo uses article[data-testid='result'] for organic results
        for article in driver.find_elements(By.CSS_SELECTOR, "article[data-testid='result']"):
            try:
                title_el = article.find_element(By.CSS_SELECTOR, "a[data-testid='result-title-a']")
                title = title_el.text.strip()
                link = title_el.get_attribute("href")
            except Exception:
                continue

            # snippet is inside div[data-result='snippet']
            snippet = "No metadata description available."
            try:
                snippet_el = article.find_element(By.CSS_SELECTOR, "div[data-result='snippet'] span")
                snippet = snippet_el.text.strip()
            except Exception:
                # try generic snippet container
                try:
                    snippet_el = article.find_element(By.CSS_SELECTOR, ".OgdwYG6KE2qthn9XQWFC")
                    snippet = snippet_el.text.strip()
                except Exception:
                    pass

            if isinstance(link, str) and link.startswith("http"):
                print(f"DuckDuckGo result: {title} -> {link}")
                results.append(
                    {
                        "organization": org_name,
                        "title": title or org_name,
                        "official_link": link,
                        "metadata_snippet": snippet,
                        "description": snippet,
                    }
                )
                if len(results) >= MAX_SEARCH_RESULTS:
                    break

        print(f"Collected {len(results)} DuckDuckGo results")
        if ENRICH_METADATA and results:
            print(f"Enriching metadata for up to {METADATA_ENRICHMENT_LIMIT} results")
            enriched = enrich_results_with_metadata(driver, results)
            print(f"Enriched {len(enriched)} results")
            print("Returning enriched Selenium results")
            return enriched

        print("Returning Selenium results")
        return results

    except Exception as e:
        print(f"Error fetching DuckDuckGo content: {e}")
    finally:
        print("Closing Selenium driver")
        driver.quit()

    print("No results returned")
    return []

