# Architecture & Technical Reference

This doc covers how SIP Goal Planner works internally — useful for
extending the project, or for walking through the design in an interview.
For install/run/deploy steps, see the main [README](../README.md).

## Agent architecture (LangGraph)

```
        START
          │
          ▼
      ┌────────┐
      │ agent  │◄──────────┐
      │ (LLM)  │           │
      └───┬────┘           │
          │                │
   tool_calls present?     │
      /        \           │
   yes          no         │
    │            │         │
    ▼            ▼         │
 ┌───────┐      END        │
 │ tools │─────────────────┘
 └───────┘
```

- **`agent` node** — calls the Groq LLM with the 5 calculator tools bound to it.
- **`tools` node** — a LangGraph `ToolNode` that executes whichever tool(s)
  the LLM requested.
- **`tools_condition`** — conditional edge: if the LLM's last message contains
  tool calls, route to `tools`; otherwise the LLM has produced a final
  natural-language answer (or a refusal), so route to `END`.
- The loop (`tools → agent`) lets the model call a tool, see the result,
  and either call another tool (e.g. recompute with an adjusted SIP amount)
  or explain the result to the user.

## End-to-end request flow

1. Browser hits `/` → FastAPI serves `app/static/index.html`.
2. Page load also calls `GET /entries` to rebuild the ledger from anything
   persisted in a previous session, so a refresh doesn't lose history.
3. User types a goal → JS `fetch()`s `POST /plan` with `{query}`.
4. `main.py` calls `get_sip_agent()` — the LangGraph graph (and the Groq
   client inside it) is built lazily on first use, so `/health` and the UI
   still come up even before `GROQ_API_KEY` is set.
5. **agent node**: prepends the system prompt (once per conversation) and
   calls the LLM with the 5 tools bound. The prompt runs, in order: a scope
   guard that refuses anything outside SIP goal planning (no tool call, fixed
   refusal message) before looking at the query at all; then lakh/crore
   conversion; then routing to the matching tool based on which 3 of
   {monthly amount, rate, years, target} are known — or, if nothing fits,
   asking for the missing piece instead of guessing.
6. **tools_condition**: if the LLM asked for a tool call → routes to the
   `tools` node (a `ToolNode` that runs the actual Python calculator
   function); if not (a refusal, a clarifying question, or a final answer) →
   routes straight to `END`.
7. **tools → agent loop**: the LLM sees the tool's numeric result and either
   calls another tool (e.g. recomputing with an adjusted SIP) or writes the
   final natural-language explanation — always stating any assumed rate.
8. `main.py` walks the message list, matches each `ToolMessage` back to its
   originating tool call via `tool_call_id`, and packages
   `{id, timestamp, answer, tool_calls}`.
9. The entry is **persisted** (`app/storage.py`) — written to
   `data/entries_store.json` (live state, used by the UI) and appended to
   `data/qa_log.txt` and `data/tool_traces.txt` (append-only audit logs).
10. Frontend renders the new numbered ledger entry: query in italics, each
    tool call as a sub-entry (nested values render recursively, so
    `compare_scenarios`' per-rate breakdown displays correctly instead of
    `[object Object]`), the final answer, and a stamp — "Computed" when a
    tool ran, "Noted" when the agent replied without one (a refusal or a
    clarifying question), "Entry Rejected" on a hard error. Each entry has
    a **Delete** button that calls `DELETE /entries/{id}`, removing it from
    the live store (the txt audit logs keep the full record regardless).

## Tools (calculators)

| Tool | Use case |
|---|---|
| `calculate_sip_future_value` | Know monthly amount + rate + years → get maturity value |
| `calculate_required_sip` | Know target amount + rate + years → get required monthly SIP |
| `calculate_required_duration` | Know monthly amount + rate + target → get time required |
| `calculate_required_rate` | Know monthly amount + target + years → get required annual return |
| `compare_scenarios` | Compare maturity value across multiple return-rate assumptions |

All calculators use the standard compound-growth SIP formula:

```
FV = P × [((1 + i)^n − 1) / i] × (1 + i)
```
where `P` = monthly investment, `i` = monthly rate, `n` = number of months.
`calculate_required_rate` has no closed-form inverse, so it solves for the
rate via binary search on the same formula.

## Scope guard

The agent only answers SIP goal-planning questions. A `STEP 0` guard in the
system prompt (`app/agent.py`) checks every incoming message before any of
the routing logic runs: if the query isn't about a SIP target amount,
monthly investment, rate, or timeline, the agent returns a fixed refusal
message and calls no tool — it will not answer general-knowledge, coding,
or unrelated questions, even if asked to "just this once." This is a
prompt-level guard (not a keyword filter), so it holds up against
rephrasing, but like any LLM-enforced rule it isn't a hard guarantee — a
production version would pair it with a lightweight output classifier as a
second layer.

## API reference

| Method | Path | What it does |
|---|---|---|
| `GET` | `/` | Serves the frontend |
| `GET` | `/health` | Backend liveness check |
| `POST` | `/plan` | Runs the agent on a query, persists and returns the result |
| `GET` | `/entries` | Returns all persisted Q&A entries (oldest first) |
| `DELETE` | `/entries/{id}` | Removes one entry from the live store |
| `GET` | `/docs` | Interactive Swagger API docs |

## Persistence / logging

No database — file-based on purpose, to keep the project dependency-free:

- `data/entries_store.json` — structured JSON, the live source of truth the
  API reads on `GET /entries`. Deleting an entry rewrites this file.
- `data/qa_log.txt` — append-only, human-readable question/answer log.
- `data/tool_traces.txt` — append-only, human-readable log of every tool
  call (name, args, result) per query.

The txt files are **never** rewritten by a delete — that's a deliberate
"live UI state vs. audit trail" split, the same pattern you'd see with a
real database + append-only log in production. The natural next step for a
production version is swapping `app/storage.py`'s two functions
(`_read_entries` / `_write_entries`) for a real datastore (SQLite/Postgres).

> **Note on free hosting:** platforms like Render's free tier have an
> *ephemeral filesystem* — anything written to `data/` is wiped on restart
> or redeploy. Fine for a live demo, but worth calling out explicitly (and
> a good thing to mention if asked about it in an interview) — the fix is a
> managed disk or a real DB, not a code change.

## Project structure

```
sip_goal_planner/
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI app + /plan, /entries endpoints + serves the UI
│   ├── agent.py             # LangGraph state graph + system prompt (lazy-built)
│   ├── calculators.py        # 5 tool functions (the financial math)
│   ├── storage.py             # File-based persistence (JSON store + txt audit logs)
│   ├── schemas.py              # Pydantic request/response models
│   └── static/
│       └── index.html           # Frontend - single-file HTML/CSS/JS
├── docs/
│   └── ARCHITECTURE.md            # This file
├── data/                          # Created at runtime; git-ignored except .gitkeep
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── render.yaml
└── README.md
```

## Frontend

A single-page site served directly by FastAPI at `http://localhost:8000/` —
no separate frontend server or build step needed. Pure HTML/CSS/JS, no
framework, no build step — one file: `app/static/index.html`.

- Talks to the backend via `fetch()` calls to `/plan`, `/entries`, and
  `/health` on the same origin, so no CORS setup is needed.
- A status indicator in the sticky navbar pings `/health` on load.
- History persists across refresh via `GET /entries` on page load.
- Each entry has a Delete button.
- If `GROQ_API_KEY` is missing, `/plan` returns a clean error and the UI
  shows it inline as a rejected entry, instead of the request silently
  hanging or the server crashing.

## Notes / things to extend for production

- Swap file-based storage for a real database (SQLite → Postgres) to survive
  restarts on ephemeral-filesystem hosts and to support concurrent writers.
- Add input validation guards (negative rates, zero years) before the LLM
  even calls the tool.
- Add retries/error handling around malformed tool-call arguments from the LLM.
- Add auth + rate limiting before exposing publicly.
- Pair the prompt-level scope guard with a lightweight classifier for a
  second layer of defense against off-topic queries.
