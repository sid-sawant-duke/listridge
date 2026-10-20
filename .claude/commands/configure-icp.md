---
description: Define your ideal customer profile and turn it into a 0–100 lead score
---

You are running `/configure-icp`. The user is an SDR, not an engineer. Ask **one short question at a time**, offer examples, and accept "skip" for anything that doesn't matter to them.

## 1. Check for an existing ICP
If `config/icp_weights.json` exists, show it as a plain-language rubric (see step 4) and ask: "Keep this, tweak it, or start over?" If they keep it, stop.

## 2. Ask about a good lead
Cover these in order, skipping anything they say doesn't matter:
1. **Target titles**, e.g. "VP Sales, Head of Revenue Ops, CRO"
2. **Seniority**, e.g. "Director and above"
3. **Company size**, as an employee range, e.g. "50–1,000"
4. **Industries**, e.g. "SaaS, fintech"
5. **Locations**, e.g. "US and Canada"
6. **Keywords** in their headline or title, e.g. "outbound, pipeline, PLG"
7. **Recent job change**: does someone being new in their role matter?
8. **Tenure**: any preferred time in role, e.g. "under 18 months"

Then ask them to **rank what matters most**. Offer a quick default: titles first, then company size, seniority, and so on.

## 3. Turn answers into weights
Build `criteria` in this exact format. Points must be whole numbers that **add up to exactly 100**, with higher-ranked items getting more points. Typical spread: top item 30–40, next 15–25, and the rest 5–15.

| What they care about | fields | match | settings |
|---|---|---|---|
| Titles | `["title"]` | `any_keyword` | `values`: lowercase title phrases, include common variants ("vp sales", "vice president sales", "head of sales") |
| Seniority | `["seniority", "title"]` | `any_keyword` | `values`: e.g. "chief", "vp", "svp", "head", "director" |
| Company size | `["company_size"]` | `size_range` | `min`, `max` (leave out `max` for "and up") |
| Industries | `["industry", "headline"]` | `any_keyword` | `values` |
| Locations | `["country", "region", "location"]` | `any_keyword` | `values`: countries, states, metros |
| Keywords | `["headline", "title"]` | `any_keyword` | `values` |
| Recent job change | `["recent_job_change"]` | `yes` | none |
| Tenure | `["tenure_months"]` | `number_range` | `min`, `max` in months |

Each criterion: `{"label": "<short plain name>", "points": N, "fields": [...], "match": "...", ...}`. See `config/icp_weights.example.json` for a full example.

Notes:
- Titles are normalized during cleaning ("Vice President" becomes "VP", "Sr." becomes "Senior"). Matching ignores filler words, so "vp sales" also matches "VP of Sales". Still include real variants like "head of sales".
- Many Sales Navigator exports don't include company size or industry. If the user's file might not, mention that leads with no data for a criterion just get 0 for it.

## 4. Confirm before saving
Show the rubric in plain language, for example:

```
Your lead score (out of 100)
  35  Title is VP Sales, Head of Sales, or CRO
  20  Company has 51–1,000 employees
  15  Director level or above
  10  Based in the US or Canada
  10  Changed jobs recently
  10  In their role under 18 months
```

Ask: "Save this? Reply **yes** or tell me what to change."

## 5. Save
Only after a yes: write `config/icp_weights.json` as `{"criteria": [...]}`, then check it:

```
.venv/bin/python -c "import json,sys; sys.path.insert(0,'scripts'); import scoring; scoring.validate(json.load(open('config/icp_weights.json'))); print('ok')"
```

If the check fails, fix the file and check again. Never leave a broken config. Finish with: "Saved. Next: `/setup-sequence` (if you haven't yet) or `/ingest-rank`."
