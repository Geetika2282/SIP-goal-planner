import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.agent import get_sip_agent
from app.schemas import PlanRequest, PlanResponse, ToolCallRecord, EntryRecord, DeleteResponse
from app import storage

app = FastAPI(
    title="SIP Goal Planner",
    description="Agentic AI financial assistant that interprets SIP goals and routes them to the correct calculator.",
    version="1.1.0",
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_ui():
    """Serves the passbook-style frontend. API docs remain at /docs."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/entries", response_model=list[EntryRecord])
def get_entries():
    """Returns previously persisted Q&A entries (oldest first) so the
    frontend can rebuild the ledger on page load / refresh."""
    return storage.list_entries()


@app.delete("/entries/{entry_id}", response_model=DeleteResponse)
def remove_entry(entry_id: str):
    """Removes one entry from the live store (and therefore from the UI on
    reload). The append-only txt audit logs are untouched by this."""
    deleted = storage.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return DeleteResponse(id=entry_id, deleted=True)


@app.post("/plan", response_model=PlanResponse)
def plan(request: PlanRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    try:
        agent = get_sip_agent()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    result = agent.invoke({"messages": [HumanMessage(content=request.query)]})
    messages = result["messages"]

    # Build a lookup of tool_call_id -> {tool name, args} from AI messages
    call_lookup: dict[str, dict] = {}
    for m in messages:
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                call_lookup[tc["id"]] = {"tool": tc["name"], "args": tc["args"]}

    tool_calls: list[ToolCallRecord] = []
    for m in messages:
        if isinstance(m, ToolMessage):
            meta = call_lookup.get(m.tool_call_id, {"tool": "unknown", "args": {}})
            try:
                parsed_result = json.loads(m.content)
            except (json.JSONDecodeError, TypeError):
                parsed_result = m.content
            tool_calls.append(
                ToolCallRecord(tool=meta["tool"], args=meta["args"], result=parsed_result)
            )

    final_answer = messages[-1].content if messages else ""

    # Persist the Q&A + tool trace to disk (JSON store + human-readable txt logs)
    saved = storage.save_entry(
        query=request.query,
        answer=final_answer,
        tool_calls=[tc.model_dump() for tc in tool_calls],
        is_error=False,
    )

    return PlanResponse(
        id=saved["id"],
        timestamp=saved["timestamp"],
        answer=final_answer,
        tool_calls=tool_calls,
    )
