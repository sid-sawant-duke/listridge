---
description: (Optional) Add work emails and phones using an enrichment tool already connected to Claude
---

You are running `/enrich`. This step is optional. The pipeline works fine without it. The user is an SDR, not an engineer. Keep it short.

## Hard rules
- **Never guess, build, or pattern-match an email or phone** (e.g. first.last@company.com). Only use values a connected tool returns. Otherwise leave the field blank.
- **Never ask for API keys.** Only use tools already connected to this Claude session.
- **Ask before spending credits.** Show the tool name and lead count, and get a clear yes first.
- Only look people up. Never use a tool's send, sequence, campaign, or "add to list" features.

## 1. See who needs a lookup
```
.venv/bin/python scripts/engine.py pending-enrich
```
If it errors because there's no `leads.csv`, tell them to run `/ingest-rank` first. If `need_lookup` is 0, say everyone already has contact info and stop.

## 2. Find a connected enrichment tool
Check your available tools for enrichment providers: Apollo, Prospeo, Hunter, Lusha, ZoomInfo, Clay, RocketReach, Cognism, Kaspr, or similar. Ignore tools that only send email.

- If a match-by-person tool exists (for Apollo, that's `apollo_people_bulk_match` or `apollo_people_match`), use it. Use bulk matching where possible to save calls.
- If the tool isn't authenticated yet, run its authentication flow first. That isn't an API key, so it's allowed.

**If none is connected**, ask once:
> No enrichment tool is connected. Want to **connect one** (Apollo, Hunter, etc.), or **skip** and leave email and phone blank?

- To connect: tell them to add the connector in Claude's settings (Settings → Connectors), then restart Claude Code in this folder and run `/enrich` again. Stop.
- To skip: say "No problem, email and phone stay blank," point to `/draft-sequence`, and stop.

## 3. Ask before spending
> I found **<Tool>**. Looking up **<need_lookup> leads** may use your <Tool> credits (up to about <need_lookup> credits; some tools also charge extra for phone numbers). Go ahead? **yes / no**

If the tool shows credit cost or balance info, show it. Also ask if they want **emails only** or **emails and phones**, since phones often cost more. Don't run anything until they say yes.

## 4. Look up and save
For each lead, send the tool only what it needs: name, company, and LinkedIn URL if available. Collect the results into `data/work/<run>/enrichment.json`:

```json
{"source": "Apollo", "results": [{"lead_id": "L0001", "email": "jane@acme.com", "phone": ""}]}
```

- Only include values the tool actually returned for **that** person. If the match is uncertain (wrong company, different person), leave it out.
- Skip emails the tool marks as invalid or unverifiable, if it says so.

Then run:
```
.venv/bin/python scripts/engine.py merge-enrichment data/work/<run>/enrichment.json
```

## 5. Report
In one or two lines: emails found X of Y, phones found X of Y, and credits used if the tool reported it. Mention any `rejected` items in plain words. Finish with: "Next: `/draft-sequence`."
