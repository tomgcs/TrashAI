# Claude Vision Prompt

The prompt we send to Claude Vision along with the user's uploaded image. This is the classification core of the product — iterate aggressively against `sample-images/`.

**Model:** `claude-sonnet-4-6`
**Input:** one image + the prompt below
**Output:** JSON matching the contract below

## Expected output contract

The model must return valid JSON matching this shape:

```json
{
  "category": "one of the 15 category IDs below",
  "confidence": "low | medium | high",
  "reasoning": "one short sentence explaining the choice",
  "notable_details": "anything the user should include in their 311 report"
}
```

The frontend uses `category` to look up the guide card from `docs/routing.md` (eventually `routing.py`/`routing.json`). `notable_details` gets surfaced to the user as suggested text to include when they file.

## Category IDs (must match `routing.md` exactly)

```
curbside_trash
bulk_item
illegal_dumping
overflowing_basket
park_trash
dog_waste
dead_animal
broken_sidewalk
pothole
damaged_sign
broken_streetlight
graffiti
tree_damage
abandoned_vehicle
other
```

## v1 draft prompt

```
You are a civic issue classifier for a NYC reporting companion app called TrashAI.
You will be shown a photo taken by a NYC resident of something that may need to be
reported to the city. Your job is to classify what is in the photo so the app can
show the user the correct 311 reporting path.

Respond with a single category ID from this list:

- curbside_trash: household trash bags at the curb
- bulk_item: mattresses, furniture, or large appliances on the sidewalk
- illegal_dumping: construction debris, tires, commercial waste, or large mixed dumps
- overflowing_basket: public corner litter baskets overflowing onto the sidewalk
- park_trash: litter or trash inside a NYC park (grass, benches, or park paths visible)
- dog_waste: dog feces on a sidewalk, stoop, or other public space
- dead_animal: a dead animal in public space
- broken_sidewalk: cracked, raised, or broken sidewalk concrete
- pothole: a pothole or significant defect in a street surface
- damaged_sign: a fallen, bent, knocked-over, or missing traffic/street sign
- broken_streetlight: a streetlight that is out, damaged, or hanging
- graffiti: graffiti or unauthorized tagging on any surface
- tree_damage: a fallen branch, split tree, or clearly dead/dying tree
- abandoned_vehicle: a vehicle that appears abandoned (no plates, flat tires, heavy damage, clearly unmoved)
- other: none of the above, or the image is unclear

Respond ONLY with valid JSON in this exact shape:

{
  "category": "<one of the above IDs>",
  "confidence": "low | medium | high",
  "reasoning": "<one short sentence>",
  "notable_details": "<details the reporter should mention, e.g. 'Construction debris and ~6 tires piled against a hydrant'>"
}

Do not include any other text before or after the JSON.

If the image does not clearly show a civic issue, return category: "other" with
confidence: "low".
```

## Iteration log

- **v1** — first draft, untested. TODO: run against `sample-images/` and track failure modes here.

## Things to try if v1 underperforms

- **Add few-shot examples** — show 2–3 labeled images in the prompt. Biggest single quality lever.
- **Split into two calls** — "is this a reportable civic issue? yes/no" then "which category?" Slower but often more accurate on edge cases.
- **Force structured output** — switch from "return JSON" to Anthropic's tool-use API, which guarantees schema-valid output. ~15 min swap.
- **Lower temperature** — if the SDK exposes it, set `temperature: 0` for more consistent JSON.
- **Ambiguity rule** — add "If you see multiple issues, pick the most prominent or most dangerous one" to reduce confusion on mixed scenes.
- **Reject prompt** — add "If the photo shows a person as the subject, return category: other with confidence: low and a note about privacy."

## Known failure modes to watch for

- **Trash vs. illegal dumping** — a single bag at the curb is `curbside_trash`; a large pile of mixed waste or construction debris is `illegal_dumping`. Phrase this clearly.
- **Sidewalk vs. pothole** — both are concrete damage; sidewalk = pedestrian surface, pothole = street surface.
- **Park vs. street trash** — if the photo shows clearly park-like context (grass, trees, park bench), prefer `park_trash` over `curbside_trash`.
- **Dog waste vs. dead animal** — small, dark, on the ground. Could look similar. Add disambiguation in the prompt or examples.
- **Graffiti on abandoned vehicle** — if a vehicle is both abandoned and tagged, prefer `abandoned_vehicle` (that's the actionable issue).
