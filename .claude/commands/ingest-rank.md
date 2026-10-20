---
description: Load leads, clean them, remove duplicates, and score them against your ICP
---

You are running `/ingest-rank`. The user is an SDR, not an engineer. Keep messages short, use plain words, and give simple choices. Never show raw JSON or stack traces.

All processing goes through `.venv/bin/python scripts/engine.py <step>`. Each step prints JSON for you to read. If a step exits with `ERROR:` / `NEXT STEP:`, pass both lines to the user in plain words and stop.

## 0. Before you start
- If `.venv/bin/python` doesn't exist, tell the user: "Setup isn't finished. Run `./install.sh` in this folder, then try `/ingest-rank` again." Stop.
- If `config/icp_weights.json` doesn't exist, tell them scoring needs an ICP first and offer to run `/configure-icp` now. You can still load and clean the file, but stop before scoring.

## 1. Pick a source
Ask:
> Where are your leads coming from?
> **A. Upload a file** (recommended): a CSV or Excel export from Sales Navigator or anywhere else
> **B. Pull from Sales Navigator in the browser**: reads a saved lead list or search from your logged-in account

For A, continue at step 2. For B, do **Option B** below, then skip straight to step 4.

## Option B: Pull from Sales Navigator

**B1. Checks**
- No `mcp__playwright__*` tools in this session → "Browser mode isn't turned on. Run `./install.sh --browser`, restart Claude Code here, then run `/login-linkedin`." Offer A instead.
- `data/browser_consent.json` missing → show this exactly and wait for a clear yes (not "ok" in passing):
  > ⚠️ Automated browsing breaks LinkedIn's User Agreement and can get your account restricted. Use at your own risk.

  On yes, write the file as `/login-linkedin` does. On no, offer A.
- Open `https://www.linkedin.com/sales/home` and snapshot. If it shows a login page → "You're not logged in. Run `/login-linkedin` first." Stop.

**B2. What to pull**
Ask them to open the **saved lead list** or **saved search** in Sales Navigator in their own browser and paste its URL. It must be on `linkedin.com/sales/`. If not, ask again.

Ask: **"How many leads do you want to pull?"** Suggest **100**. Each Sales Nav page shows about 25 leads, so pages = leads ÷ 25, rounded up.

Respond based on the number:
- **Up to 100**: fine, go ahead.
- **101–250**: warn first and get a yes:
  > Heads up: bigger pulls look less like normal browsing, and LinkedIn is more likely to flag your account. LinkedIn doesn't publish an exact limit, so staying at 100 or fewer per run, and not doing several runs back to back, is the safer choice. Pull <N> anyway, or drop to 100?
- **Over 250**: don't do it. Say: "The limit is 250 leads per run to protect your account. I'll pull 250 now. Wait a day before pulling more." Then continue with 250 (10 pages).

If the list has fewer leads than they asked for, you'll just reach the end sooner.

**Give a time estimate before starting.** Each page takes about **2 minutes**: loading, scrolling, reading the leads, and a 20-second pause. Cleaning and scoring at the end adds about 2 minutes.

> Estimated time: **about <pages × 2 + 2> minutes** for <N> leads (<pages> pages). For example, 100 leads ≈ 10 minutes, 250 leads ≈ 22 minutes.
> I'll update you after every page. Keep this window and the Chrome window open, and don't use LinkedIn in the Chrome window while it runs. To stop early, press **Esc**. Every finished page is already saved, so just say "use what you got" and I'll continue with those leads.

Wait for a go-ahead, then note the start time.

**B3. Pull, slowly**
Create `data/pulls/<YYYYMMDD-HHMMSS>/`. For each page, 1 up to the cap:
1. Open the page. Use the list's own **Next** button, or the page URL the list uses.
2. Wait for results to load, then press **PageDown** a few times (with `browser_press_key`) so all ~25 rows render. Typing, form-filling, and custom scripts are blocked in this project on purpose.
3. Snapshot and **check for stop signs first** (below).
4. Read each lead from the snapshot. Record only what's shown, with the field left `""` when it isn't there:
   - `full_name`, `title`, `company`, `location`
   - `sales_nav_url`: the lead's `/sales/lead/...` link
   - `tenure`: e.g. "2 years 3 months in role"
   - `recent_job_change`: `"yes"` only if a "Changed jobs" / "Recently hired" badge is shown
   - `headline`, `industry`, `company_size`: only if visible
5. Write them as a JSON list to `data/pulls/<ts>/page-<n>.json`. Saving each page right away means a stopped run keeps what it got.
6. Progress update after **every** page, one line, using real elapsed time to re-estimate what's left:
   > ✓ Page 2 of 4: 50 of 100 leads so far · about 4 min left
   
   If pages are taking longer than 2 minutes, update the estimate honestly. Don't keep quoting the original. If the list ends early, say so: "The list only had 60 leads. Done pulling."
7. **Wait 20 seconds** before the next page, using the browser tool's wait. Don't skip or shorten this.
8. Stop early if there's no next page.

Never open individual lead profiles. List pages only.

**Stop signs: stop immediately on any of these.** Don't retry, don't reload, don't try another route:
- A CAPTCHA, "security verification", "let's do a quick security check", or "unusual activity"
- Any warning or restriction notice about the account, or a usage/commercial limit message
- A login or sign-in page, or being sent off `linkedin.com/sales/`

Tell the user plainly what appeared, for example: "LinkedIn showed a security check on page 3, so I stopped. I kept the 50 leads from pages 1–2. Please check your account in your normal browser before trying again, and wait a day or more." **Never try to solve, bypass, or work around these checks.**

When finished or stopped, close the browser.

If the user interrupted the pull and asks to continue with what was pulled, close the browser and go straight to B4 using the existing `data/pulls/<ts>/` folder.

**B4. Make it a run**
```
.venv/bin/python scripts/engine.py save-pull data/pulls/<ts>
```
This saves the combined pull to `data/raw/` and sets the column mapping automatically, so there's nothing to confirm. Tell them how many leads came in and how long it took, e.g. "Pulled 100 leads in 9 minutes. Cleaning and scoring now (about 2 minutes)." Then continue at **step 4**, with a one-line update as each step finishes.

## 2. Get the file
Ask them to drag the file into this window or paste its path. Then run:

```
.venv/bin/python scripts/engine.py load "<path exactly as given>"
```

## 3. Confirm the column mapping
Show `suggested_mapping` as a short two-column table: **Our field** → **Their column**. Show only mapped fields, then list `unmapped_columns` on one line. Use the `sample` rows to sanity-check it, e.g. make sure the column mapped to `linkedin_url` really holds URLs.

Show any `warnings` in plain words. If the file has email or phone columns, explain that they're ignored on purpose: contact info only comes from `/enrich`, never from the upload.

Ask: "Does this look right? Reply **yes**, or tell me what to change, e.g. *title is in 'Current Role'*."

Apply any changes. Allowed fields: `full_name, first_name, last_name, title, company, location, linkedin_url, sales_nav_url, tenure, recent_job_change, headline, industry, company_size, seniority`. Each field maps to one exact header from the file, or `null`.

Write the confirmed mapping to the `mapping_file` path from the load output, as JSON in the same shape as `suggested_mapping`. Never write it before the user says yes.

## 4. Clean, dedupe, score
Run each step in turn:

```
.venv/bin/python scripts/engine.py clean
.venv/bin/python scripts/engine.py dedupe
.venv/bin/python scripts/engine.py score
```

After `clean`, show up to 3 `examples` as quick before → after lines so the user can see what changed.

## 5. Summary
Show a short summary:

```
Leads in:            <total_in from summary>
Duplicates removed:  <duplicate_url + duplicate_name_company>
Suppressed:          <suppressed>
Already contacted:   <already_in_campaign>
Ready to score:      <scored>

Scores   80-100: n   60-79: n   40-59: n   20-39: n   0-19: n
```

Then show the top 5 leads in a short table: name, title, company, score, reason. Get `total_in` from `.venv/bin/python scripts/engine.py summary`.

## 6. Threshold
Ask: "Drop leads below a score? Pick one: **40**, **60**, a number you choose, or **keep all**." Then run:

```
.venv/bin/python scripts/engine.py threshold --min-score <N or 0>
```

Tell them how many leads were kept and dropped. Finish with: "Next: `/enrich` to add emails and phones (optional), or `/draft-sequence` to write the emails."

## Rules
- Never edit the original file or anything in `data/raw/`.
- Never fill in email or phone here.
- Lead data stays in `data/`. Don't paste whole lead lists into chat; summaries and the top 5 are enough.
