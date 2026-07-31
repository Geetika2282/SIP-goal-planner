from pydantic import BaseModel
from typing import Any


class PlanRequest(BaseModel):
    query: str


class ToolCallRecord(BaseModel):
    tool: str
    args: dict[str, Any]
    result: Any


class PlanResponse(BaseModel):
    id: str
    timestamp: str
    answer: str
    tool_calls: list[ToolCallRecord] = []


class EntryRecord(BaseModel):
    """A persisted Q&A entry, as returned by GET /entries."""
    id: str
    timestamp: str
    query: str
    answer: str
    tool_calls: list[ToolCallRecord] = []
    is_error: bool = False


class DeleteResponse(BaseModel):
    id: str
    deleted: bool
