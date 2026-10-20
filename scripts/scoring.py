"""Apply config/icp_weights.json to a lead and explain the score in plain English.

Config format:
{
  "criteria": [
    {"label": "Target title", "points": 30, "fields": ["title"],
     "match": "any_keyword", "values": ["vp sales", "head of sales"]},
    {"label": "Company size", "points": 15, "fields": ["company_size"],
     "match": "size_range", "min": 51, "max": 500},
    {"label": "Tenure under a year", "points": 10, "fields": ["tenure_months"],
     "match": "number_range", "min": 0, "max": 12},
    {"label": "Recent job change", "points": 10, "fields": ["recent_job_change"],
     "match": "yes"}
  ]
}
Points must add up to 100.
"""

import re

MATCH_TYPES = {"any_keyword", "size_range", "number_range", "yes"}


class ConfigError(Exception):
    pass


def validate(cfg):
    crit = cfg.get("criteria")
    if not isinstance(crit, list) or not crit:
        raise ConfigError("The ICP file has no criteria.")
    total = 0
    for c in crit:
        for key in ("label", "points", "fields", "match"):
            if key not in c:
                raise ConfigError(f"An ICP criterion is missing '{key}'.")
        if c["match"] not in MATCH_TYPES:
            raise ConfigError(f"Unknown match type '{c['match']}' in '{c['label']}'.")
        if c["match"] == "any_keyword" and not c.get("values"):
            raise ConfigError(f"'{c['label']}' has no keywords.")
        total += c["points"]
    if round(total) != 100:
        raise ConfigError(f"ICP points add up to {total}, not 100.")


_FILLER = {"of", "the", "and", "&", "for", "a", "an"}


def _words(s):
    return " ".join(w for w in re.sub(r"[^a-z0-9+&]+", " ", s.lower()).split() if w not in _FILLER)


def _keyword_hit(value, keywords):
    """Whole-word match, ignoring filler words: 'vp sales' matches 'VP of Sales'."""
    v = f" {_words(value)} "
    for kw in keywords:
        k = _words(kw)
        if k and f" {k} " in v:
            return kw
    return None


def parse_size(s):
    """'51-200 employees' -> (51, 200); '10,001+' -> (10001, inf); '250' -> (250, 250)."""
    t = str(s or "").replace(",", "").lower()
    nums = [int(n) for n in re.findall(r"\d+", t)]
    if not nums:
        return None
    if "+" in t or "more" in t or "over" in t:
        return nums[0], float("inf")
    if len(nums) >= 2:
        return nums[0], nums[1]
    return nums[0], nums[0]


def _to_number(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def score_lead(lead, cfg):
    """Return (score 0-100, reasons string)."""
    score = 0
    hits, misses, missing = [], [], []
    for c in cfg["criteria"]:
        label, pts = c["label"], c["points"]
        values = [str(lead.get(f) or "").strip() for f in c["fields"]]
        values = [v for v in values if v]
        if not values:
            missing.append(label.lower())
            continue
        matched = None
        if c["match"] == "any_keyword":
            for v in values:
                kw = _keyword_hit(v, c["values"])
                if kw:
                    matched = f"{label} ({kw})"
                    break
        elif c["match"] == "yes":
            if any(v.lower() == "yes" for v in values):
                matched = label
        elif c["match"] == "size_range":
            rng = parse_size(values[0])
            lo, hi = c.get("min", 0), c.get("max") or float("inf")
            if rng and rng[0] <= hi and rng[1] >= lo:
                matched = f"{label} ({values[0]})"
        elif c["match"] == "number_range":
            n = _to_number(values[0])
            lo, hi = c.get("min", 0), c.get("max") or float("inf")
            if n is not None and lo <= n <= hi:
                matched = label
        if matched:
            score += pts
            hits.append(f"{matched} +{pts:g}")
        else:
            misses.append(label.lower())

    parts = []
    if hits:
        parts.append("; ".join(hits))
    if misses:
        parts.append("not a match: " + ", ".join(misses))
    if missing:
        parts.append("no data: " + ", ".join(missing))
    return round(min(score, 100)), " | ".join(parts) or "No criteria matched"
