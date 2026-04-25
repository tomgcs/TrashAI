# Groups feature — brainstorm

A "group" system for users to create a neighborhood-scoped cleanup group, join one (cap 20), and schedule a time to go out and pick up trash together.

Constraints from the existing codebase: no auth, ephemeral JSON storage, two render trees (desktop + mobile), 2-day hackathon scope.

## Data model — new file `groups.py` + `data/groups.json`

```json
{
  "id": "uuid",
  "name": "East Village Cleanup",
  "neighborhood": "East Village",
  "scheduled_at": "2026-04-26T10:00",
  "meet_lat": 40.72, "meet_lng": -73.98,
  "max_members": 20,
  "members": ["Tom", "Alex"],
  "created_at": "2026-04-24T14:30"
}
```

Helpers mirroring [storage.py](../storage.py): `load_groups()`, `save_group()`, `join_group(id, name)`, `leave_group(id, name)`.

## Identity (the hard part, given no auth)

Simplest: ask once for a display name, stash in `st.session_state.display_name`. That's your "who joined" key.

**Tradeoff:** page refresh = identity lost, anyone can impersonate anyone. Acceptable for a demo, broken for real coordination — call this out in the pitch as future work.

## UI — silhouette button + slide-in panel

- **Button:** floating circular div, top-right of map (away from upload panel which sits left/top). CSS background-image of the silhouette, ~40% opacity, hover → 80%. Implemented as a CSS-styled `st.button` inside both `desktop-root` and `mobile-root` containers, with `key_prefix` like the upload panel does.
- **Panel:** when toggled (`st.session_state.group_panel_open`), reveal a right-side drawer (desktop) or bottom sheet (mobile) — same trick as the upload panel's `12vh → 50vh` grow. Don't overlap the map controls.

Three tabs inside the panel:

1. **Browse** — list of groups: name • neighborhood • 🕒 scheduled time • 👥 N/20 • [Join]. Disabled when full.
2. **Create** — form: name, neighborhood (text), date+time picker, optional pin-on-map for meet point, [Create].
3. **Mine** — groups you've joined, with [Leave] and a clearly displayed countdown to the meetup.

## Map integration (optional, do last)

Add a *second* marker style — the silhouette icon — for each group's `meet_lat/lng`. Distinct from trash pins so they don't compete visually. Click → opens that group in the panel.

## Files to touch

| File | Change |
|---|---|
| `groups.py` (new) | Storage helpers, ~50 lines, mirrors `storage.py`. |
| `streamlit_app.py` | `_render_group_button(key_prefix)`, `_render_group_panel(key_prefix)`, wire into both trees. CSS for the floating button scoped under each `.st-key-*-root`. |
| `.gitignore` | Add `data/groups.json` (same as pins). |

## Scope flags before building

- **Ephemeral:** every push to `main` wipes groups. A cleanup scheduled for Saturday created Friday survives — but only until next deploy. Same constraint as pins; just be aware.
- **Mobile pixel-tightness:** the panel growth pattern is already load-bearing; adding a third growth state ("group panel open") needs a new CSS rule, not a refactor of the existing one.
- **Cap of 20:** trivial to enforce server-side in `join_group`.
- **Time estimate:** ~20 minutes to v1 if you skip the map markers. ~45 with markers.
