<div align="center">

# 💰 SIP Goal Planner: https://sip-goal-planner-1.onrender.com/

**Stop guessing. Start planning.**

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?style=flat-square&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-agent-1C3A56?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F55036?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-6FA88F?style=flat-square)

</div>

---

## 🎯 What is this?

Most people know roughly what they want — *"₹50 lakh in 10 years"* — but
not the fourth number that makes it math. **SIP Goal Planner** is a small
agentic app: you describe a SIP (Systematic Investment Plan) goal in one
sentence, and it figures out **which** number you're missing and computes
it for you.

No dropdowns, no forms with four required fields. Just:

> *"I want ₹50 lakh in 10 years, expecting 12% annual returns — how much should I invest monthly?"*

...and it answers with the exact monthly amount, the total you'll have
invested, and the total gain — worked out by an actual calculator function,
not guessed by the LLM.

### Use case

- **Individual investors** sanity-checking a savings goal before talking to
  an advisor
- **Learning tool** for understanding how monthly amount, rate, duration,
  and target amount trade off against each other
- **Reference implementation** of a tool-calling LangGraph agent — routing
  natural language to deterministic financial functions, with a scoped
  system prompt that refuses to answer anything off-topic

## ✨ Features

| | |
|---|---|
| 🧮 | Solves for **any one** of: monthly SIP, target amount, duration, or required return |
| 🇮🇳 | Understands Indian numbering shorthand — "50 lakh", "1.2 crore" |
| ⚖️ | Flags unrealistic goals and suggests an adjusted amount or timeline |
| 📒 | Ledger-style history, persisted across page refreshes |
| 🎯 | Strictly on-topic — refuses general-knowledge or unrelated questions |
| 🖥️ | Single-file HTML/CSS/JS frontend, no build step, no framework |

## 🛠️ Tech stack

- **Backend:** FastAPI, LangGraph, LangChain
- **LLM:** Groq (`llama-3.3-70b-versatile`) — free tier, low latency
- **Persistence:** file-based JSON store + append-only audit logs
- **Frontend:** vanilla HTML/CSS/JS, served directly by FastAPI

## 🚀 Clone & run locally

```bash
git clone https://github.com/<your-username>/sip-goal-planner.git
cd sip-goal-planner

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# edit .env and paste a free key from https://console.groq.com/keys

uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** for the app, **http://localhost:8000/docs**
for the interactive API reference.

## 📁 Project structure

```
sip_goal_planner/
├── app/
│   ├── main.py           # FastAPI app + endpoints, serves the UI
│   ├── agent.py            # LangGraph agent + system prompt
│   ├── calculators.py       # The 5 financial-calculation tools
│   ├── storage.py            # File-based persistence
│   ├── schemas.py             # Pydantic models
│   └── static/index.html        # Frontend
├── docs/
│   ├── ARCHITECTURE.md            # How the agent & request flow work
│   └── DEPLOYING.md                # Free hosting steps (Render / Railway / Fly.io)
├── requirements.txt
└── render.yaml
```

## 📚 More docs

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — how the LangGraph agent
  routes queries, the scope guard, the full request lifecycle, the API
  reference
- **[docs/DEPLOYING.md](docs/DEPLOYING.md)** — steps to put this live for
  free on Render, Railway, or Fly.io

## 📄 License

MIT — see [LICENSE](LICENSE). Do whatever you like with it.

---

<div align="center">
<sub>Built as a learning project. For illustration purposes only — not financial advice.</sub>
</div>
