---
description: (Browser mode) One-time Sales Navigator login, saved in a private local browser profile
---

You are running `/login-linkedin`. The user is an SDR, not an engineer. Keep it short.

## 1. Check browser mode is set up
If no `mcp__playwright__*` browser tools are available in this session:
> Browser mode isn't turned on. In Terminal, run `./install.sh --browser` in this folder, then restart Claude Code here. When it asks about the **playwright** server, choose yes. Then run `/login-linkedin` again.

Stop.

## 2. Risk warning (first time only)
If `data/browser_consent.json` doesn't exist, show this **exactly** and wait for a clear yes:

> ⚠️ Automated browsing breaks LinkedIn's User Agreement and can get your account restricted. Use at your own risk.
>
> Type **yes** to continue, or **no** to stick with file uploads.

Only an explicit yes counts ("yes", "I accept", "go ahead"). "ok" or "sure" in passing doesn't count. If unclear, ask again. On no, suggest exporting the list to a file and using `/ingest-rank` → Upload. Stop.

On yes, write `data/browser_consent.json` with `{"accepted": true, "date": "<YYYY-MM-DD>"}`.

## 3. Log in. The user does this, not you.
Open `https://www.linkedin.com/sales/login` in the browser tool. Then say:

> A Chrome window just opened. Log in to Sales Navigator there yourself, including any 2-step code. I won't see or type your password. Reply **done** when you see your Sales Navigator home page.

- **Never** type, ask for, or store the user's email, password, or 2FA codes. If they paste a password in chat, tell them not to and don't use it.
- Don't click anything on the login page.

## 4. Confirm
When they reply done, open `https://www.linkedin.com/sales/home` and take a snapshot.
- If it shows the Sales Navigator home (not a login form): "You're logged in. The login is saved on this Mac in `.browser-session/`, so you won't need to do this again unless LinkedIn logs you out."
- If it still shows a login page: ask them to finish logging in, then check once more.
- If it shows a CAPTCHA, security check, or a warning about the account: **stop**. Tell them what you see and that they should resolve it themselves in the window. Never try to get around it.

Close the browser at the end. Finish with: "Next: `/ingest-rank` → option B."
