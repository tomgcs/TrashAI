# Civic Issue Guide Content

For each classifiable category, this table tells the user **what agency handles it**, **where to file**, **what to select**, and **what to say**. This is the core IP of the app — the AI classifies, but the guide is what genuinely helps a NYC resident.

**Status:** first-pass draft. Every link, service-type name, and instruction **must be verified** against [portal.311.nyc.gov](https://portal.311.nyc.gov/) before demo. This is Person C's primary deliverable for the weekend.

## Sources to verify against

- [NYC 311 Portal](https://portal.311.nyc.gov/) — canonical list of all service request types
- [NYC 311 Open Data — Service Requests](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9) — real complaint types with frequencies
- [NYC Parks Report a Problem](https://www.nycgovparks.org/reservations/report) — for park-specific issues
- [Graffiti-Free NYC](https://www.nyc.gov/site/graffitifree/index.page) — graffiti cleanup program

## Output shape per category

Each category maps to a JSON record like:

```json
{
  "display_name": "Pothole",
  "agency": "NYC DOT",
  "channel": "311 (online, phone, or NYC 311 app)",
  "link": "https://portal.311.nyc.gov/...",
  "service_type": "Street Condition - Pothole",
  "instructions": "File 'Pothole' via 311. Provide the street address and note which lane or direction."
}
```

The UI renders the fields into a "how to report" card.

## Category guide (v1 drafts — verify before demo)

### 1. `curbside_trash` — Curbside trash bag
- **Agency:** DSNY (Sanitation)
- **Channel:** 311 online / 311 phone / NYC 311 app
- **Service type:** Missed Collection
- **Link:** portal.311.nyc.gov → search "Missed Collection"
- **Instructions:** "File a **Missed Collection** report with DSNY. You'll need the address and your regular collection day."

### 2. `bulk_item` — Bulk item (mattress, furniture, appliance)
- **Agency:** DSNY
- **Channel:** 311
- **Service type:** Request for Bulk Item Pickup / Derelict Item
- **Link:** portal.311.nyc.gov → "Bulk Item Pickup"
- **Instructions:** "If it's **your** item: schedule a bulk pickup with DSNY via 311 and leave it curbside on your collection day. If it's **not yours** (someone dumped it), file as **Illegal Dumping** instead."

### 3. `illegal_dumping` — Illegal dumping
- **Agency:** DSNY Enforcement
- **Channel:** 311
- **Service type:** Illegal Dumping
- **Link:** portal.311.nyc.gov → "Illegal Dumping"
- **Instructions:** "File an **Illegal Dumping** report with DSNY. Your photo helps — save it. Include address, time of day, and any details about who or what dumped it."

### 4. `overflowing_basket` — Overflowing litter basket
- **Agency:** DSNY
- **Channel:** 311
- **Service type:** Overflowing Litter Basket
- **Link:** portal.311.nyc.gov → "Overflowing Litter Basket"
- **Instructions:** "File **Overflowing Litter Basket** via 311. Include cross streets or the nearest address."

### 5. `park_trash` — Trash in a park
- **Agency:** NYC Parks
- **Channel:** 311 or NYC Parks direct
- **Service type:** Park Maintenance - Trash
- **Link:** [nycgovparks.org/reservations/report](https://www.nycgovparks.org/reservations/report) or 311
- **Instructions:** "Report **Park Maintenance** via 311 or directly on the NYC Parks site. Include the park name and a landmark (entrance, playground, specific path)."

### 6. `dog_waste` — Dog waste on sidewalk or public space
- **Agency:** DSNY (enforces the pooper-scooper law) / DOHMH
- **Channel:** 311
- **Service type:** Dog Waste
- **Link:** portal.311.nyc.gov → "Dog Waste"
- **Instructions:** "File **Dog Waste** via 311. Enforcement of a specific violation usually requires witnessing the owner, but recurring issues at a location can still be reported and routed to enforcement."

### 7. `dead_animal` — Dead animal
- **Agency:** DOHMH for small animals (rat, pigeon, squirrel); NYPD for larger; NYC Parks if in a park
- **Channel:** 311
- **Service type:** Dead Animal
- **Link:** portal.311.nyc.gov → "Dead Animal"
- **Instructions:** "File **Dead Animal** via 311 for removal. For a pet with a tag, call 311 directly so they can route to the right agency."

### 8. `broken_sidewalk` — Cracked or broken sidewalk
- **Agency:** NYC DOT
- **Channel:** 311
- **Service type:** Sidewalk Condition
- **Link:** portal.311.nyc.gov → "Sidewalk Condition"
- **Instructions:** "File **Sidewalk Condition** with DOT via 311. Note: in NYC the **property owner** usually repairs sidewalks, but DOT can inspect and notify the owner, especially for tripping hazards."

### 9. `pothole` — Pothole
- **Agency:** NYC DOT
- **Channel:** 311
- **Service type:** Street Condition - Pothole
- **Link:** portal.311.nyc.gov → "Pothole"
- **Instructions:** "File **Pothole** via 311. Provide the street address and note which lane or direction of travel."

### 10. `damaged_sign` — Fallen or damaged traffic sign
- **Agency:** NYC DOT
- **Channel:** 311
- **Service type:** Street Sign - Damaged / Street Sign - Missing
- **Link:** portal.311.nyc.gov → "Street Sign Condition"
- **Instructions:** "File **Street Sign Condition** via 311. Include the intersection and which direction the sign was facing."

### 11. `broken_streetlight` — Broken or out streetlight
- **Agency:** NYC DOT (Street Lighting)
- **Channel:** 311
- **Service type:** Street Light Condition
- **Link:** portal.311.nyc.gov → "Street Light Condition"
- **Instructions:** "File **Street Light Condition** via 311. If the pole has a visible ID number, include it — speeds up the fix."

### 12. `graffiti` — Graffiti
- **Agency:** Graffiti-Free NYC (free cleanup for private property) / NYPD (if connected to a crime)
- **Channel:** 311
- **Service type:** Graffiti
- **Link:** portal.311.nyc.gov → "Graffiti" or [nyc.gov/site/graffitifree](https://www.nyc.gov/site/graffitifree/index.page)
- **Instructions:** "File **Graffiti** via 311. If you own the property, you can also apply for free cleanup through Graffiti-Free NYC."

### 13. `tree_damage` — Damaged tree, fallen branch, dead tree
- **Agency:** NYC Parks (Forestry)
- **Channel:** 311 or NYC Parks
- **Service type:** Damaged Tree / Dead Tree
- **Link:** portal.311.nyc.gov → "Damaged Tree"
- **Instructions:** "File **Damaged Tree** via 311 or directly with NYC Parks Forestry. **For life-safety hazards** (tree on power lines, blocking a street, on top of a vehicle), call **911**, not 311."

### 14. `abandoned_vehicle` — Abandoned vehicle
- **Agency:** NYPD (311 routes it)
- **Channel:** 311
- **Service type:** Derelict Vehicle
- **Link:** portal.311.nyc.gov → "Derelict Vehicle"
- **Instructions:** "File **Derelict Vehicle** via 311. Include make, model, color, license plate (if any), and how long it's been there."

### 15. `other` — Unknown / other
- **Agency:** General 311
- **Channel:** [portal.311.nyc.gov](https://portal.311.nyc.gov/) or call 311
- **Service type:** N/A — describe the issue
- **Instructions:** "Use the **311 online portal** or **call 311** — describe the issue and they'll route. If you're not sure where it fits, this is the safest option."

## Handling ambiguous or low-confidence classifications

When the model returns `"confidence": "low"` or `"category": "other"`:
- Still render the map pin (user knows where they saw the issue).
- Instead of a specific agency card, show the **general 311 card** (category 15).
- Add a short note: "We weren't fully sure what this was. Here's how to file a general 311 report."

## Out of MVP scope

- Emergency routing — we show "call 911" text in tree-damage instructions, but we do not build automated emergency detection
- Multi-language instructions (NYC has this via 311 itself — point users there)
- Severity/priority scoring
- Duplicate-report detection across users
