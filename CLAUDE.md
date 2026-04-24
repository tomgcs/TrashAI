# CLAUDE.md

Guidance for Claude sessions working on this repo. README.md is the human-facing pitch; this file is the operational context.

## What this is

TrashAI is a civic-reporting companion for NYC. User uploads a photo of a street issue → app extracts location (EXIF or geocoded address) → classifies it with Claude Vision → pins it on a shared map → shows a hand-curated 311 reporting guide. **We never submit 311 reports — we only guide the user to the right form.** That's an intentional scope limit: no API integrations, no liability, no wrong reports filed on anyone's behalf.

Built for the **CUNY AI Innovation Challenge — Spring 2026**, Software track, "AI for Environmental Sustainability" theme. Two-day hackathon scope (Fri 2026-04-24 → Sat 2026-04-25).

## Stack

- Python 3.9 locally (system macOS), Python 3.11 on Streamlit Community Cloud.
- Streamlit web UI.
- Anthropic SDK + Claude Sonnet 4.6 for vision classification.
- Pillow for EXIF GPS; geopy/Nominatim for address geocoding.
- folium + streamlit-folium for the map.
- JSON file + images directory for persistence (see "Storage").

## File map

| File | Role |
|---|---|
| [streamlit_app.py](streamlit_app.py) | UI entry point: upload, location resolution, result card, map render. |
| [classify.py](classify.py) | Claude Vision call, JSON parse, **stub fallback** when no API key. |
| [prompt.py](prompt.py) | The single classification prompt string. Defines the 15 category IDs. |
| [routing.py](routing.py) | `GUIDE` dict — category ID → agency, 311 link, service type, instructions. |
| [location.py](location.py) | EXIF GPS extraction + Nominatim geocoding fallback. |
| [storage.py](storage.py) | JSON-backed persistence: `load_pins`, `save_pin`, `load_image`. |
| `data/pins.json` | Runtime-written pin list. Gitignored (ephemeral per container). |
| `data/images/` | Runtime-written user uploads. Gitignored except `.gitkeep`. |
| [.streamlit/secrets.toml](.streamlit/secrets.toml) | `ANTHROPIC_API_KEY`. Gitignored. |

## Critical conventions

### Category IDs are shared between two files
`prompt.py` tells Claude which category IDs to return. `routing.py` has a `GUIDE` dict keyed by those same IDs. **If you add, rename, or remove a category, edit both.** `routing.get_guide` falls back to `"other"` for unknown IDs, so a mismatch fails soft but silently.

### Python 3.9 compatibility
Local dev is on macOS system Python 3.9. Do **not** use `X | Y` union syntax or `list[X]` / `dict[X, Y]` generic builtins in annotations — use `typing.Optional`, `typing.Tuple`, `typing.List`, `typing.Dict`. Streamlit Cloud runs 3.11 so the app runs fine there either way, but local imports crash on 3.9 if you use the modern syntax.

### Stub classifier mode
[classify.py](classify.py) detects a placeholder `ANTHROPIC_API_KEY` (`""`, `"REPLACE_ME_WITH_YOUR_KEY"`, `"sk-ant-..."`) and routes through `_stub_classify` instead of calling Anthropic. The stub hashes the image bytes and picks a deterministic category. A yellow warning banner appears at the top of the app whenever stub mode is active. Real Claude is re-enabled just by pasting a valid key — no code changes.

Keep the stub working. It's how teammates without an API key develop the UI, and it's the fallback if the key ever expires mid-demo.

### Storage model (important)
- `data/pins.json` is a flat list of `{lat, lng, category, display_name, image}` dicts.
- `image` is a filename (UUID .jpg) living under `data/images/`.
- `save_pin` appends + rewrites the whole JSON file (fine at N<1000 pins).
- `load_pins` is called on every Streamlit rerun. No caching yet — if pins grow large, add `@st.cache_data` keyed on the file mtime.
- On Streamlit Community Cloud, the container filesystem is **shared across all visitors** but **ephemeral**. It resets on every commit/redeploy and after long idle periods. That's acceptable for a demo.
- Do not commit `data/pins.json` or user images. `.gitignore` already handles this.

### Secrets
Local: `.streamlit/secrets.toml` (gitignored). Template at `.streamlit/secrets.toml.example`.
Cloud: paste the same TOML into the Streamlit Cloud app's "Secrets" UI.
Never commit a real key. Never print the key to logs.

### Session state vs persistence
- `st.session_state.last_result` → per-visitor (their most recent classification). Intentional.
- Pins → shared across visitors via disk. Intentional.
- Do not put pins back into session_state. That regresses the crowd-sourced map claim.

## Running locally

```bash
# from TrashAI/ (the inner repo root)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # edit to add key (optional; stub mode works without)
.venv/bin/streamlit run streamlit_app.py
```

The venv lives at `.venv/` inside the repo. Always invoke `.venv/bin/streamlit` or `.venv/bin/python3` — do not rely on the system `streamlit`.

Harmless startup warning: `urllib3 ... LibreSSL 2.8.3`. It's a macOS-only SSL lib note, not an error.

## Deploying

Streamlit Community Cloud. Repo must be public (or Streamlit Cloud must be authorized as a GitHub app). Point the deploy at `streamlit_app.py`. Paste `ANTHROPIC_API_KEY` into the Secrets UI in TOML format. First deploy ~2 minutes; subsequent pushes auto-redeploy.

There is **no staging environment**. `main` is production.

## Known limitations (intentional, not bugs)

- No auth, rate limits, or spam protection on pin creation.
- Nominatim geocoding has a ~1 req/s free-tier cap; it's fine for a hackathon.
- Images are stored at original upload size. A 10MB upload takes 10MB of container disk.
- Folium rerenders the whole map on every Streamlit rerun. OK under ~100 pins.
- No moderation: any uploaded image appears in any visitor's map popup.

## Things that are out of scope for this build

- Actually submitting 311 reports.
- Geofencing to NYC (users could submit pins anywhere; the map is centered on NYC but not restricted).
- Auth, accounts, or editing/deleting pins.
- Mobile-optimized camera capture (Streamlit's uploader works on mobile browsers, just not as a native camera button).
- Analytics, usage tracking, or abuse detection.

Do not add these unless the user explicitly asks. They break "two-day hackathon scope."

## Tone

- Keep responses short. The user prefers direct answers to exploratory narration.
- Before running anything that modifies global state (brew install, system pip), ask first.
- When editing one of the shared-contract files (prompt.py ↔ routing.py), verify both sides.
- When adding a dependency, add it to `requirements.txt` in the same change.
