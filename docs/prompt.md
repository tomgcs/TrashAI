# Claude Vision Prompt

The prompt we send to Claude Vision along with the user's uploaded image. This is the core of the product — iterate aggressively against `sample-images/`.

## Expected output contract

The model must return valid JSON matching this shape:

```json
{
  "category": "one of: curbside_bag | bulk_item | illegal_dumping | overflowing_basket | park_trash | e_waste | hazardous | dead_animal | abandoned_vehicle | unknown",
  "confidence": "low | medium | high",
  "reasoning": "one short sentence explaining why",
  "notable_details": "anything relevant to the 311 description (e.g., 'appears to be construction debris and tires')"
}
```

The frontend uses `category` to look up the agency from `docs/routing.md` and composes the final report card.

## v1 draft prompt

```
You are a trash classification assistant for a NYC 311 reporting app. You will be
shown a photo uploaded by a NYC resident who wants to report trash. Your job is to
classify the trash into one of the following categories so the app can route the
report to the correct city agency.

Categories:
- curbside_bag: household trash bags left at the curb
- bulk_item: furniture, mattresses, large appliances on the sidewalk
- illegal_dumping: construction debris, tires, commercial waste, large dumps of mixed waste
- overflowing_basket: public corner litter baskets that are overflowing
- park_trash: litter or trash inside a NYC park (grass, benches, park paths visible)
- e_waste: televisions, monitors, computers, printers, other electronics
- hazardous: paint cans, chemical containers, batteries, motor oil
- dead_animal: dead animals on the street
- abandoned_vehicle: cars that appear abandoned (no plates, flat tires, heavily damaged)
- unknown: none of the above, or the image does not clearly show trash

Respond ONLY with valid JSON in this exact shape:

{
  "category": "<one of the above>",
  "confidence": "low | medium | high",
  "reasoning": "<one short sentence>",
  "notable_details": "<any details relevant to a 311 report description>"
}

Do not include any other text before or after the JSON.
```

## Iteration log

- **v1** — first draft, untested. TODO: run against `sample-images/` and track failure modes here.

## Things to try if v1 underperforms

- Add few-shot examples (show 2–3 labeled images in the prompt)
- Split into two calls: "is this trash? yes/no" then "which category?" — slower but often more accurate
- Lower the temperature (if the SDK exposes it) for more consistent JSON
- Add "If you see multiple types, pick the most prominent one" to reduce confusion on mixed piles
