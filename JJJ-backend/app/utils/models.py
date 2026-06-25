from ollama import chat
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from groq import Groq
from typing import List, Optional

load_dotenv()
client = Groq()


MAX_LINKS_FOR_LLM = 50
MAX_TEXT_LEN = 600
MAX_DOCS_FOR_REPORT = 6
MAX_DOC_TEXT_FOR_REPORT = 3000


def _compact_links(links):
    compact = []
    for item in links[:MAX_LINKS_FOR_LLM]:
        if isinstance(item, dict):
            compact.append(
                {
                    "href": (item.get("href") or item.get("url") or item.get("link") or "")[:MAX_TEXT_LEN],
                    "text": (item.get("text") or "")[:180],
                }
            )
        elif isinstance(item, str):
            compact.append({"href": item[:MAX_TEXT_LEN], "text": ""})
    return compact


def _compact_content(data):
    compact = []
    for item in data[:MAX_DOCS_FOR_REPORT]:
        if not isinstance(item, dict):
            continue
        compact.append(
            {
                "link": (item.get("link") or "")[:MAX_TEXT_LEN],
                "title": (item.get("title") or "")[:200],
                "content": (item.get("content") or "")[:MAX_DOC_TEXT_FOR_REPORT],
            }
        )
    return compact


class OperationalScale(BaseModel):
    budget_allocated: str = Field(
        ..., 
        description="The total budget allocated for the upcoming fiscal year in local currency, including any standard conversions (e.g., '₹5,500.92 crore ($570 million USD)'). Use standard text, do not use LaTeX."
    )
    faculty_count: str = Field(
        ..., 
        description="The number of academic/faculty members or specialists (e.g., '859 faculty members'). State 'DATA NOT AVAILABLE' if missing."
    )
    support_staff_count: str = Field(
        ..., 
        description="The number of administrative, technical, or support personnel (e.g., '10,701 personnel'). State 'DATA NOT AVAILABLE' if missing."
    )
    beneficiary_capacity: str = Field(
        ..., 
        description="The metric tracking end-users, students, or daily traffic capacity (e.g., '3,769 medical students'). State 'DATA NOT AVAILABLE' if missing."
    )


class CivicAwarenessReport(BaseModel):
    # Section 1: The Fabric of Accountability
    fabric_of_accountability: str = Field(
        ...,
        description=(
            "A cohesive paragraph establishing the physical and political landscape. "
            "Must open with the physical scale (acreage/location) and foundational purpose, "
            "explicitly state it is a taxpayer-funded public asset, name its founding year and governing body, "
            "and end with: 'To properly evaluate its service delivery and institutional performance, "
            "citizens must pull back the curtain on its operational and financial footprint.'"
        )
    )

    # Section 2: The Human and Financial Scale
    human_and_financial_scale_context: str = Field(
        ...,
        description="A transitional prose sentence synthesizing the scale metrics before breaking them down (e.g., 'To mobilize these vast public resources...')."
    )
    scale_metrics: OperationalScale = Field(
        ..., 
        description="Structured numerical data capturing the human and financial magnitude of the infrastructure asset."
    )

    # Section 3: The Transparency Gap
    transparency_gap_introduction: str = Field(
        ...,
        description=(
            "A paragraph analyzing what is missing from the public domain. Acknowledge that top-level governance "
            "and leadership (name the Director/Head if available) are cataloged, but state that infrastructure execution "
            "reveals critical blind spots. Lead directly into the missing indicators list."
        )
    )
    missing_accountability_metrics: List[str] = Field(
        ...,
        description=(
            "An explicit list of verified variables missing from public tracking. Must look for: "
            "1) Utilized expenditure vs sanctioned costs, 2) Timeline milestones/project delay durations, "
            "and 3) Identity of executing agencies, contractors, or active redevelopment master plans."
        )
    )
    transparency_gap_conclusion: str = Field(
        ...,
        description="A final analytical statement explaining how this data asymmetry leaves taxpayers completely in the dark regarding asset maintenance or operational execution."
    )

    # Section 4: Citizen Action Item
    citizen_action_item: str = Field(
        ...,
        description=(
            "A structured paragraph converting the critique into public utility. Must assert that transparency is "
            "actively maintained by an informed public. Provide a concrete next step (e.g., filing an RTI request or "
            "public records demand with the specific governing body) to compel disclosure of the hidden variables."
        )
    )
class linkStruct(BaseModel):
    url : list[str]



def whichPageLink(links,orgs):
    prompt = f"""
You are a precise link extraction assistant. Your task is to analyze a list of candidate URLs and select up to 3 links that are the most genuine, authoritative, and data-rich for a civic awareness and public accountability analysis.

The goal is to find links that will provide enough deep, factual content to generate a schema including: key facts, public interest significance, entities/people, dates/numbers, and potential structural risks or accountability concerns.

links: {links}
Organisation name: {orgs}

Apply the following evaluation rules strictly:

1. PRIORITY CRITERIA:
   - Favor official domains (.edu, .gov, .org, or specific institutional domains) that host primary data, administrative notices, official history, governance structures, or press releases.
   - Favor comprehensive news aggregators or educational portals ONLY if they contain detailed timelines, policy shifts, structural overviews, or public controversies surrounding the entity.

2. REJECTION CRITERIA:
   - Reject hyper-specific transactional pages (e.g., login screens, payment forms, narrow exam result portals).
   - Reject broken, empty, or placeholder URLs.

3. EVALUATION THOUGHT PROCESS:
   - Does this link contain concrete facts, dates, numbers, or names that matter to public interest?
   - Can a user evaluate civic impact, institutional risk, or governance quality from this link?

Output your final answer strictly in the following JSON format, choosing the top 1 to 3 best URLs. If absolutely no URLs are relevant or genuine, return an empty list.

{{"url": ["<selected_url_1>", "<selected_url_2>"]}}
"""
    response = chat(
        model="qwen2.5-coder:7b",
        messages = [{
            "role": "user",
            "content": prompt
        }],
        format=linkStruct.model_json_schema(),
    )
    
    print("response from whichPageLink",response)
    content = response.message.content
    if content is None:
        raise ValueError("LLM response did not include JSON content")

    return linkStruct.model_validate_json(content)

def whichInfoLink(links,orgs):
    compact_links = _compact_links(links)

    prompt = (
       
    )

    messages = [
        {
            "role": "user",
            "content": f"{prompt}\n\nCandidates: {compact_links}",
        }
    ]

    response = chat(
        model="qwen3.5:9b",
        messages=messages,
        format=linkStruct.model_json_schema(),
    )

    content = response.message.content
    if content is None:
        raise ValueError("LLM response did not include JSON content")

    return linkStruct.model_validate_json(content)

def cleanAndParseData(data,orgs):
    compact_data = _compact_content(data)
    prompt = f"""
        You are an investigative data journalist and public accountability auditor. Your task is to analyze scraped raw data for a piece of public infrastructure and synthesize it into a sharp, scannable public asset report. Your tone must be authoritative, objective, and deeply rooted in the principle of citizen oversight—treating the infrastructure as a taxpayer-funded public asset rather than just an institution.

Do not use empty fluff or generic praise. Lead with hard numbers, use brutal clarity regarding institutional opacity, and adhere strictly to the following four-section structure.

### Core Structure to Follow:

## 1. The Fabric of Accountability
*   **Objective:** Contextualize the asset within its physical and political landscape.
*   **Requirements:** 
    *   Open with a strong hook detailing the physical scale (e.g., acreage, location) and its foundational purpose.
    *   Explicitly state that it is a public asset funded directly by taxpayers.
    *   Mention its founding year, governing body/ministry, and operational status (e.g., autonomous).
    *   End the paragraph with a transitional sentence asserting that evaluating its performance requires pulling back the curtain on its operational and financial footprint.

## 2. The Human and Financial Scale
*   **Objective:** Quantify the sheer magnitude of the operation using hard data.
*   **Requirements:** 
    *   Detail the latest fiscal year budget allocation in local currency (and provide a conversion to USD in standard text, e.g., "$570 million USD").
    *   Enumerate the human infrastructure: break down workforce categories (e.g., faculty/specialists vs. administrative/support staff) and the end-user/beneficiary capacity (e.g., students, daily active users, or capacity).

## 3. The Transparency Gap: What Taxpayers Aren't Seeing
*   **Objective:** Execute a critical audit of what data is *missing* or obfuscated from the public domain.
*   **Requirements:** 
    *   Acknowledge that while top-level macro-allocations and leadership figures (name the Director/Head if available in the data) are tracked, the fine-grained execution is opaque.
    *   Highlight the critical blind spots or data asymmetry.
    *   Use a bulleted list to explicitly call out missing tracking data. Specifically look for absences in:
        *   Actual utilized expenditure vs. sanctioned project costs.
        *   Timeline milestones, project delays, or calculated durations of backlogs.
        *   Identity of primary executing agencies, chief contractors, or master plans.
    *   Conclude with a sharp analytical sentence explaining how this specific data asymmetry leaves taxpayers in the dark regarding asset maintenance or upgrades.

## 4. Citizen Action Item: Exercising Oversight
*   **Objective:** Convert the analysis into actionable civic utility.
*   **Requirements:** 
    *   State that transparency is actively maintained by an informed public.
    *   Provide a concrete, realistic next step for a citizen seeking to close this information gap (e.g., filing a targeted Right to Information/RTI request or public records demand with the specific governing ministry or institution).
    *   List the exact hidden variables they should compel the disclosure of (e.g., hidden project costs, penalty clauses, active maintenance contracts).

### Formatting & Data Rules:
*   **No Placeholders:** If specific data points (like acreage, specific staff counts, or the current director's name) are missing from the provided scraped data, state "DATA NOT AVAILABLE" inside that specific section rather than inventing facts.
*   **No Inline LaTeX for simple numbers/units:** Use standard text for currencies, units, and percentages (e.g., write "₹5,500.92 crore" or "$570 million USD"). Do not use LaTeX formatting unless expressing complex, multi-variable mathematical formulas.
*   **Tone:** Highly objective, analytical, and sharp. Avoid overly emotional rhetoric; let the missing data points generate the critical friction.

        Data Payload:
        {compact_data}
        """.strip()
    
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.2,
            max_completion_tokens=4096,
            top_p=1,
            stream=False,
            stop=None,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "civic_awareness_report",
                    "strict": False,
                    "schema": CivicAwarenessReport.model_json_schema(),
                },
            },
        )
        print("resp from cleanAndParseData", completion)
    except Exception as e:
        raise ValueError(f"Failed to generate report: {e}")
    content = completion.choices[0].message.content
    if content is None:
        raise ValueError("LLM response did not include JSON content")

    return CivicAwarenessReport.model_validate_json(content)


