# CLAUDE.md

Guidance for Claude sessions working on this repo. README.md is the human-facing pitch; this file is the operational context.

## What this is

TrashAI is a civic-reporting companion for NYC. User uploads a photo of a street issue → app extracts location (EXIF GPS, or browser geolocation prompt, or geocoded address — all constrained to NYC) → classifies it with Claude Vision → pins it on a shared map as a circular photo marker → shows a hand-curated 311 reporting guide. **We never submit 311 reports — we only guide the user to the right form.** That's an intentional scope limit: no API integrations, no liability, no wrong reports filed on anyone's behalf.

Built for the **CUNY AI Innovation Challenge — Spring 2026**, Software track, "AI for Environmental Sustainability" theme. Two-day hackathon scope (Fri 2026-04-24 → Sat 2026-04-25).

## Live deployment

- **Production URL:** https://trashai-5appeqpxzalkzbg3jnjjmun.streamlit.app
- **Hosted on:** Streamlit Community Cloud, free tier.
- **Branch:** `main` auto-deploys on every push (~30-60s delay). **There is no staging env — `main` is production.**
- **Data persistence:** Files written to `data/` (pins.json, groups.json, images/) survive code redeploys — Streamlit Cloud preserves the working tree across pushes. They only get wiped by a manual reboot from the dashboard or by a code-level wipe (commit a one-shot `shutil.rmtree`, deploy, then revert). A push is not a reset.
- **Rollback:** `git revert <sha> && git push` — auto-redeploys to working state.
- **Reboot without push:** dashboard → "Manage app" → "Reboot" (useful when the container is weird but code is fine).

## Stack

- Python 3.9 locally (system macOS), Python 3.11 on Streamlit Cloud and in the Codespaces devcontainer.
- Streamlit web UI.
- Anthropic SDK + **Claude Sonnet 4.6** (`claude-sonnet-4-6`) for vision classification.
- Pillow for EXIF GPS and image resize before the API call.
- geopy/Nominatim for address geocoding, restricted to NYC.
- folium + streamlit-folium for the map; pins render as circular photo markers via `DivIcon`. Pan/zoom is constrained to NYC (see "Map bounds").
- streamlit-js-eval for the in-browser geolocation prompt (`navigator.geolocation`) when EXIF lacks GPS — see "Geolocation flow".
- JSON files + images directory for persistence (see "Storage model").
- Two product surfaces: **Upload** mode (photo → classify → pin) and **Groups** mode (lightweight cleanup-meetup directory). See "Groups feature".

## File map

| File | Role |
|---|---|
| [streamlit_app.py](streamlit_app.py) | UI entry point. Single render tree (`left, right = st.columns([7, 3])`) with media-queried CSS that swaps desktop side-by-side ↔ mobile stacked layout — see "Layout: one tree, two CSS regimes" below. Holds the upload + geolocation flow, Groups mode UI, the folium map build, the pin border-color map (`CATEGORY_COLORS`), and the `_thumbnail` helper. |
| [classify.py](classify.py) | Claude Vision call (`MODEL = "claude-sonnet-4-6"`) + image downscale (`_prepare_for_api`) + JSON parse with regex fallback + **stub fallback** when no API key (`is_stub_mode`, `_stub_classify`). |
| [prompt.py](prompt.py) | The single classification prompt string. Defines the 15 category IDs and the JSON response shape. |
| [routing.py](routing.py) | `GUIDE` dict — category ID → agency, 311 deep link (KA-XXXXX article URLs), service type, instructions. |
| [location.py](location.py) | EXIF GPS extraction (`get_location_from_exif`) + NYC-bounded Nominatim geocoding (`geocode_address`). |
| [storage.py](storage.py) | JSON-backed pin persistence: `load_pins`, `save_pin`, `load_image`. |
| [groups.py](groups.py) | JSON-backed group persistence: `load_groups`, `save_group`, `join_group`. |
| [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) | Codespaces / VS Code dev container config (Python 3.11 + Streamlit auto-run on port 8501). |
| `data/pins.json` | Runtime-written pin list. Gitignored. |
| `data/groups.json` | Runtime-written group list. **Not in `.gitignore`** — see "Storage model". |
| `data/images/` | Runtime-written user uploads. Gitignored except `.gitkeep`. |
| [.streamlit/secrets.toml](.streamlit/secrets.toml) | `ANTHROPIC_API_KEY`. Gitignored. |
| [docs/](docs/) | Design doc, prompt iteration notes, routing research, stack decision, groups brainstorm. Reference material — not loaded at runtime. |

## Critical conventions

### Category IDs are shared between three files
`prompt.py` tells Claude which category IDs to return. `routing.py` has a `GUIDE` dict keyed by those same IDs. `streamlit_app.py` has a `CATEGORY_COLORS` dict keyed by those same IDs (drives the pin's border color on the map). **If you add, rename, or remove a category, edit all three.** `routing.get_guide` and `CATEGORY_COLORS.get` both fall back to `"other"` / white for unknown IDs, so a mismatch fails soft but silently.

### "other" category does not save a pin
When `classify_image` returns `category: "other"`, [streamlit_app.py](streamlit_app.py) shows a yellow warning (`st.warning`) and **skips `save_pin` and the result card entirely** — `st.session_state.last_result` is also cleared so any stale prior card disappears. This keeps the map for genuine NYC civic issues, not random photos. Don't drop this guard if you refactor the classify flow.

### Layout: one tree, two CSS regimes
[streamlit_app.py](streamlit_app.py) builds a single render tree — `left, right = st.columns([7, 3], gap="large")` with the panel inside `right` and the folium map inside `left`. Two `@media` blocks then swap the visual layout:

- **Desktop (`min-width: 641px`)** — full-viewport layout, map left at 100vh, panel right scrollable; page chrome (header/toolbar/footer) hidden.
- **Mobile (`max-width: 900px`)** — `flex-direction: column-reverse` flips the columns so the panel sits on top (45vh, internally scrollable) and the map fills the bottom (55vh).

There is intentionally no DOM split or per-viewport widget cloning. Earlier doc revisions described a two-render-tree architecture (desktop-root / mobile-root containers, `_render_*` helpers, prefixed widget keys); none of that is in the code today, and you don't need to recreate it. Just remember the breakpoints overlap from 641-900px (desktop CSS *and* mobile CSS both apply on mid-size viewports — mobile wins where they conflict because it's later in the stylesheet).

When adding UI, write it once inside `with right:` (or `with left:`) and let the media queries handle layout. If you tweak the column ratio, update the panel's mobile `45vh` height accordingly so the map still fills the screen.

### Geolocation flow
When `get_location_from_exif` returns `None`, the panel shows a **📍 Use my current location** button. Clicking it sets `st.session_state.geo_requested = True`; on the rerun, [streamlit_app.py](streamlit_app.py) calls `streamlit_js_eval.get_geolocation()`, which injects a tiny iframe that calls `navigator.geolocation.getCurrentPosition` — that's what triggers the browser's native location-permission dialog. If the call returns coords, they're used directly; otherwise the address text input is shown as a fallback. The `geo_requested` flag persists in session state across uploads (re-clicks reuse the cached browser permission).

Two requirements that bite if you forget them:
- `navigator.geolocation` only fires on **HTTPS or `localhost`**. Streamlit Cloud is HTTPS so prod is fine. Local dev on `localhost:8501` is fine. Accessing the dev server via a LAN IP silently no-ops.
- The browser remembers a previous "Block" decision per origin. If a user denied location once, the prompt won't re-appear — they have to clear the site's location permission in their browser settings. That's a browser limitation, not a bug.

### Map bounds
The folium `Map` is constructed with `min_zoom=10` and the maxBounds option set to a buffered NYC bbox `[[40.40, -74.40], [41.00, -73.55]]` with `maxBoundsViscosity = 1.0`. Together this means:
- The user cannot zoom out past the all-five-boroughs view.
- Panning past the bbox snaps back immediately (viscosity 1.0 = solid wall).

The bbox is intentionally a few tenths of a degree wider than the geocoder's NYC viewbox in [location.py](location.py) (`(40.477, -74.260) → (40.920, -73.700)`) — the map needs slack at the edges so users near the city limits aren't fighting the snap-back. If you change either bbox, keep the map's wider than the geocoder's.

### Python 3.9 compatibility
Local dev is on macOS system Python 3.9. **`X | Y` union syntax (PEP 604) is 3.10+** — do not use it; use `Optional[X]` / `Union[X, Y]` from `typing`. PEP 585 generic builtins (`list[X]`, `dict[X, Y]`, `tuple[X, ...]`) DO work on 3.9 at runtime and are already used in [storage.py](storage.py) and [routing.py](routing.py); they're fine. Streamlit Cloud runs 3.11 and so does the devcontainer, so the only real constraint is "no `X | Y` union syntax."

### Stub classifier mode
[classify.py](classify.py) detects a placeholder `ANTHROPIC_API_KEY` (`""`, `"REPLACE_ME_WITH_YOUR_KEY"`, `"sk-ant-..."`) via `is_stub_mode()` and routes through `_stub_classify` instead of calling Anthropic. The stub hashes the image bytes and picks a deterministic category from a fixed list of 8. A small `st.caption` ("⚙️ Stub mode — add API key…") appears under the title whenever stub mode is active. Real Claude is re-enabled just by pasting a valid key — no code changes.

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

### Groups feature
Second product surface alongside Upload. Toggled by a `st.radio` in the right panel; the active mode lives in `st.session_state.groups_mode`. There's no auth — visitors pick a `display_name` once per session (kept in `st.session_state.display_name`, never persisted) and can then create or join groups. Group records are written to `data/groups.json` by [groups.py](groups.py).

Group schema (`data/groups.json` is a flat list):
```json
{
  "id": "<uuid hex, 8 chars>",
  "title": "Prospect Park Cleanup",
  "neighborhood": "Park Slope, Brooklyn",
  "meetup_location": "Main entrance, 9th St & Prospect Park W",
  "meetup_time": "Saturday Apr 26 at 10am",
  "creator": "<display_name>",
  "members": ["<display_name>", ...]
}
```

Notes:
- `meetup_time` is a free-text string, not a parsed datetime. Intentional — keeps the UI dumb and lets users write "tomorrow afternoon" or whatever they want.
- `members` always starts as `[creator]`. `join_group` is idempotent — joining twice is a no-op.
- The creator field is just whatever the visitor typed for display name. There is no identity verification. Don't add one — it breaks "no auth" scope.
- `data/groups.json` is **not** in `.gitignore` (unlike `data/pins.json`). If you `git add .` while groups exist, you'll commit them. Either add it to `.gitignore` next time you're touching that file, or be deliberate about staging.

### HTML escape AI output in popups
Popup HTML in [streamlit_app.py](streamlit_app.py) renders `display_name`, `reasoning`, `notable_details`, and `confidence` inside a Folium `<div>`. All four go through `html.escape()` before interpolation because they originate from a model response. Do not skip this if you add more AI-sourced fields to the popup.

### Storage model
- `data/pins.json` is a flat list. `save_pin` appends + rewrites the whole file (fine at N<1000).
- `load_pins` runs on every Streamlit rerun. No caching yet — if pins grow large, add `@st.cache_data` keyed on the file mtime.
- On Streamlit Cloud, the container filesystem is **shared across all visitors**. Files written to `data/` persist across code pushes/redeploys — only a manual reboot from the dashboard, or a code-level wipe (one-shot `shutil.rmtree` deployed then reverted), clears them. Long idle eventually recycles the container too.
- Do not commit `data/pins.json` or user images. `.gitignore` already handles this.

### Secrets
Local: `.streamlit/secrets.toml` (gitignored). Template at `.streamlit/secrets.toml.example`.
Cloud: paste the same TOML into the Streamlit Cloud app's "Secrets" UI (Manage app → ⋮ → Settings → Secrets). Changes there trigger a restart, not a redeploy.
Never commit a real key. Never print it to logs or UI. Never include it in an error message.

### Session state vs persistence
Per-visitor (in `st.session_state`, never written to disk):
- `last_result` — their most recent classification result + matching guide.
- `groups_mode` — Upload vs Groups tab.
- `display_name` — chosen once per session for Groups; cleared when the tab is closed.
- `create_group_open` — keeps the "Create a group" expander open after a successful save.
- `geo_requested` — set by the "Use my current location" button to trigger `get_geolocation()` on the next rerun.

Shared across visitors (on disk under `data/`):
- Pins (`pins.json` + `images/`).
- Groups (`groups.json`).

Do not put pins or groups back into `session_state` — that regresses the shared/crowd-sourced claim.

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
| Disk | ~50 GB | Persists across code pushes. Wiped only by manual reboot or long idle. |
| Concurrent users | 1 container, 1 Streamlit worker | Queued under load. Fine for a hackathon demo. |
| GPU | None | Irrelevant — vision runs via API. |
| Cold start | ~20-30s | Warm the URL 5 min before a demo. |

## Demo-day rules

- **Avoid pushing to `main` within ~5 minutes of a demo** — the redeploy briefly takes the site offline. Pins, images, and groups survive the redeploy, so the map state is safe.
- **Warm the site with one page load** 5 min before the demo to avoid a cold-start during the pitch.
- **Seed pins manually** on the live site right before judging so the map isn't empty. Pins survive code redeploys; a manual reboot or ~7-day idle is what wipes them.

## Known limitations (intentional, not bugs)

- No auth, rate limits, or spam protection on pin creation.
- Nominatim geocoding has a ~1 req/s free-tier cap; fine for a hackathon.
- On-disk images are stored at original upload size. A 10 MB upload takes 10 MB of container disk. (Only the API-bound copy is resized.)
- Folium rerenders the whole map on every Streamlit rerun. OK under ~100 pins.
- No moderation: any uploaded image appears in any visitor's map popup.
- "Persistence across visitors" lasts until a manual dashboard reboot or long idle (~7 days). Code redeploys leave the data intact.

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
