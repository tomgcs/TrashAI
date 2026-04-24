# TrashAI

AI-powered trash reporting for NYC. Users upload a photo of trash; TrashAI classifies the type and generates a pre-filled 311 report routed to the correct NYC agency (DSNY, Parks, DEP, etc).

**Event:** CUNY AI Innovation Challenge — Spring 2026
**Track:** AI Software (Agentic AI)
**Theme:** AI for Environmental Sustainability

## Problem

NYC residents routinely see trash that should be reported to the city, but 311 is a maze: different trash types go to different agencies, each with its own complaint category and form. Most people give up and don't report. The result is slower cleanup, more illegal dumping, and a heavier burden on the neighborhoods already dealing with the worst conditions.

## Solution (MVP / demo scope)

1. User uploads a photo of trash.
2. Claude Vision classifies the trash into one of our defined categories.
3. App displays a pre-filled 311 report: the correct NYC agency, the matching 311 complaint type, and a suggested description.
4. User reviews/confirms before filing (they file through the real 311 themselves).

**Demo scope:** No live 311 API submission. No persistence. No authentication. Focus is on classification accuracy and correct agency routing.

## Team

- _Name — CUNY campus — role_
- _Name — CUNY campus — role_
- _Name — CUNY campus — role_
- _Name — CUNY campus — role_

## Stack

**TBD** — to be finalized Day 2 morning. See [docs/stack-decision.md](docs/stack-decision.md) for the options under consideration.

## Repository

```
TrashAI/
├── docs/
│   ├── design-doc.md      # link to Product Design Doc
│   ├── routing.md         # trash category → NYC agency mapping
│   ├── prompt.md          # Claude Vision prompt iterations
│   └── stack-decision.md  # stack options + decision
├── sample-images/         # test photos for prompt iteration
└── .env.example           # environment variable template
```

## Hackathon checklist

- [ ] Repo set to public
- [ ] `aiinnovationhub2026` added as collaborator
- [ ] Design doc edit access granted to `cuny-ai-innovation-challenge-organizers@googlegroups.com`
- [ ] Day 1 deliverables signed off by track lead (before 7pm)
- [ ] Day 2 deliverables signed off and uploaded to BeMyApp (before 5pm)

## License

MIT — see [LICENSE](LICENSE).
