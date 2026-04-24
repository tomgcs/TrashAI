# TrashAI

A civic reporting companion for NYC. Snap a photo of anything that needs action — trash, dog waste, cracked sidewalk, fallen sign, pothole, dead animal, graffiti, and more. TrashAI (1) pins your photo on a map of the city and (2) tells you exactly where and how to report it.

**We do not submit any reports ourselves.** TrashAI is a guide, not a submitter. That's a feature: no API dependencies, no liability, no wrong reports in your name, and the app scales to any civic issue without new integrations.

**Event:** CUNY AI Innovation Challenge — Spring 2026
**Track:** AI Software (Agentic AI)
**Theme:** AI for Environmental Sustainability

## Problem

NYC residents — especially students new to the city — routinely see problems that should be reported but give up because 311 is opaque: different issues go to different agencies, each with its own complaint category, form, and routing rules. Most people don't bother. The result is slower fixes, more broken windows, and a bigger burden on neighborhoods already dealing with the worst conditions.

## Solution (demo scope)

1. User uploads a photo.
2. The app extracts GPS from the photo's EXIF metadata if present; otherwise asks for an address.
3. Claude Vision classifies what's in the photo into one of ~15 civic issue categories.
4. The photo is pinned on an NYC map at its location.
5. The app shows a guide card: **which agency handles this**, **where to file**, **what to select** (the correct 311 complaint type), and **what to say**.
6. User files the report themselves via the real 311 — TrashAI just shows them how.

No database, no user accounts, no backend — demo runs entirely in session state.

## Stack

- **Python 3.11**
- **Streamlit** — web app framework
- **Anthropic SDK** with **Claude Sonnet 4.6** — vision classification
- **Pillow** — image and EXIF reading
- **folium** + **streamlit-folium** — NYC map with photo-annotated pins
- **geopy** (Nominatim) — address → lat/long geocoding (fallback when no EXIF)
- **Streamlit Community Cloud** — free deploy, public URL

## Team

- _Name — CUNY campus — role_
- _Name — CUNY campus — role_
- _Name — CUNY campus — role_
- _Name — CUNY campus — role_

## Repository

```
TrashAI/
├── streamlit_app.py         # main app entry (not yet scaffolded)
├── routing.py               # issue category → NYC agency guide (not yet scaffolded)
├── prompt.py                # Claude Vision prompt (not yet scaffolded)
├── requirements.txt         # Python deps (not yet scaffolded)
├── .streamlit/
│   └── secrets.toml         # LOCAL ONLY — gitignored
├── docs/
│   ├── design-doc.md        # link to Google Doc + signoff tracker
│   ├── routing.md           # guide content: category → agency, channel, link, instructions
│   ├── prompt.md            # Claude Vision prompt + JSON output contract
│   └── stack-decision.md    # final stack + reasoning
├── sample-images/           # test photos for prompt iteration
├── LICENSE
└── .gitignore
```

## Hackathon checklist

- [ ] Repo set to public
- [ ] `aiinnovationhub2026` added as collaborator
- [ ] Design doc edit access granted to `cuny-ai-innovation-challenge-organizers@googlegroups.com`
- [ ] Day 1 deliverables signed off by track lead (before 7pm Fri 2026-04-24)
- [ ] Day 2 deliverables signed off and uploaded to BeMyApp (before 5pm Sat 2026-04-25)

## License

MIT — see [LICENSE](LICENSE).
