# Stack Decision

**Status:** pending — decision target is Day 2 morning (2026-04-25), once team skills are confirmed.

## Constraints

- 4-person team
- 2-day hackathon (Day 1: 2026-04-24, Day 2: 2026-04-25, final deadline 5pm Sat)
- Demo only — no real 311 API submission, no persistence, no auth
- Judging is based on a <5 min video, not live interaction
- Need ANTHROPIC_API_KEY to stay server-side (cannot be exposed to browser)

## Options

### A. Next.js (TypeScript) on Vercel

Frontend + API routes in one codebase. Deploys to a public URL.

- ✅ Polished, real-product look
- ✅ Single deploy, no CORS
- ✅ Shareable URL for the website deliverable
- ❌ Requires React/TS familiarity
- ❌ More setup surface area than needed for a demo

### B. Streamlit (Python)

Single Python file becomes a web app. Deploys free to Streamlit Community Cloud.

- ✅ Anyone with Python can contribute — lowest team coordination cost
- ✅ Fastest path from zero to working demo
- ✅ Handles file upload + layout out of the box
- ❌ Recognizable Streamlit aesthetic (not a blocker — video is what's judged)

### C. Gradio (Python)

Even simpler than Streamlit, but more rigid for multi-output UIs.

- ✅ Minimum code for input → output demos
- ❌ Harder to lay out three pieces of info (category + agency + report text) nicely
- Generally: if we'd pick Gradio, we'd pick Streamlit instead

## Decision criteria

**Primary:** does anyone on the team know React/JS/TS beyond basics?

- Yes → Option A is viable; weigh polish vs speed
- No → Option B, no debate

**Secondary:** does the team want a shareable URL for the website deliverable, or is a local demo recording fine?

- Shareable URL: A (Vercel) or B (Streamlit Cloud) both work
- Local demo: either, no advantage

## Current lean

Option B (Streamlit) unless a React-comfortable teammate steps forward. Reasoning: judging weights reward working AI + clear pitch, not frontend polish, and Streamlit frees the team to spend time on prompt quality and the routing taxonomy, which is where the points live.

## Decision

_TBD — fill in once confirmed with the team._
