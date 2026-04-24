# Stack Decision

**Status:** ✅ Decided 2026-04-24.

## Final stack

| Layer | Choice | Purpose |
|---|---|---|
| Language | Python 3.11 | What everyone writes in |
| Framework | Streamlit | Turns the Python script into a web app |
| AI | Anthropic SDK + Claude Sonnet 4.6 | Vision classification of uploaded photos |
| Image handling | Pillow | Read images, extract EXIF |
| Map | folium + streamlit-folium | NYC map with pin-per-photo |
| Geocoding | geopy (Nominatim / OpenStreetMap) | Address text → lat/long when EXIF is missing |
| Hosting | Streamlit Community Cloud | Free public URL, auto-deploys from GitHub main |

`requirements.txt` (to be created when code is scaffolded):

```
streamlit>=1.40
anthropic>=0.45
Pillow>=11.0
folium>=0.17
streamlit-folium>=0.22
geopy>=2.4
```

Six dependencies. One language. One deploy target.

## Location strategy (EXIF-first)

For each uploaded photo:

1. **Try EXIF GPS tags first.** Pillow exposes EXIF; the `GPSInfo` tag contains lat/long when the phone captured it. Most iPhone and Android photos taken in the Camera app include this.
2. **If EXIF is missing or the photo was shared through a service that strips it** (AirDrop preserves; most messaging apps and social media strip), show a text input: *"Where did you see this? (e.g., 199 Chambers St, New York, NY)"*.
3. **Geocode the user-typed address** via Nominatim (`geopy`). No API key required. 1 req/sec limit and a User-Agent header requirement — both fine for demo scale.
4. **Map pin placement** uses whichever lat/long was resolved.

The "magic moment" of the demo is EXIF-first: drag a photo in, see it auto-pin on the NYC map without typing anything. The fallback keeps it robust on images that have been shared.

## Why Streamlit (for the record / for the pitch)

Options considered: Next.js (TypeScript), Streamlit (Python), Gradio (Python), Python-backend + Next.js-frontend hybrid.

Streamlit won because:

- **Team skill fit.** Python-only stack lets all four teammates contribute to any file.
- **Speed.** ~30 lines of Python gets a working upload + classify + display. Every hour not spent on framework is an hour on prompt quality, guide content, or the video pitch — where the points are.
- **No stack split.** No frontend/backend coordination, no CORS, no two deploys to fail.
- **Map integration.** `streamlit-folium` is plug-and-play; folium handles image-in-popup natively.
- **Demo reliability.** Streamlit Community Cloud + video recorded on localhost = minimal surface area for things to break on Saturday.

## Tradeoffs we accepted

- **Aesthetic.** Streamlit has a recognizable look. Judging weights (30% impact, 20% technical, 20% AI, 15% code quality, 10% creativity, 5% presentation) don't explicitly reward polish, and the video is what they watch.
- **Scale ceiling.** If TrashAI continues past the hackathon, the Streamlit app gets rewritten once it needs accounts, persistence across sessions, or a real backend. That's a Week 4+ problem, not a Day 2 one.
- **Cold starts on Community Cloud.** Apps sleep after ~7 days of no traffic; first hit after sleep takes ~30s. Mitigation: visit the URL to warm it up before judging.

## Options we rejected

### Next.js (TypeScript)
Considered. Would produce a more polished demo. Rejected because no team member has enough React experience to be productive in 2 days, and the learning cost would come out of prompt-quality and guide-content time.

### Gradio
Simpler than Streamlit for a single input → single output demo. Rejected because our UI needs an image, an address input, a map, and a guide card all on screen — Streamlit's layout primitives are more flexible.

### Python backend + Next.js frontend
Industry-standard pattern. Rejected because we use no Python-specific ML libraries (the entire AI call is one HTTP request to Claude that can be made equally from either language), so the split adds all the integration cost with none of the benefits.
