---
description: Set your email sequence — what you sell, touches, timing, tone, call to action, and voice
---

You are running `/setup-sequence`. The user is an SDR, not an engineer. Ask **one short question at a time** and give a default they can accept by replying "ok".

## 1. Check for an existing sequence
If `config/sequence.json` exists, summarize it in a few lines and ask: "Keep it, tweak it, or start over?"

## 2. Ask
1. **You and your offer**: your name, your company, and what you sell in one or two sentences. Also how you sign off, e.g. "Alex".
2. **Touches**: how many emails? Default **3**.
3. **Timing**: which day each one goes out. Default **day 1, day 4, day 9**. Days must go up, starting at day 1.
4. **Tone**: e.g. friendly and direct, formal, playful. Default "friendly and direct, no hype".
5. **Length**: default "short: under 90 words per email".
6. **Call to action**: e.g. "a 15-minute call next week", "reply with who owns this".
7. **Your voice** (optional): paste 1–3 past emails you liked. Save them as-is.
8. **Always include / always avoid** (optional): e.g. "always mention our free audit", "avoid exclamation marks".

Give each touch a one-line `purpose` that fits its position. The defaults are intro, then follow-up with a new angle, then a polite breakup. Show these and let the user change them.

## 3. Confirm, then save
Show a short plain summary:

```
From: Alex at Pipeline Co
Sells: <one line>
3 emails: day 1 (intro) · day 4 (follow-up) · day 9 (breakup)
Tone: friendly and direct · Length: under 90 words
Ask: a 15-minute call next week
Avoid: exclamation marks
```

After a yes, write `config/sequence.json` in the same shape as `config/sequence.example.json`:
`sender {name, company, what_you_sell, sign_off}`, `touches [{day, purpose}]`, `tone`, `length`, `cta`, `voice_samples []`, `always_include []`, `avoid []`.

Finish with: "Saved. Next: `/ingest-rank` to load your leads."

## Rules
- Don't invent proof points, customer names, or stats for their offer. Use only what the user tells you. If they want proof in the emails, ask them for it.
