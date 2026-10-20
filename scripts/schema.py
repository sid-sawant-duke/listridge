"""Standard lead schema and header aliases used for column mapping."""

import re

# Output columns before the touch columns (see CLAUDE.md "Output schema").
BASE_COLUMNS = [
    "first_name", "last_name", "full_name", "title", "company", "location",
    "linkedin_url", "sales_nav_url", "tenure", "recent_job_change",
    "icp_score", "score_reasons",
    "email", "phone", "enrichment_source",
]


def touch_columns(n_touches):
    cols = []
    for i in range(1, n_touches + 1):
        cols += [f"touch{i}_day", f"touch{i}_subject", f"touch{i}_body"]
    return cols


# Fields a source file can be mapped onto. email/phone are deliberately absent:
# contact fields only ever come from a connected enrichment tool (hard rule 2).
MAPPABLE_FIELDS = [
    "full_name", "first_name", "last_name", "title", "company", "location",
    "linkedin_url", "sales_nav_url", "tenure", "recent_job_change",
    "headline", "industry", "company_size", "seniority",
]

# Extra working columns kept through the pipeline (used for scoring/drafting,
# not exported).
WORKING_COLUMNS = [
    "headline", "industry", "company_size", "seniority",
    "city", "region", "country", "tenure_months",
]

ALIASES = {
    "full_name": ["name", "full name", "lead name", "contact name", "person name"],
    "first_name": ["first name", "firstname", "first", "given name"],
    "last_name": ["last name", "lastname", "last", "surname", "family name"],
    "title": ["title", "job title", "current title", "position", "role",
              "current position", "current role"],
    "company": ["company", "company name", "account", "account name",
                "organization", "current company", "employer"],
    "location": ["location", "geography", "geo", "region", "city", "person location",
                 "lead location"],
    "linkedin_url": ["linkedin url", "linkedin", "profile url", "linkedin profile",
                     "linkedin profile url", "public profile url", "person linkedin url"],
    "sales_nav_url": ["sales navigator url", "sales nav url", "sales navigator profile",
                      "sales navigator link", "lead url", "salesnav url"],
    "tenure": ["tenure", "time in role", "time in position", "years in role",
               "time in current role", "tenure in role"],
    "recent_job_change": ["recent job change", "changed jobs", "job change",
                          "recently changed jobs", "new in role"],
    "headline": ["headline", "summary", "about", "bio"],
    "industry": ["industry", "company industry", "account industry"],
    "company_size": ["company size", "employees", "employee count", "headcount",
                     "company headcount", "number of employees", "size"],
    "seniority": ["seniority", "seniority level", "level"],
}


def norm_header(h):
    return re.sub(r"[^a-z0-9]+", " ", str(h or "").lower()).strip()


def suggest_mapping(headers):
    """Return ({field: header_or_None}, [unmapped headers])."""
    by_norm = {}
    for h in headers:
        by_norm.setdefault(norm_header(h), h)
    mapping, used = {}, set()
    for field in MAPPABLE_FIELDS:
        mapping[field] = None
        for alias in [field.replace("_", " ")] + ALIASES.get(field, []):
            h = by_norm.get(alias)
            if h is not None and h not in used:
                mapping[field] = h
                used.add(h)
                break
    unmapped = [h for h in headers if h not in used]
    return mapping, unmapped
