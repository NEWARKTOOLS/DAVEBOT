# DAVEBOT

DAVEBOT is a toolmaking and moulding work management system (WMS) concept modeled on "Dad Dave" — the seasoned toolmaker who *knows everything* (or at least thinks he does). The goal is to track jobs end-to-end, help quote tooling and moulding work, and provide a knowledge-first assistant that answers toolmaking and plastic moulding questions.

## What this repo contains

This repository currently provides a product blueprint and a runnable API prototype. It captures:

- A WMS domain model for toolmaking jobs (new tools, diecast tools, repairs/mods, one-offs)
- A quote lifecycle that generates customer documentation with company branding
- Quoting calculators for tooling and moulding
- Inventory for ancillaries, plates, and general materials
- End-to-end job tracking from enquiry/quote through manufacture and sampling
- A DAVEBOT assistant that can answer and calculate common toolmaking questions

Start with the docs in the `docs/` folder.

## Run the API prototype

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open `http://localhost:8000/docs` for the interactive API.

## Next steps (implementation sketch)

1. Build a web UI (dashboard + quoting + WMS tracking).
2. Implement persistence (database) and authentication.
3. Add document templating for branded quotes and job packs.
4. Add a DAVEBOT assistant layer with domain formulas and FAQs.

## Documentation index

- [Product requirements](docs/requirements.md)
- [Data model](docs/data-model.md)
- [Roadmap](docs/roadmap.md)
- [Quote calculators](docs/quote-calculators.md)
- [Document templates](docs/document-templates.md)
- [Pricing research plan](docs/research-plan.md)
