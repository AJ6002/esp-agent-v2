"""ESP APM Standalone Agent Service V2.

Runs on Port 8092 by default.
Exposes:
- GET /health: Healthcheck and connector status
- POST /query: Streaming NDJSON endpoint for <AgentDock /> React UI
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.config import settings
from app.db.esp_db import check_esp_db_health
from app.ai.router import ask_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agent_service_v2")

app = FastAPI(
    title="ESP APM Agent Service V2",
    description="Standalone Industrial Diagnostic Microservice for ESP Artificial Lift",
    version="2.0.0",
)

# Enable CORS for all frontends (Vite port 5173, Next.js port 3000, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequestPayload(BaseModel):
    session_id: str | None = None
    message: str
    well_id: str | None = None
    asset_id: str | None = None
    page_route: str | None = None
    time_range: str | None = None
    conversation_history: list[dict] | None = None


@app.get("/health")
def health_endpoint():
    db_ok = check_esp_db_health()
    return {
        "status": "HEALTHY" if db_ok else "DEGRADED",
        "service": "esp-agent-service-v2",
        "port": settings.PORT,
        "database_connected": db_ok,
        "llm_api_base": settings.LLM_API_BASE,
    }


async def stream_query_response(payload: QueryRequestPayload) -> AsyncGenerator[str, None]:
    try:
        # Frame 1: Status (Routing)
        yield json.dumps({
            "type": "status",
            "stage": "ROUTING",
            "progress": 0.15,
            "message": "Analyzing query intent & identifying asset...",
        }) + "\n"

        target_well = payload.well_id or payload.asset_id
        if payload.page_route and not target_well:
            # Extract from route e.g. /wells/FS-017
            parts = payload.page_route.strip("/").split("/")
            if len(parts) >= 2 and parts[0] == "wells":
                target_well = parts[1]

        # Frame 2: Status (Processing)
        yield json.dumps({
            "type": "status",
            "stage": "DIAGNOSING",
            "progress": 0.50,
            "message": "Querying Server 184 SCADA telemetry & physics baseline models...",
        }) + "\n"

        # Execute deterministic logic + LLM synthesis
        result = ask_agent(
            question=payload.message,
            well_id=target_well,
            conversation_history=payload.conversation_history,
        )

        # Frame 3: Clarification Frame (if needed)
        if result.get("needs_clarification"):
            yield json.dumps({
                "type": "clarification",
                "question": result.get("markdown_text", ""),
                "options": result.get("suggested_options", []),
            }) + "\n"
            yield json.dumps({"type": "done", "status": "COMPLETED"}) + "\n"
            return

        # Frame 4: Status (Synthesizing)
        yield json.dumps({
            "type": "status",
            "stage": "SYNTHESIS",
            "progress": 0.85,
            "message": "Formatting engineering report & recommendations...",
        }) + "\n"

        # Frame 5: Text Delta Frame (Stream the markdown content)
        text_content = result.get("markdown_text", "")
        # Stream in chunks for smooth progressive rendering in <AgentDock />
        chunk_size = 120
        for i in range(0, len(text_content), chunk_size):
            yield json.dumps({
                "type": "text_delta",
                "delta": text_content[i : i + chunk_size],
            }) + "\n"

        # Frame 6: Advisory Frame (if structured diagnosis data exists)
        if result.get("intent") == "EVENT_DIAGNOSE" and result.get("structured_data"):
            s_data = result["structured_data"]
            yield json.dumps({
                "type": "advisory",
                "advisory": {
                    "event_id": s_data.get("event_id"),
                    "well_id": s_data.get("well_id"),
                    "trip_cause": s_data.get("trip_cause"),
                    "severity": s_data.get("severity"),
                    "confidence": result.get("confidence", 0.95),
                    "hypotheses": s_data.get("hypotheses", []),
                    "deviations": s_data.get("deviations", []),
                    "next_steps": s_data.get("next_steps", []),
                },
            }) + "\n"

        # Frame 7: Done Sentinel
        yield json.dumps({"type": "done", "status": "COMPLETED"}) + "\n"

    except Exception as e:
        logger.error(f"Error handling query: {e}", exc_info=True)
        yield json.dumps({
            "type": "error",
            "code": "PIPELINE_ERROR",
            "message": str(e),
        }) + "\n"
        yield json.dumps({"type": "done", "status": "FAILED"}) + "\n"


@app.post("/query")
async def query_endpoint(payload: QueryRequestPayload):
    return StreamingResponse(
        stream_query_response(payload),
        media_type="application/x-ndjson",
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
    )
