# SIP Goal Planner

A small agentic app that turns a plain-English SIP (Systematic Investment
Plan) goal into an instant financial plan — "I want ₹50 lakh in 10 years,
how much should I invest monthly?" in, the numbers and an explanation out.

Under the hood it's a **LangGraph** agent (backed by **Groq**) that picks
the right calculation, runs it, and explains the result — no hardcoded
if/else intent parsing. Full technical breakdown in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## What it does

- Understands goals in plain English, including Indian shorthand ("50 lakh", "1.2 crore")
- Solves for whichever value you're missing: monthly investment, target
  corpus, duration, or required rate of return
- Flags unrealistic goals and suggests an adjusted amount or timeline
- Keeps a running ledger of every entry, saved across page refreshes
- Stays on topic — it only answers SIP goal-planning questions

## Quickstart

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

## Publishing this repo to GitHub

```bash
cd sip-goal-planner
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/sip-goal-planner.git
git push -u origin main
```

`.env` and everything in `data/` are already git-ignored, so no API keys or
local logs get pushed by accident.

## Hosting a free public demo

Once it's on GitHub, you can spin up a live URL for free on
**[Render](https://render.com)**:

1. **dashboard.render.com → New → Web Service** → connect GitHub → pick
   this repo.
2. Render reads `render.yaml` in this repo and pre-fills everything
   (build command, start command, free plan).
3. In the service's **Environment** tab, add one variable:
   `GROQ_API_KEY` (from [console.groq.com/keys](https://console.groq.com/keys)).
4. Deploy. You get a public URL like `https://sip-goal-planner.onrender.com`,
   and every future `git push` auto-redeploys it.

Free-tier services sleep after ~15 min idle — the first request after that
takes 30–60s to wake up, which is expected on the free plan.

A `Dockerfile` is also included if you'd rather deploy via a
container-based host (Railway, Fly.io, etc.) instead.

## Tech stack

FastAPI · LangGraph · Groq (Llama 3.3 70B) · vanilla HTML/CSS/JS frontend,
no build step.

## License

MIT — do whatever you like with it.
