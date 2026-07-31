"""
Simple file-based persistence for the SIP Goal Planner.

Two kinds of files are written, on purpose:

1. entries_store.json - the single source of truth the API reads/writes.
   Structured JSON so entries can be listed and deleted individually from
   the UI (each entry has a stable id).
2. qa_log.txt / tool_traces.txt - append-only, human-readable audit logs.
   These are NEVER rewritten or trimmed, even when an entry is deleted from
   the store above. That mirrors a standard "live state vs. audit log" split
   you'd see in a production system: what the UI shows can shrink, the
   record of what actually happened does not.

This is intentionally file-based (no DB) to keep the project dependency-free
for a portfolio/demo build. Swapping `_read_entries`/`_write_entries` for a
real datastore (SQLite/Postgres) is the natural next step - see README.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

ENTRIES_FILE = DATA_DIR / "entries_store.json"
QA_LOG_FILE = DATA_DIR / "qa_log.txt"
TRACE_LOG_FILE = DATA_DIR / "tool_traces.txt"

# Single-process lock: fine for a small demo app served by one uvicorn
# worker. A multi-worker/production deployment would need a real DB instead
# of file writes to stay correct under concurrent requests.
_lock = Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_entries() -> list[dict]:
    if not ENTRIES_FILE.exists():
        return []
    try:
        return json.loads(ENTRIES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _write_entries(entries: list[dict]) -> None:
    ENTRIES_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def list_entries() -> list[dict]:
    """Returns all persisted entries, oldest first, for rebuilding the UI on load."""
    with _lock:
        return _read_entries()


def save_entry(query: str, answer: str, tool_calls: list[dict], is_error: bool) -> dict:
    """Persists one Q&A round-trip: adds it to the JSON store and appends it
    to both human-readable txt logs. Returns the stored entry (with id + timestamp)."""
    entry = {
        "id": uuid.uuid4().hex[:12],
        "timestamp": _now_iso(),
        "query": query,
        "answer": answer,
        "tool_calls": tool_calls,
        "is_error": is_error,
    }

    with _lock:
        entries = _read_entries()
        entries.append(entry)
        _write_entries(entries)
        _append_qa_log(entry)
        _append_trace_log(entry)

    return entry


def delete_entry(entry_id: str) -> bool:
    """Removes an entry from the live JSON store only. Returns False if no
    entry with that id existed. The txt audit logs are append-only and keep
    the full historical record even after a UI delete."""
    with _lock:
        entries = _read_entries()
        remaining = [e for e in entries if e["id"] != entry_id]
        if len(remaining) == len(entries):
            return False
        _write_entries(remaining)
        return True


def _append_qa_log(entry: dict) -> None:
    lines = [
        f"[{entry['timestamp']}] id={entry['id']}",
        f"Q: {entry['query']}",
        f"A: {entry['answer']}",
        "-" * 60,
        "",
    ]
    with QA_LOG_FILE.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _append_trace_log(entry: dict) -> None:
    if not entry["tool_calls"]:
        return
    lines = [f"[{entry['timestamp']}] id={entry['id']} query=\"{entry['query']}\""]
    for call in entry["tool_calls"]:
        lines.append(f"  tool: {call['tool']}")
        lines.append(f"    args:   {json.dumps(call['args'])}")
        lines.append(f"    result: {json.dumps(call['result'])}")
    lines.append("-" * 60)
    lines.append("")
    with TRACE_LOG_FILE.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))
