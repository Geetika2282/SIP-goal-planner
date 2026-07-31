# Deploying SIP Goal Planner

This app is a **Python backend (FastAPI + LangGraph)** that also serves the
frontend — not a static site. That matters for where it can be hosted.

## ⚠️ About Netlify

Netlify hosts **static sites and JavaScript serverless functions** — it
does not run a persistent Python process, which is what this app needs
(the FastAPI server, the LangGraph agent loop, the file-based `data/`
store). Deploying this repo to Netlify as-is will not work.

Two honest options if you want Netlify in the picture:

- **Easiest — skip Netlify, use a Python-friendly host instead.** Render,
  Railway, and Fly.io all support Python natively, connect straight to
  GitHub, and have free tiers. This gets your whole app (frontend + backend)
  live with one deploy. **This is the recommended path below.**
- **Split hosting (more setup, only if you specifically need Netlify).**
  Host `app/static/index.html` on Netlify as a static file, and the FastAPI
  backend separately on Render/Railway/Fly.io. You'd need to: point the
  frontend's `fetch()` calls at the backend's public URL instead of
  `window.location.origin`, and add CORS headers in `main.py` (FastAPI's
  `CORSMiddleware`) since the two would now be on different origins. Not
  covered step-by-step here since it adds real complexity for no benefit —
  Option 1 gives you the same result with far less work.

## ✅ Recommended: Render (free, connects to GitHub)

1. **Push this repo to GitHub** (skip if already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/sip-goal-planner.git
   git push -u origin main
   ```

2. **Create the web service**
   - Go to [dashboard.render.com](https://dashboard.render.com) → **New** → **Web Service**
   - Connect your GitHub account, select this repo
   - Render detects `render.yaml` in the repo root and pre-fills:
     - Environment: Python
     - Build command: `pip install -r requirements.txt`
     - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - Plan: Free

3. **Add your API key**
   - In the service's **Environment** tab, add `GROQ_API_KEY` with a free
     key from [console.groq.com/keys](https://console.groq.com/keys)
   - This is the only secret the app needs

4. **Deploy**
   - Render builds and starts the service — you get a public URL like
     `https://sip-goal-planner.onrender.com`
   - Every future `git push` to `main` auto-redeploys

**Free tier note:** the service sleeps after ~15 minutes of no traffic. The
first request after that takes 30–60s to wake it up — normal free-tier
behavior, not a bug.

**Data note:** Render's free tier has an *ephemeral filesystem* — anything
in `data/` (the ledger history) is wiped on restart or redeploy. Fine for a
demo; a persistent disk or a real database is the fix for production.

## Alternative: Railway

Same idea, different dashboard:

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Railway auto-detects Python and installs `requirements.txt`
3. Set the start command if it isn't auto-filled: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add `GROQ_API_KEY` under **Variables**
5. Deploy — Railway gives you a public URL, auto-redeploys on push

Railway's free allowance is credit-based rather than always-on-free, so
check current limits on their pricing page before relying on it long-term.

## Alternative: Fly.io (Docker-based)

This repo already includes a working `Dockerfile`, so Fly.io works out of
the box:

```bash
# 1. Install flyctl: https://fly.io/docs/flyctl/install/
fly auth login
fly launch          # detects the Dockerfile, asks a few setup questions
fly secrets set GROQ_API_KEY=your_key_here
fly deploy
```

Fly's free allowance covers small always-on apps like this one.

## Which one should I pick?

| Host | Setup effort | Good for |
|---|---|---|
| **Render** | Lowest — `render.yaml` does the work | First deploy, sharing a demo link |
| **Railway** | Low | If you prefer Railway's dashboard/DX |
| **Fly.io** | Medium (Docker/CLI) | If you want more control over the runtime |

For most people sharing a portfolio project, **Render** is the simplest
starting point.
