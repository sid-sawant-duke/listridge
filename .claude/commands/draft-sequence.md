---
description: Draft a personalized email sequence for every lead, review the style, and export the CSV
---

You are running `/draft-sequence`. The user is an SDR, not an engineer. Keep messages short. Never show raw JSON.

All lead data comes from `.venv/bin/python scripts/engine.py`. If a step prints `ERROR:` / `NEXT STEP:`, tell the user both in plain words and stop.

## 0. Before you start
- Read `config/sequence.json`. If it's missing, offer to run `/setup-sequence` first.
- Run `.venv/bin/python scripts/engine.py pending-drafts --limit 3`. If it errors because there's no `leads.csv`, tell them to run `/ingest-rank` first.
- If `drafted` > 0, some leads are already done from an earlier session. Say so and skip to step 3. Reread `approved_samples.json` from the run folder (`data/work/<run>/`) to get the approved style.

## How to write every email
- Use **only** facts in the lead's data: name, title, company, location, tenure, recent job change, headline, industry, company size. **Never invent** news, funding, hiring, tech stack, mutual connections, or anything else that isn't in the data (hard rule 4).
- If there's nothing specific to reference, write a strong **generic opener** about their role's common problem instead of making something up.
- Follow `sequence.json`: each touch's `purpose`, the `tone`, `length`, `cta`, `always_include`, and `avoid`, and match `voice_samples` if there are any.
- Describe the offer only with `sender.what_you_sell`. Don't invent proof points or stats.
- Write final text, with no placeholders like `{{first_name}}` or `[Company]`. The engine rejects drafts that contain them.
- Touch 1 needs a subject. Later touches can have an empty subject, which means reply in the same thread.
- Don't add email addresses, phone numbers, or links unless they're in `always_include`.

## 1. Three samples
Draft the full sequence for the **3 leads** from `pending-drafts --limit 3`. Show each one cleanly:

```
— Jane Doe · VP of Sales · Acme (score 100)
Day 1 · Subject: ...
<body>

Day 4 · Subject: (same thread)
<body>
...
```

Ask: "How's the style? Reply **approve**, or tell me what to change (shorter, more casual, different opener, and so on)."

## 2. Revise until approved
Apply their feedback and redraft the same 3 leads. Repeat until they approve.

When they approve:
- Save the 3 approved drafts with `add-drafts` (step 3 format).
- Write `data/work/<run>/approved_samples.json` with the approved sequences plus a short list of the style notes they gave, so later batches and later sessions stay consistent.

## 3. Draft everyone else in batches
Loop:
1. `.venv/bin/python scripts/engine.py pending-drafts --limit 20`
2. Draft each lead in that batch the same way.
3. Write `data/work/<run>/batch.json`:
   ```json
   {"drafts": [{"lead_id": "L0004", "touches": [{"subject": "...", "body": "..."}, {"subject": "", "body": "..."}]}]}
   ```
   The number of touches must equal the number in `sequence.json`.
4. `.venv/bin/python scripts/engine.py add-drafts data/work/<run>/batch.json`
5. If any are `rejected`, fix exactly those problems and resubmit only those leads.
6. Give the user a one-line progress update, e.g. "Drafted 40 of 112", and continue until `remaining` is 0.

Don't stop to ask between batches unless something goes wrong. If the user wants to check a specific lead, use `pending-drafts --ids L0042` to see that lead's data.

## 4. Export
Ask for a short campaign name (suggest one, e.g. `q4-revops-leaders`). Then run:

```
.venv/bin/python scripts/engine.py export --name "<name>"
```

The engine never overwrites an earlier campaign file and adds `_2`, `_3` if the name is taken.

Tell the user:
- Where the file is: give the `full_path`.
- How many leads it has, and how many have an email.
- That nothing has been sent. The file is theirs to import wherever they like.
- That these leads will now be skipped automatically in future `/ingest-rank` runs.
