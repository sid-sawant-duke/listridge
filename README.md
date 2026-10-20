# Listwright

Turn a list of leads into a clean, scored, ready-to-import CSV, with a personalized email sequence written for every lead.

It runs on your Mac inside Claude Code. **It never sends anything.** You get a file and decide what to do with it.

## What it does

1. **Cleans** your lead list: fixes names ("JANE DOE, MBA" becomes "Jane Doe"), titles, and company names.
2. **Removes** duplicates, people on your do-not-contact list, and anyone already in a past campaign.
3. **Scores** every lead 0–100 against your ideal customer profile and says why.
4. **Adds** emails and phones (optional), only from a tool you've already connected, like Apollo. It never guesses.
5. **Writes** a multi-email sequence for every lead, using only real facts from their profile.
6. **Exports** one CSV to `data/campaigns/`.

## Setup (one time)

You need a Mac with [Claude Code](https://claude.com/claude-code) and Python 3.9 or newer. If Python is missing, the installer tells you how to get it.

```bash
cd listwright
./install.sh
claude
```

## How to use it

Inside Claude Code, run these in order:

| Command | What it does | How often |
|---|---|---|
| `/configure-icp` | Describe your ideal lead → becomes your 0–100 score | Once, then tweak anytime |
| `/setup-sequence` | What you sell, how many emails, timing, tone, call to action | Once, then tweak anytime |
| `/ingest-rank` | Upload a CSV or Excel file → clean, dedupe, score | Every new list |
| `/enrich` | *(Optional)* Add emails and phones from a connected tool | Every new list |
| `/draft-sequence` | Review 3 samples, then write emails for everyone and export | Every new list |

To upload a file, drag it into the Claude Code window when asked.

## Where your files go

Everything stays on your computer in `data/`, and is never committed to git:

- `data/raw/` holds an untouched copy of every file you upload.
- `data/campaigns/` holds your exported campaigns, one new file per export. Old ones are never overwritten.
- `data/suppression.csv` is your do-not-contact list. Add a row (LinkedIn URL, or full name + company) and that person won't show up again.
- `data/work/` holds working files for each run, handy if something looks off.

## Good to know

- **Contact info:** email and phone only come from a connected enrichment tool. Email or phone columns in your upload are ignored. If you don't enrich, those columns stay blank.
- **Credits:** `/enrich` always tells you how many lookups it will run and asks before spending credits.
- **Repeat contacts:** once you export a campaign, those people are skipped automatically in future lists.

## Browser mode (optional)

Instead of uploading a file, Claude can read a saved lead list or search straight from your Sales Navigator account.

> ⚠️ **Automated browsing breaks LinkedIn's User Agreement and can get your account restricted. Use at your own risk.** Uploading a file is the safer, recommended option.

To turn it on, you need Google Chrome and [Node.js](https://nodejs.org):

```bash
./install.sh --browser
claude          # choose "yes" when asked about the playwright server
```

Then in Claude Code:

1. Run `/login-linkedin` once. A separate Chrome window opens and **you** log in yourself; Claude never sees your password. The login is saved in `.browser-session/` on your Mac.
2. Run `/ingest-rank`, choose option B, and paste the URL of a saved list or search.

Built-in limits protect your account:
- You choose how many leads to pull. 100 or fewer per run is recommended. Up to 250 is allowed after a warning, since bigger pulls are more likely to get flagged. Over 250 is never pulled in one run.
- Before starting, you get a time estimate (about 2 minutes per 25 leads, e.g. 100 leads ≈ 10 minutes) and a progress update after every page. Press **Esc** any time to stop; pages already pulled are kept.
- There's a 20-second pause between pages.
- Only list pages are read. Individual profiles are never opened.
- If LinkedIn shows a security check, a warning or a login page, it **stops immediately** and keeps what it already pulled. It never tries to get around these.

To log out of browser mode completely, delete the `.browser-session` folder.

## For developers

- Processing lives in `scripts/engine.py`. Run `.venv/bin/python scripts/engine.py --help` to see every step.
- Tests: `.venv/bin/python -m unittest`
- Project rules for Claude are in `CLAUDE.md`.
