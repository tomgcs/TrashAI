# CLAUDE.md

Guidance for Claude sessions working on this repo. README.md is the human-facing pitch; this file is the operational context.

## What this is

TrashAI is a civic-reporting companion for NYC. User uploads a photo of a street issue → app extracts location (EXIF or geocoded address, constrained to NYC) → classifies it with Claude Vision → pins it on a shared map as a circular photo marker → shows a hand-curated 311 reporting guide. **We never submit 311 reports — we only guide the user to the right form.** That's an intentional scope limit: no API integrations, no liability, no wrong reports filed on anyone's behalf.

Built for the **CUNY AI Innovation Challenge — Spring 2026**, Software track, "AI for Environmental Sustainability" theme. Two-day hackathon scope (Fri 2026-04-24 → Sat 2026-04-25).

## Live deployment

- **Production URL:** https://trashai-5appeqpxzalkzbg3njjjmun.streamlit.app
- **Hosted on:** Streamlit Community Cloud, free tier.
- **Branch:** `main` auto-deploys on every push (~30-60s delay). **There is no staging env — `main` is production.**
- **Rollback:** `git revert <sha> && git push` — auto-redeploys to working state.
- **Reboot without push:** dashboard → "Manage app" → "Reboot" (useful when the container is weird but code is fine).

## Stack

- Python 3.9 locally (system macOS), Python 3.11 on Streamlit Cloud and in the Codespaces devcontainer.
- Streamlit web UI.
- Anthropic SDK + **Claude Sonnet 4.6** (`claude-sonnet-4-6`) for vision classification.
- Pillow for EXIF GPS and image resize before the API call.
- geopy/Nominatim for address geocoding, restricted to NYC.
- folium + streamlit-folium for the map; pins render as circular photo markers via `DivIcon`.
- JSON file + images directory for persistence (see "Storage").

## File map

| File | Role |
|---|---|
| [streamlit_app.py](streamlit_app.py) | UI entry point. Two parallel render trees (desktop + mobile) with scoped CSS — see "Two render trees" below. Helpers: `_build_folium_map`, `_render_upload_panel`, `_render_mobile_panel`, `_render_desktop_layout`, `_render_mobile_layout`. Pin border-color map (`CATEGORY_COLORS`) lives here too. |
| [classify.py](classify.py) | Claude Vision call + image downscale + JSON parse + **stub fallback** when no API key. |
| [prompt.py](prompt.py) | The single classification prompt string. Defines the 15 category IDs. |
| [routing.py](routing.py) | `GUIDE` dict — category ID → agency, 311 link, service type, instructions. |
| [location.py](location.py) | EXIF GPS extraction + NYC-bounded Nominatim geocoding. |
| [storage.py](storage.py) | JSON-backed persistence: `load_pins`, `save_pin`, `load_image`. |
| [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) | Codespaces / VS Code dev container config (Python 3.11 + Streamlit auto-run on port 8501). |
| `data/pins.json` | Runtime-written pin list. Gitignored (ephemeral per container). |
| `data/images/` | Runtime-written user uploads. Gitignored except `.gitkeep`. |
| [.streamlit/secrets.toml](.streamlit/secrets.toml) | `ANTHROPIC_API_KEY`. Gitignored. |

## Critical conventions

### Category IDs are shared between three files
`prompt.py` tells Claude which category IDs to return. `routing.py` has a `GUIDE` dict keyed by those same IDs. `streamlit_app.py` has a `CATEGORY_COLORS` dict keyed by those same IDs (drives the pin's border color on the map). **If you add, rename, or remove a category, edit all three.** `routing.get_guide` and `CATEGORY_COLORS.get` both fall back to `"other"` / white for unknown IDs, so a mismatch fails soft but silently.

### "other" category does not save a pin
When Claude (or the stub) returns `category: "other"`, [streamlit_app.py](streamlit_app.py) shows a yellow warning and **skips `save_pin` and the result card entirely**. This is intentional — the map is for genuine NYC civic issues, not random photos. Don't drop this guard if you refactor the classify flow.

### Two render trees (desktop + mobile)
[streamlit_app.py](streamlit_app.py) renders **both** layouts every run, wrapped in `st.container(key="desktop-root")` and `st.container(key="mobile-root")`. CSS media queries hide whichever doesn't match the viewport. This is the architecture's load-bearing trick — earlier attempts to use one DOM tree + CSS reflow broke every time Streamlit's component wrappers changed shape (especially after file upload). Don't merge them back.

Consequences:
- **Two `st_folium` iframes per rerun** (one per layout). Acceptable at current pin counts; if it drags, add `@st.cache_data` on `_thumbnail`.
- **Widget keys must be unique across the two trees.** `_render_upload_panel(key_prefix)` accepts a prefix (`d` / `m`) and applies it to every `st.file_uploader`, `st.text_input`, `st.button` — otherwise Streamlit raises `DuplicateWidgetID`. The `st_folium` calls also need explicit `key=` (`d_map` / `m_map`) — `st_folium` auto-IDs from args and two identical map calls collide.
- **All CSS is scoped under `.st-key-desktop-root` or `.st-key-mobile-root`.** When you add a CSS rule, scope it to the right tree or it'll leak.
- **Mobile layout is pixel-tight.** Panel grows from `12vh` (pristine — no file, no result, detected via a hidden `[data-tai-pristine]` marker + CSS `:has()`) to `50vh` (after upload/result). Map fills the rest. The whole panel is capped — content must fit via density (horizontal columns), not scrolling. `st.columns` is force-flexed to `row` on mobile because Streamlit's default stacks them.
- **Shared session state.** `st.session_state.last_result` is shared across both trees, so a result card classified on desktop also appears on mobile after a viewport switch.

### Python 3.9 compatibility
Local dev is on macOS system Python 3.9. Do **not** use `X | Y` union syntax or `list[X]` / `dict[X, Y]` generic builtins in annotations — use `typing.Optional`, `typing.Tuple`, `typing.List`, `typing.Dict`. Streamlit Cloud runs 3.11 and so does the devcontainer, so either syntax works there — the constraint is local dev only.

### Stub classifier mode
[classify.py](classify.py) detects a placeholder `ANTHROPIC_API_KEY` (`""`, `"REPLACE_ME_WITH_YOUR_KEY"`, `"sk-ant-..."`) via `is_stub_mode()` and routes through `_stub_classify` instead of calling Anthropic. The stub hashes the image bytes and picks a deterministic category from a fixed list of 8. A yellow warning banner appears at the top of the app whenever stub mode is active. Real Claude is re-enabled just by pasting a valid key — no code changes.

Keep the stub working. It's how teammates without an API key develop the UI, and it's the fallback if the key ever expires mid-demo.

### Image downscale before Anthropic call
Anthropic caps image payloads at **5 MB base64** (~3.75 MB raw). Phone photos routinely exceed this. [classify.py](classify.py) has `_prepare_for_api` that resizes to max 1600px on the longest side + JPEG quality 85 before encoding. The **original full-resolution photo** is what gets written to disk and shown in the map popup — only the API-bound copy is downsized. Don't remove this without raising the API limit another way.

### Geocoding is bounded to NYC — EXIF is not
[location.py](location.py) calls Nominatim with `country_codes="us"`, `viewbox=[(40.477, -74.260), (40.920, -73.700)]`, and `bounded=True`. Typed addresses outside NYC return `None` rather than geocoding elsewhere. This prevents the "199 chamber street → UK" failure mode.

**`get_location_from_exif` is NOT bounded.** If a user uploads a photo taken in London, the EXIF GPS (51.51, -0.07) is returned as-is and the pin lands off the NYC map. This has already happened in the live `pins.json`. Intentional for now (keeps the uploader simple and doesn't punish genuinely-in-NYC users whose EXIF has a few meters of drift outside the viewbox), but if the user complains about foreign pins, gate EXIF through the same NYC viewbox check before accepting it.

If you ever widen scope beyond NYC, update the viewbox; don't remove `bounded=True` without replacement scoping.

### Pin schema
Each entry in `data/pins.json` is:
```json
{
  "lat": float, "lng": float,
  "category": "pothole",
  "display_name": "Pothole",
  "image": "<uuid>.jpg",
  "reasoning": "Claude's one-line explanation",
  "notable_details": "what the reporter should mention",
  "confidence": "low | medium | high"
}
```
`load_pins` and popup rendering use `.get()` with defaults, so older pins missing the three AI fields still render. Don't drop fields silently — update the schema intentionally.

### HTML escape AI output in popups
Popup HTML in [streamlit_app.py](streamlit_app.py) renders `display_name`, `reasoning`, `notable_details`, and `confidence` inside a Folium `<div>`. All four go through `html.escape()` before interpolation because they originate from a model response. Do not skip this if you add more AI-sourced fields to the popup.

### Storage model
- `data/pins.json` is a flat list. `save_pin` appends + rewrites the whole file (fine at N<1000).
- `load_pins` runs on every Streamlit rerun. No caching yet — if pins grow large, add `@st.cache_data` keyed on the file mtime.
- On Streamlit Cloud, the container filesystem is **shared across all visitors** but **ephemeral**: resets on every commit/redeploy, manual reboot, or long idle (~7 days). Acceptable for a demo.
- Do not commit `data/pins.json` or user images. `.gitignore` already handles this.

### Secrets
Local: `.streamlit/secrets.toml` (gitignored). Template at `.streamlit/secrets.toml.example`.
Cloud: paste the same TOML into the Streamlit Cloud app's "Secrets" UI (Manage app → ⋮ → Settings → Secrets). Changes there trigger a restart, not a redeploy.
Never commit a real key. Never print it to logs or UI. Never include it in an error message.

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

## Hardware / resource limits (Streamlit Community Cloud, free tier)

| Resource | Limit | Notes |
|---|---|---|
| RAM | ~1 GB | Baseline usage ~200 MB; safe for hundreds of pins. |
| CPU | Shared, fractional core | Slow but adequate. Latency is dominated by Claude API round-trip (~3-6s). |
| Disk | ~50 GB, ephemeral | Wiped on every redeploy / reboot / long idle. |
| Concurrent users | 1 container, 1 Streamlit worker | Queued under load. Fine for a hackathon demo. |
| GPU | None | Irrelevant — vision runs via API. |
| Cold start | ~20-30s | Warm the URL 5 min before a demo. |

## Demo-day rules

- **Do not push to `main` within ~30 minutes of a demo.** Every push wipes `data/pins.json` and `data/images/*`.
- **Warm the site with one page load** 5 min before the demo to avoid a cold-start during the pitch.
- **Seed pins manually** on the live site right before judging so the map isn't empty. They'll survive until the next deploy or ~7-day idle.

## Known limitations (intentional, not bugs)

- No auth, rate limits, or spam protection on pin creation.
- Nominatim geocoding has a ~1 req/s free-tier cap; fine for a hackathon.
- On-disk images are stored at original upload size. A 10 MB upload takes 10 MB of container disk. (Only the API-bound copy is resized.)
- Folium rerenders the whole map on every Streamlit rerun. OK under ~100 pins.
- No moderation: any uploaded image appears in any visitor's map popup.
- "Persistence across visitors" only lasts until the next redeploy/reboot.

## Things that are out of scope for this build

- Actually submitting 311 reports.
- Auth, accounts, or editing/deleting pins.
- Mobile-optimized camera capture (Streamlit's uploader works on mobile browsers but isn't a native camera button).
- Analytics, usage tracking, or abuse detection.
- A real database / image bucket (Supabase, Firebase, S3). Post-hackathon upgrade if crowd-sourced persistence becomes a real requirement.

Do not add these unless the user explicitly asks. They break "two-day hackathon scope."

## Tone

- Keep responses short. The user prefers direct answers to exploratory narration.
- Before running anything that modifies global state (brew install, system pip), ask first.
- When editing one of the shared-contract files (prompt.py ↔ routing.py), verify both sides.
- When adding a dependency, add it to `requirements.txt` in the same change.
- When two people are working on `main`, expect pull-rebase-push sometimes. Don't force-push.
