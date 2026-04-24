# Trash Category → NYC Agency Routing

Maps each trash category the vision model can output to the correct NYC agency, 311 complaint type, and suggested report description.

Sources to validate against:
- [NYC 311 Service Requests (Open Data)](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9)
- [NYC 311 Reference (nyc.gov/311)](https://portal.311.nyc.gov/)

**Status:** first-pass draft — needs verification against actual 311 complaint types before demo.

## Categories (v1)

| # | Category | Example | Agency | 311 Complaint Type | Description template |
|---|---|---|---|---|---|
| 1 | Household curbside bag | Black trash bag at the curb past pickup | DSNY | Missed Collection | "Household trash bag left uncollected at [address]. Photo attached." |
| 2 | Bulk item | Mattress, couch, furniture | DSNY | Bulk Item Pickup / Derelict Item | "Bulk item (mattress/furniture) on sidewalk at [address]. Needs pickup." |
| 3 | Illegal dumping | Construction debris, tires, commercial waste on sidewalk/lot | DSNY | Illegal Dumping | "Illegal dumping observed at [address]. Appears to be [debris type]." |
| 4 | Overflowing litter basket | Public trash can overflowing onto sidewalk | DSNY | Overflowing Litter Basket | "Corner litter basket at [address] is overflowing." |
| 5 | Trash in a park | Litter, overflowing bins inside a NYC park | NYC Parks | Park Maintenance - Trash | "Trash/litter in [park name]. Location: [description]." |
| 6 | E-waste | TVs, monitors, computers, printers | DSNY SAFE Disposal | Electronics Recycling | "Electronics (e-waste) at [address]. DSNY will not collect with regular trash." |
| 7 | Hazardous waste | Paint cans, chemicals, batteries, motor oil | DSNY SAFE / DEP | Hazardous Waste | "Hazardous material at [address]: [type]. Needs SAFE Disposal event." |
| 8 | Dead animal | Dead rat/pigeon/other on street | DOHMH | Dead Animal | "Dead animal at [address]. Needs removal." |
| 9 | Abandoned vehicle | Car with no plates / expired registration / clearly abandoned | NYPD | Abandoned Vehicle | "Abandoned vehicle at [address]. [Description of vehicle]." |

## Open questions

- Should we collapse 6 + 7 into a single "Special Disposal" category to keep the model's decision easier?
- How do we handle "uncertain" — low-confidence classifications? Proposal: if confidence < threshold, return `category: unknown` and route to DSNY general 311 with a note.
- Do we need a "not trash / false upload" category for robustness?

## Out of MVP scope

- Automatic address detection (user types or confirms address manually)
- Severity/priority scoring
- Duplicate-report detection
