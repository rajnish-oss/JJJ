import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel
from app.services.geofence import create_infrastructure_geofence
from app.scrapers.officialLink import search_organization
from app.orchestrator import graph 
from langchain_core.runnables import RunnableConfig
from app.services.geofence import check_user_geofence
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings
from app.db.db import create_civic_report, retrieve_report
from IPython.display import Image, display
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from datetime import datetime



app = FastAPI()


class WorkflowRequest(BaseModel):
    org_name: str


class GeofenceRequest(BaseModel):
    address: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins; specify list like ["http://localhost:3000"] for production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

async def main(report):
    return await asyncio.to_thread(create_civic_report, report)


def run_workflow_stream(org_name: str, config: RunnableConfig):
    display(Image(graph.get_graph(xray=True).draw_mermaid_png()))

    final_state = graph.invoke({"org_name": org_name}, config=config)
    return final_state


@app.post("/enter-org-to-fence")
async def root(request: Request):
    try:
        body = await request.json()
        address = body.get("address")
        if not address:
            raise HTTPException(status_code=422, detail="Missing address")

        report = await retrieve_report(address)
        if report is None:
            config: RunnableConfig = {"configurable": {"thread_id": "1"}}
            result = await asyncio.to_thread(
                run_workflow_stream,
                address,
                config,
            )
            report = result.get("report")
            print("result-main", report)
            if isinstance(report, BaseModel):
                report = report.model_dump(mode="json")

            if report is None:
                raise HTTPException(status_code=500, detail="Workflow did not generate a report.")

            report["organization"] = address
            report["sources"] = result.get("page_urls", [])
            await create_civic_report(report)
        return create_infrastructure_geofence(address)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected successfully.")

    try:
        while True:
            try:
                # 1. Safely receive and parse JSON
                data = await websocket.receive_json()

                # Validate payload structure safely
                if "lat" not in data or "lon" not in data:
                    await websocket.send_json({"error": "Missing 'lat' or 'lon' in payload."})
                    continue

                # 2. Prevent event loop blocking
                user_geofence = await run_in_threadpool(check_user_geofence, data["lat"], data["lon"])

                if user_geofence is None:
                    await websocket.send_json({
                        "error": "User is not inside a tracked infrastructure geofence."
                    })
                    continue

                # 3. Retrieve and send report
                report = await retrieve_report(user_geofence["display_name"])

                if report is None:
                    await websocket.send_json({"error": f"Report {user_geofence['display_name']} not found."})
                    continue

                report["created_at"] = report["created_at"].isoformat()
                report["updated_at"] = report["updated_at"].isoformat()

                await websocket.send_json({"report": report})

            except WebSocketDisconnect:
                # Catch actual disconnects immediately so they don't hit the blanket Exception block
                print("Client disconnected cleanly during communication.")
                break

            except Exception as internal_err:
                print(f"Error processing message: {internal_err}")
                try:
                    # Only attempt to send the error if the socket is still alive
                    await websocket.send_json({"error": "Internal processing error."})
                except Exception:
                    # If we fail to send the error message, the connection is dead.
                    print("Failed to send error message. Socket is dead.")
                    break

    except Exception as e:
        # This now only catches fatal failures outside the communication loop
        print(f"Fatal connection error: {e}")

    # No finally block needed. FastAPI natively closes the connection when the function ends.
    print("WebSocket endpoint lifecycle completed.")

@app.post("/run-workflow")
async def run_workflow(request: WorkflowRequest):
    try:
        config: RunnableConfig = {"configurable": {"thread_id": "1"}}
        result = await asyncio.to_thread(run_workflow_stream, request.org_name, config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

