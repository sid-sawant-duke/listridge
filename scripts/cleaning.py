"""Cleaning helpers: names, titles, companies, locations, URLs, tenure."""

import re
import unicodedata
from urllib.parse import urlsplit

# --- generic text -----------------------------------------------------------

_EMOJI_EXTRA = {0x200D, 0xFE0E, 0xFE0F, 0x20E3}


def strip_emoji(s):
    out = []
    for ch in s:
        cp = ord(ch)
        if cp in _EMOJI_EXTRA or 0x1F3FB <= cp <= 0x1F3FF or 0xE0020 <= cp <= 0xE007F:
            continue
        if unicodedata.category(ch) in ("So", "Cs", "Co"):
            continue
        out.append(ch)
    return "".join(out)


def squash(s):
    return re.sub(r"\s+", " ", s or "").strip(" \t,;|-–—")


def text(s):
    return squash(strip_emoji(unicodedata.normalize("NFC", str(s or ""))))


# --- names ------------------------------------------------------------------

CREDENTIALS = {
    "mba", "phd", "ph.d", "cpa", "pmp", "cfa", "md", "m.d", "jd", "j.d", "esq",
    "csm", "cspo", "shrm-cp", "shrm-scp", "phr", "sphr", "cissp", "cism", "ccie",
    "rn", "bsn", "msn", "ms", "msc", "ma", "ba", "bs", "bsc", "mph", "mha", "dds",
    "cfp", "chfc", "clu", "cma", "cia", "frm", "pe", "leed ap", "six sigma",
    "mcse", "aws", "ea", "edd", "ed.d", "llm", "mfa", "mpa", "msw", "lcsw",
    "jr", "sr", "ii", "iii", "iv",
}
_PREFIXES = re.compile(r"^(dr|mr|mrs|ms|miss|prof)\.?\s+", re.I)
_PAREN = re.compile(r"\s*[\(\[].*?[\)\]]\s*")
_PARTICLES = {"van", "von", "de", "da", "del", "della", "der", "den", "di", "la", "le", "du", "dos", "st."}


def _is_credential(tok):
    t = tok.strip(" .,").lower()
    if not t:
        return True
    if t in CREDENTIALS or t.replace(".", "") in {c.replace(".", "") for c in CREDENTIALS}:
        return True
    # all-caps acronym of 2-5 letters after a comma, e.g. "CSPO", "PMP", "CRO"
    return bool(re.fullmatch(r"[A-Z]{2,5}(-[A-Z]{2,3})?", tok.strip(" .,")))


def _cap_word(w):
    if not w:
        return w
    if "-" in w:
        return "-".join(_cap_word(p) for p in w.split("-"))
    if "'" in w and len(w) > 2:
        a, b = w.split("'", 1)
        return _cap_word(a) + "'" + _cap_word(b)
    low = w.lower()
    if low.startswith("mc") and len(w) > 2:
        return "Mc" + low[2:].capitalize()
    return low.capitalize()


def fix_name_case(name):
    """Only re-case names that are ALL CAPS or all lower; keep deliberate mixed case."""
    letters = [c for c in name if c.isalpha()]
    if not letters or not (all(c.isupper() for c in letters) or all(c.islower() for c in letters)):
        return name
    words = name.split()
    out = []
    for i, w in enumerate(words):
        if 0 < i < len(words) - 1 and w.lower() in _PARTICLES:
            out.append(w.lower())
        else:
            out.append(_cap_word(w))
    return " ".join(out)


def clean_name_part(s):
    s = text(s)
    s = _PAREN.sub(" ", s)
    s = _PREFIXES.sub("", s)
    if "," in s:
        head, *rest = [p.strip() for p in s.split(",")]
        keep = [p for p in rest if p and not all(_is_credential(t) for t in p.split())]
        s = " ".join([head] + keep)
    # Trailing credentials without a comma ("Jane Doe MBA"). Only when 3+ tokens and the
    # token looks deliberate (caps or dotted), so short surnames like "Ma" survive.
    toks = s.split()
    while (len(toks) > 2 and toks[-1].strip(".").lower() in CREDENTIALS
           and (toks[-1].isupper() or "." in toks[-1] or toks[-1].lower() in {"jr", "sr"}
                or any(c.isupper() for c in toks[-1][1:]))):
        toks.pop()
    s = " ".join(toks).strip(" .,")
    return fix_name_case(squash(s))


def split_name(full):
    """'Jane van der Berg' -> ('Jane', 'van der Berg')."""
    parts = full.split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


# --- titles -----------------------------------------------------------------

ACRONYMS = {
    "ceo", "cfo", "coo", "cto", "cro", "cmo", "cio", "ciso", "cpo", "cco", "cso",
    "vp", "svp", "evp", "avp", "gm", "hr", "it", "ai", "ml", "gtm", "sdr", "bdr",
    "ae", "am", "csm", "b2b", "b2c", "saas", "emea", "apac", "latam", "amer",
    "na", "us", "uk", "eu", "ux", "ui", "qa", "pr", "seo", "ops", "revops",
    "abm", "plg", "smb", "erp", "crm", "ibm", "aws", "sap", "llc",
}
_TITLE_SUBS = [
    (r"\bsenior vice president\b", "SVP"),
    (r"\bexecutive vice president\b", "EVP"),
    (r"\bassistant vice president\b", "AVP"),
    (r"\bvice president\b", "VP"),
    (r"\bv\.p\.?", "VP"),
    (r"\bsr\.?(?=\s|$)", "Senior"),
    (r"\bjr\.?(?=\s|$)", "Junior"),
    (r"\bmgr\.?(?=\s|$)", "Manager"),
    (r"\bdir\.?(?=\s|$)", "Director"),
    (r"\bmktg\b", "Marketing"),
    (r"\bbiz dev\b", "Business Development"),
]
_SMALL = {"of", "and", "the", "for", "to", "in", "at", "on", "&"}


def _smart_case(s):
    words = s.split()
    out = []
    for i, w in enumerate(words):
        core = w.strip("(),/").lower()
        if core in ACRONYMS:
            out.append(w.upper() if core != "saas" else w.lower().replace("saas", "SaaS"))
        elif i > 0 and core in _SMALL:
            out.append(w.lower())
        else:
            out.append(_cap_word(w) if w.isalpha() else w[:1].upper() + w[1:].lower())
    return " ".join(out)


def normalize_title(s):
    s = text(s)
    # Headline-style titles: keep the part before the first separator.
    s = re.split(r"\s+[|•·]\s+|\s+@\s+", s)[0]
    for pat, rep in _TITLE_SUBS:
        s = re.sub(pat, rep, s, flags=re.I)
    letters = [c for c in s if c.isalpha()]
    if letters and (all(c.isupper() for c in letters) or all(c.islower() for c in letters)):
        s = _smart_case(s)
    else:
        s = " ".join(w.upper() if w.lower() in ACRONYMS and w.lower() not in {"it", "am", "us", "na", "ai"} else w
                     for w in s.split())
    return squash(s)


# --- companies --------------------------------------------------------------

_LEGAL = re.compile(
    r"[,\s]+(inc|incorporated|llc|l\.l\.c|ltd|limited|corp|corporation|co|gmbh|"
    r"s\.?a|s\.?a\.?s|ag|plc|pty|bv|b\.v|oy|ab|srl|sarl|lp|llp)\.?$",
    re.I,
)


def normalize_company(s):
    s = text(s)
    prev = None
    while prev != s:
        prev = s
        s = _LEGAL.sub("", s).strip(" ,.")
    letters = [c for c in s if c.isalpha()]
    if letters and all(c.isupper() for c in letters) and len(letters) > 4 and " " in s:
        s = " ".join(w if len(w) <= 3 else _cap_word(w) for w in s.split())
    elif letters and all(c.islower() for c in letters):
        s = _smart_case(s)
    return squash(s)


def company_key(s):
    return re.sub(r"[^a-z0-9]", "", normalize_company(s).lower())


# --- locations --------------------------------------------------------------

COUNTRIES = {
    "united states", "usa", "us", "united kingdom", "uk", "canada", "australia",
    "germany", "france", "india", "ireland", "netherlands", "spain", "italy",
    "sweden", "singapore", "israel", "brazil", "mexico", "japan", "switzerland",
    "denmark", "norway", "finland", "belgium", "austria", "poland", "portugal",
    "new zealand", "south africa", "united arab emirates", "uae",
}


US_STATES = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id", "il", "in",
    "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv",
    "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc", "sd", "tn",
    "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy", "dc",
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island",
    "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west virginia", "wisconsin", "wyoming", "district of columbia",
}


def parse_location(s):
    """Return (clean_location, city, region, country)."""
    s = text(s)
    parts = [p.strip() for p in s.split(",") if p.strip()]
    city = region = country = ""
    if len(parts) >= 3:
        city, region, country = parts[0], parts[1], parts[-1]
    elif len(parts) == 2:
        if parts[1].lower() in COUNTRIES:
            region, country = parts
        else:
            city, region = parts
            if region.lower() in US_STATES:
                country = "United States"
    elif len(parts) == 1:
        if parts[0].lower() in COUNTRIES:
            country = parts[0]
        else:
            region = parts[0]
    return ", ".join(parts), city, region, country


# --- urls -------------------------------------------------------------------

def normalize_url(s):
    s = text(s)
    if not s:
        return ""
    if not re.match(r"^https?://", s, re.I):
        s = "https://" + s
    p = urlsplit(s)
    host = p.netloc.lower()
    if host.endswith("linkedin.com"):
        host = "www.linkedin.com"
    path = p.path.rstrip("/")
    if "/in/" in path.lower():
        path = path.lower()
    # Sales Nav lead links carry search context after the ID:
    # /sales/lead/ACwAAA123,NAME_SEARCH,xYz -> /sales/lead/ACwAAA123
    m = re.match(r"(/sales/(?:lead|people)/[^,/]+)", path, re.I)
    if m:
        path = m.group(1)
    return f"https://{host}{path}"


def is_sales_nav_url(url):
    return "/sales/" in url.lower()


def url_key(url):
    u = normalize_url(url)
    return u.lower().split("://", 1)[-1] if u else ""


# --- tenure / job change ----------------------------------------------------

def tenure_months(s):
    s = text(s).lower()
    if not s:
        return ""
    if re.search(r"less than (a|one|1) year", s):
        return 6
    years = re.search(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?|y)\b", s)
    months = re.search(r"(\d+)\s*(?:months?|mos?|m)\b", s)
    if not years and not months:
        bare = re.fullmatch(r"\d+(?:\.\d+)?", s)
        return round(float(s) * 12) if bare else ""
    total = 0.0
    if years:
        total += float(years.group(1)) * 12
    if months:
        total += int(months.group(1))
    return round(total)


_YES = {"yes", "y", "true", "1", "x", "changed jobs", "recently changed jobs", "new role", "job change"}
_NO = {"no", "n", "false", "0"}


def yes_no(s):
    t = text(s).lower()
    if t in _YES or t.startswith("changed jobs"):
        return "yes"
    if t in _NO:
        return "no"
    return ""
