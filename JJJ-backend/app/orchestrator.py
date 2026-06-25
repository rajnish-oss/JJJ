from typing import Any, TypedDict
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from app.scrapers.officialLink import search_organization
from app.scrapers.scrapeLinkArray import collect_links_from_pages
from app.scrapers.scrapeInfoContent import scrapeInfoContent
from app.utils.models import whichPageLink,whichInfoLink,cleanAndParseData



class OrchestratorState(TypedDict, total=False):
    org_name: str
    search_results: list[dict[str, Any]]
    page_urls: list[str]
    collected_links: list[dict[str, Any]]
    content: list[dict[str,str]]
    report: Any


def _prioritize_info_links(collected_links: list[dict[str, Any]], limit: int = 60) -> list[dict[str, Any]]:
    tokens = (
        "about",
        "about-us",
        "aboutus",
        "mission",
        "platform",
        "issues",
        "policy",
        "campaign",
        "contact",
        "team",
    )

    scored: list[tuple[int, dict[str, Any]]] = []
    for item in collected_links:
        href = str(item.get("href", "")).lower()
        text = str(item.get("text", "")).lower()
        haystack = f"{href} {text}"
        score = sum(1 for token in tokens if token in haystack)
        scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:limit]]

def scrapeLinks(state: OrchestratorState):
    collected_links = state.get("page_urls", [])
    print("scraping links")
    content = scrapeInfoContent(collected_links)

    return {"content": content}


def makeReport(state: OrchestratorState):
    content = state.get("content", [])
    orgs = state.get("org_name")

    print("making report")

    data = cleanAndParseData(content,orgs)

    return {"report": data}

def getCorrectPageLink(state: OrchestratorState):
    search_results = state.get("search_results", [])
    orgs = state.get("org_name")

    if orgs is None or not search_results:
        return END

    data = whichPageLink(search_results, orgs)

    # LangGraph nodes should return partial state updates (a dict)
    return {"page_urls": data.url}


def getCorrectInfoLink(state: OrchestratorState):
    collected_links = state.get("collected_links", [])
    orgs = state.get("org_name")
    if orgs is None or not collected_links:
        return END

    candidates = _prioritize_info_links(collected_links, limit=60)
    data = whichInfoLink(candidates, orgs)

    return {"content": scrapeInfoContent(data.url)}

def search_organization_node(state: OrchestratorState):

    org_name = state.get("org_name")
    if not org_name:
        raise ValueError("org_name is required")
    results = search_organization(org_name)
    page_urls = [
        result["official_link"]
        for result in results
        if isinstance(result.get("official_link"), str)
    ]
    return {"search_results": results}


def collect_links_node(state: OrchestratorState):

    page_urls = state.get("page_urls", [])
    collected_links = collect_links_from_pages(page_urls)
    return {"collected_links": collected_links}

graph = StateGraph(OrchestratorState)

graph.add_node("search_organization", search_organization_node)
graph.add_node("collect_links_from_pages", collect_links_node)
graph.add_node("getCorrectPageLink", getCorrectPageLink)
graph.add_node("scrapeLinks", scrapeLinks)
graph.add_node("finalData",makeReport)
graph.add_edge(START, "search_organization")
graph.add_edge("search_organization", "getCorrectPageLink")
graph.add_edge("getCorrectPageLink", "scrapeLinks")
graph.add_edge("scrapeLinks", "finalData")
graph.add_edge("finalData", END)

checkpointer = InMemorySaver()
config: RunnableConfig = {"configurable": {"thread_id": "1"}}

graph = graph.compile(checkpointer=checkpointer)
