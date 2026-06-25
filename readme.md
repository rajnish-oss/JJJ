# JJJ Civic Awareness Platform

JJJ is a location-aware civic accountability prototype. The app watches a user's browser geolocation, checks whether the user is inside a tracked public infrastructure boundary, and displays an AI-generated civic awareness report for that organization.

The project is split into two applications:

- `JJJ-backend/`: FastAPI backend for geofencing, report generation, scraping, Redis indexing, and MongoDB persistence.
- `jjj-frontend/`: Next.js frontend that connects to the backend over WebSocket and renders the live report UI.

## What It Does

1. A civic infrastructure or organization is submitted to the backend.
2. The backend resolves the location boundary using LocationIQ.
3. Boundary data is stored in Redis as a geofence.
4. If a report does not already exist, the backend searches the web, scrapes relevant pages, and uses an LLM workflow to generate a structured civic accountability report.
5. The browser watches the user's current location and streams coordinates to the backend.
6. When the user is inside a tracked geofence, the backend returns the stored report over WebSocket.
7. The frontend displays the report, including operational scale, transparency gaps, missing accountability metrics, and citizen action items.

## Tech Stack

### Backend

- Python
- FastAPI
- WebSockets
- LangGraph
- Pydantic
- MongoDB with Motor
- Redis geospatial indexing
- Selenium with Chrome
- LocationIQ geocoding API
- Ollama for local link-selection models
- Groq API for report generation

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- Native browser geolocation
- Native WebSocket client

## Repository Structure

```text
.
|-- JJJ-backend/
|   |-- main.py
|   `-- app/
|       |-- db/
|       |   |-- db.py
|       |   `-- model.py
|       |-- scrapers/
|       |   |-- officialLink.py
|       |   |-- scrapeInfoContent.py
|       |   `-- scrapeLinkArray.py
|       |-- services/
|       |   `-- geofence.py
|       |-- utils/
|       |   |-- generate_slug.py
|       |   `-- models.py
|       `-- orchestrator.py
|-- jjj-frontend/
|   |-- app/
|   |   |-- page.tsx
|   |   |-- layout.tsx
|   |   `-- components/
|   |       |-- infoCard.tsx
|   |       `-- radar.tsx
|   `-- package.json
`-- readme.md
```

## Prerequisites

Install these before running the full project:

- Python 3.11 or newer
- Node.js 20 or newer
- MongoDB instance
- Redis server running on `localhost:6379`
- Google Chrome or Chromium for Selenium
- Ollama running locally
- LocationIQ API key
- Groq API key

The current backend expects Redis at `localhost:6379` and the frontend expects the backend WebSocket at `ws://localhost:8000/ws`.

## Backend Setup

From the backend folder:

```bash
cd JJJ-backend
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```bash
pip install fastapi uvicorn pydantic pydantic-settings python-dotenv motor pymongo redis requests selenium langgraph langchain-core ollama groq ipython
```

Create `JJJ-backend/.env`:

```env
MONGO_URI=mongodb://localhost:27017
location_iq=your_locationiq_api_key
GROQ_API_KEY=your_groq_api_key

# Optional scraper tuning
AI_AGENT_MAX_SEARCH_RESULTS=6
AI_AGENT_ENRICH_METADATA=false
AI_AGENT_METADATA_LIMIT=2
```

Start Redis and MongoDB, then run the backend:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

## Ollama Setup

The backend uses Ollama models in `app/utils/models.py` for link selection.

Pull the expected models:

```bash
ollama pull qwen2.5-coder:7b
ollama pull qwen3.5:9b
```

Make sure Ollama is running before triggering the report-generation workflow.

## Frontend Setup

From the frontend folder:

```bash
cd jjj-frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

When prompted, allow location access. The app needs browser geolocation permission to stream coordinates to the backend.

## API Reference

### `POST /enter-org-to-fence`

Creates or refreshes a tracked infrastructure geofence for an organization or address. If a report does not already exist in MongoDB, this endpoint runs the report-generation workflow.

Request body:

```json
{
  "address": "AIIMS Delhi"
}
```

Behavior:

- Looks for an existing report by `organization`.
- If missing, searches for official pages, scrapes content, generates a civic awareness report, and stores it in MongoDB.
- Resolves the submitted address through LocationIQ.
- Seeds the resulting bounding boxes into Redis.

### `POST /run-workflow`

Runs the LangGraph report workflow directly for an organization name.

Request body:

```json
{
  "org_name": "AIIMS Delhi"
}
```

### `WebSocket /ws`

Receives live coordinates and returns a report when the user is inside a tracked geofence.

Client message:

```json
{
  "lat": 28.5672,
  "lon": 77.21
}
```

Server response when inside a tracked geofence:

```json
{
  "report": {
    "organization": "AIIMS Delhi",
    "fabric_of_accountability": "...",
    "human_and_financial_scale_context": "...",
    "scale_metrics": {
      "budget_allocated": "...",
      "faculty_count": "...",
      "support_staff_count": "...",
      "beneficiary_capacity": "..."
    },
    "transparency_gap_introduction": "...",
    "missing_accountability_metrics": ["..."],
    "transparency_gap_conclusion": "...",
    "citizen_action_item": "..."
  }
}
```

Server response when no geofence matches:

```json
{
  "error": "User is not inside a tracked infrastructure geofence."
}
```

## Report Schema

Reports are stored in MongoDB under the `civic_platform.reports` collection. Each report includes:

- `organization`
- `fabric_of_accountability`
- `human_and_financial_scale_context`
- `scale_metrics`
- `transparency_gap_introduction`
- `missing_accountability_metrics`
- `transparency_gap_conclusion`
- `citizen_action_item`
- `created_at`
- `updated_at`

## Development Notes

- The frontend currently hardcodes the backend WebSocket URL as `ws://localhost:8000/ws` in `jjj-frontend/app/page.tsx`.
- CORS is open in development with `allow_origins=["*"]`.
- Redis data is used for fast geofence lookups and is not the source of truth for reports.
- MongoDB stores the generated civic reports.
- Selenium requires a working Chrome or Chromium installation.
- The report workflow depends on external websites, so scraping quality may vary by page availability, bot protection, and response format.
- Browser geolocation usually requires `localhost` or HTTPS.

## Common Workflow

1. Start MongoDB.
2. Start Redis.
3. Start Ollama and confirm the required models are available.
4. Start the FastAPI backend on port `8000`.
5. Seed a geofence with `POST /enter-org-to-fence`.
6. Start the Next.js frontend on port `3000`.
7. Open the frontend and allow location access.

## Useful Commands

```bash
# Backend
cd JJJ-backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd jjj-frontend
npm run dev

# Frontend lint
cd jjj-frontend
npm run lint
```

## Current Limitations

- There is no backend `requirements.txt` yet.
- Redis connection settings are hardcoded to `localhost:6379`.
- The frontend WebSocket URL is hardcoded for local development.
- The backend opens CORS broadly for development.
- Geofencing currently uses bounding boxes from LocationIQ, not precise polygon boundaries.
- Report accuracy depends on the quality of scraped public data and the LLM output.

## Suggested Next Improvements

- Add a `requirements.txt` or `pyproject.toml` for backend dependency management.
- Move Redis host, Redis port, and frontend backend URL into environment variables.
- Add a seed script for common infrastructure locations.
- Add automated tests for geofence matching and report persistence.
- Replace broad CORS settings with environment-specific allowed origins.
- Add loading and permission-denied states to the frontend geolocation flow.
