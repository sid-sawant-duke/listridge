"""Run with: .venv/bin/python -m unittest"""

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))

import cleaning as cl  # noqa: E402
import scoring  # noqa: E402
from schema import suggest_mapping  # noqa: E402


class TestCleaning(unittest.TestCase):
    def test_names(self):
        cases = {
            "Jane Doe, MBA": "Jane Doe",
            "🚀 Raj Patel 🚀": "Raj Patel",
            "MARY O'BRIEN": "Mary O'Brien",
            "carlos mcdonald": "Carlos McDonald",
            "Carlos McDonald PhD": "Carlos McDonald",
            "Dr. Ana de la Cruz (She/Her)": "Ana de la Cruz",
            "Wei Ma": "Wei Ma",
            "DeAndre Jordan": "DeAndre Jordan",
            "John Smith Jr.": "John Smith",
            "Sam Lee, CSPO, PMP": "Sam Lee",
        }
        for raw, want in cases.items():
            self.assertEqual(cl.clean_name_part(raw), want, raw)

    def test_split_name(self):
        self.assertEqual(cl.split_name("Ana de la Cruz"), ("Ana", "de la Cruz"))
        self.assertEqual(cl.split_name("Cher"), ("Cher", ""))

    def test_titles(self):
        self.assertEqual(cl.normalize_title("VICE PRESIDENT OF SALES"), "VP of Sales")
        self.assertEqual(cl.normalize_title("Sr. Director | RevOps | Helping teams"), "Senior Director")
        self.assertEqual(cl.normalize_title("Mktg Mgr"), "Marketing Manager")
        self.assertEqual(cl.normalize_title("head of demand gen"), "Head of Demand Gen")

    def test_companies(self):
        self.assertEqual(cl.normalize_company("Acme Corp, Inc."), "Acme")
        self.assertEqual(cl.normalize_company("Wayne Enterprises GmbH"), "Wayne Enterprises")
        self.assertEqual(cl.normalize_company("IBM"), "IBM")
        self.assertEqual(cl.company_key("Hooli Inc"), cl.company_key("Hooli"))

    def test_location(self):
        self.assertEqual(cl.parse_location("Austin, Texas, United States")[1:], ("Austin", "Texas", "United States"))
        self.assertEqual(cl.parse_location("New York, NY")[1:], ("New York", "NY", "United States"))
        self.assertEqual(cl.parse_location("Berlin, Germany")[1:], ("", "Berlin", "Germany"))

    def test_urls(self):
        a = cl.url_key("linkedin.com/in/JaneDoe/?utm_source=share")
        b = cl.url_key("https://www.linkedin.com/in/janedoe")
        self.assertEqual(a, b)
        self.assertTrue(cl.is_sales_nav_url("https://www.linkedin.com/sales/lead/ACw1"))
        self.assertEqual(cl.normalize_url("https://www.linkedin.com/sales/lead/ACwAAA1,NAME_SEARCH,xYz"),
                         "https://www.linkedin.com/sales/lead/ACwAAA1")

    def test_tenure(self):
        self.assertEqual(cl.tenure_months("1 year 2 months"), 14)
        self.assertEqual(cl.tenure_months("2 yrs 6 mos"), 30)
        self.assertEqual(cl.tenure_months("8 months"), 8)
        self.assertEqual(cl.tenure_months("less than a year"), 6)
        self.assertEqual(cl.tenure_months(""), "")

    def test_mapping_suggestion(self):
        m, unmapped = suggest_mapping(["Name", "Job Title", "Profile URL", "Email", "Random"])
        self.assertEqual(m["full_name"], "Name")
        self.assertEqual(m["title"], "Job Title")
        self.assertEqual(m["linkedin_url"], "Profile URL")
        self.assertIn("Email", unmapped)  # contact fields never mapped (hard rule 2)


class TestScoring(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((ROOT / "config" / "icp_weights.example.json").read_text())

    def test_example_config_valid(self):
        scoring.validate(self.cfg)

    def test_points_must_total_100(self):
        bad = {"criteria": [{"label": "x", "points": 50, "fields": ["title"], "match": "yes"}]}
        with self.assertRaises(scoring.ConfigError):
            scoring.validate(bad)

    def test_score_is_deterministic_and_explained(self):
        lead = {"title": "VP of Sales", "company_size": "51-200", "country": "United States",
                "recent_job_change": "yes", "tenure_months": "14"}
        s1, r1 = scoring.score_lead(lead, self.cfg)
        s2, r2 = scoring.score_lead(lead, self.cfg)
        self.assertEqual((s1, r1), (s2, r2))
        self.assertEqual(s1, 100)
        self.assertIn("Target title (vp sales) +35", r1)

    def test_missing_data_scores_zero_and_says_so(self):
        s, r = scoring.score_lead({"title": "Account Executive"}, self.cfg)
        self.assertEqual(s, 0)
        self.assertIn("no data: company size", r)

    def test_size_parsing(self):
        self.assertEqual(scoring.parse_size("1,001-5,000 employees"), (1001, 5000))
        self.assertEqual(scoring.parse_size("10,001+"), (10001, float("inf")))


class TestPipeline(unittest.TestCase):
    """End to end through the CLI in a throwaway project root."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "config").mkdir()
        (self.tmp / "data" / "campaigns").mkdir(parents=True)
        shutil.copy(ROOT / "config" / "icp_weights.example.json", self.tmp / "config" / "icp_weights.json")
        (self.tmp / "data" / "suppression.csv").write_text(
            "linkedin_url,full_name,company,reason\n"
            "https://www.linkedin.com/in/suppressed-person,,,opted out\n")
        self.env = {**os.environ, "LISTWRIGHT_ROOT": str(self.tmp)}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def engine(self, *args, ok=True):
        p = subprocess.run([sys.executable, str(ROOT / "scripts" / "engine.py"), *args],
                           env=self.env, capture_output=True, text=True)
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr)
            return json.loads(p.stdout)
        return p

    def run_pipeline(self, fixture):
        load = self.engine("load", str(HERE / "fixtures" / fixture))
        run_dir = self.tmp / "data" / "work" / load["run"]
        shutil.copy(run_dir / "mapping.suggested.json", run_dir / "mapping.json")
        clean = self.engine("clean")
        dedupe = self.engine("dedupe")
        score = self.engine("score")
        return load, clean, dedupe, score, run_dir

    def test_csv_pipeline(self):
        load, clean, dedupe, score, run_dir = self.run_pipeline("messy_leads.csv")
        self.assertEqual(load["rows"], 9)  # preamble line and blank row skipped
        self.assertTrue((self.tmp / load["raw_copy"]).exists())
        self.assertEqual(clean["cleaned"], 9)
        self.assertEqual(dedupe["duplicate_url"], 1)            # Jane Doe twice
        self.assertEqual(dedupe["duplicate_name_company"], 1)   # Carlos McDonald / Hooli
        self.assertEqual(dedupe["suppressed"], 1)
        self.assertEqual(dedupe["kept"], 6)
        self.assertEqual(score["scored"], 6)
        scores = [l["icp_score"] for l in score["top_leads"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

        thr = self.engine("threshold", "--min-score", "60")
        with open(run_dir / "leads.csv", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), thr["kept"])
        self.assertTrue(all(int(r["icp_score"]) >= 60 for r in rows))
        self.assertTrue(all(r["email"] == "" and r["phone"] == "" for r in rows))

    def test_xlsx_matches_csv(self):
        _, _, dedupe, score, _ = self.run_pipeline("messy_leads.xlsx")
        self.assertEqual(dedupe["kept"], 6)
        self.assertEqual(score["scored"], 6)

    def test_past_campaign_leads_removed(self):
        (self.tmp / "data" / "campaigns" / "q3_2026-09-01.csv").write_text(
            "full_name,company,linkedin_url\nMary O'Brien,Initech,\n")
        _, _, dedupe, _, _ = self.run_pipeline("messy_leads.csv")
        self.assertEqual(dedupe["already_in_campaign"], 1)
        self.assertEqual(dedupe["kept"], 5)

    def test_missing_icp_gives_plain_error(self):
        (self.tmp / "config" / "icp_weights.json").unlink()
        load = self.engine("load", str(HERE / "fixtures" / "messy_leads.csv"))
        run_dir = self.tmp / "data" / "work" / load["run"]
        shutil.copy(run_dir / "mapping.suggested.json", run_dir / "mapping.json")
        self.engine("clean")
        self.engine("dedupe")
        p = self.engine("score", ok=False)
        self.assertEqual(p.returncode, 2)
        self.assertIn("/configure-icp", p.stderr)

    def test_missing_file_gives_plain_error(self):
        p = self.engine("load", "/nope/leads.csv", ok=False)
        self.assertEqual(p.returncode, 2)
        self.assertIn("Couldn't find the file", p.stderr)

    def _ready_run(self):
        shutil.copy(ROOT / "config" / "sequence.example.json", self.tmp / "config" / "sequence.json")
        *_, run_dir = self.run_pipeline("messy_leads.csv")
        self.engine("threshold", "--min-score", "0")
        return run_dir

    def _draft_all(self, run_dir):
        pending = self.engine("pending-drafts", "--limit", "100")
        batch = {"drafts": [{"lead_id": l["lead_id"], "touches": [
            {"subject": f"Quick idea for {l.get('company', 'you')}", "body": f"=SUM(1) hi {l['first_name']}"},
            {"subject": "", "body": "Following up."},
            {"subject": "", "body": "Last note from me."}]} for l in pending["leads"]]}
        (run_dir / "batch.json").write_text(json.dumps(batch))
        return self.engine("add-drafts", str(run_dir / "batch.json"))

    def test_drafts_validation(self):
        run_dir = self._ready_run()
        bad = {"drafts": [
            {"lead_id": "L0001", "touches": [{"subject": "Hi {{first_name}}", "body": "x"},
                                             {"subject": "", "body": "y"}, {"subject": "", "body": "z"}]},
            {"lead_id": "L0002", "touches": [{"subject": "Hi", "body": "only one touch"}]},
            {"lead_id": "L9999", "touches": []},
        ]}
        (run_dir / "batch.json").write_text(json.dumps(bad))
        res = self.engine("add-drafts", str(run_dir / "batch.json"))
        self.assertEqual(res["saved"], 0)
        self.assertEqual(len(res["rejected"]), 3)

    def test_export_never_overwrites(self):
        run_dir = self._ready_run()
        self.assertEqual(self._draft_all(run_dir)["remaining"], 0)
        first = self.engine("export", "--name", "Q4 Test!")
        second = self.engine("export", "--name", "Q4 Test!")
        self.assertNotEqual(first["file"], second["file"])
        self.assertTrue(second["file"].endswith("_2.csv"))
        with open(first["full_path"], encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(reader.fieldnames[-3:], ["touch3_day", "touch3_subject", "touch3_body"])
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]["touch2_day"], "4")
        self.assertNotIn("lead_id", rows[0])
        # formula-looking text is neutralized for spreadsheet apps
        self.assertTrue(all(r["touch1_body"].startswith("'=SUM") for r in rows))
        # exported leads (and their in-file duplicates) are skipped by the next ingest
        _, _, dedupe, _, _ = self.run_pipeline("messy_leads.csv")
        self.assertEqual(dedupe["already_in_campaign"], 8)
        self.assertEqual(dedupe["kept"], 0)

    def test_export_blocked_until_all_drafted(self):
        self._ready_run()
        p = self.engine("export", "--name", "x", ok=False)
        self.assertEqual(p.returncode, 2)
        self.assertIn("/draft-sequence", p.stderr)

    def test_enrichment_only_writes_tool_values(self):
        run_dir = self._ready_run()
        todo = self.engine("pending-enrich")
        self.assertEqual(todo["need_lookup"], 6)
        res_file = run_dir / "enrichment.json"
        res_file.write_text(json.dumps({"source": "Apollo", "results": [
            {"lead_id": "L0001", "email": "jane@acme.com", "phone": "+1 415 555 0100"},
            {"lead_id": "L0002", "email": "not-an-email"},
            {"lead_id": "L0003", "email": ""},
        ]}))
        res = self.engine("merge-enrichment", str(res_file))
        self.assertEqual((res["emails_added"], res["phones_added"]), (1, 1))
        self.assertEqual(len(res["rejected"]), 1)
        with open(run_dir / "leads.csv", encoding="utf-8") as f:
            rows = {r["lead_id"]: r for r in csv.DictReader(f)}
        self.assertEqual(rows["L0001"]["enrichment_source"], "Apollo")
        self.assertEqual(rows["L0002"]["email"], "")
        self.assertEqual(rows["L0003"]["enrichment_source"], "")
        # changing the cutoff now would discard enrichment, so it's refused
        p = self.engine("threshold", "--min-score", "50", ok=False)
        self.assertEqual(p.returncode, 2)

    def test_browser_pull_becomes_a_run(self):
        pull = self.tmp / "data" / "pulls" / "20261019-120000"
        pull.mkdir(parents=True)
        page1 = [
            {"full_name": "Jane Doe, MBA", "title": "VP of Sales", "company": "Acme Inc.",
             "location": "Austin, Texas, United States",
             "sales_nav_url": "https://www.linkedin.com/sales/lead/ACwAAA1,NAME_SEARCH,abc",
             "tenure": "1 year 2 months in role", "recent_job_change": "yes"},
            {"full_name": "Raj Patel", "title": "Head of Sales", "company": "Globex",
             "sales_nav_url": "https://www.linkedin.com/sales/lead/ACwBBB2,NAME_SEARCH,def"},
        ]
        page2 = [  # Jane again, with a different search suffix on her link
            {"full_name": "Jane Doe", "title": "VP Sales", "company": "Acme",
             "sales_nav_url": "https://www.linkedin.com/sales/lead/ACwAAA1,NAME_SEARCH,zzz"},
            {"full_name": "", "company": "Blank row"},
        ]
        (pull / "page-1.json").write_text(json.dumps(page1))
        (pull / "page-2.json").write_text(json.dumps(page2))
        res = self.engine("save-pull", str(pull))
        self.assertEqual(res["pages"], 2)
        self.assertEqual(res["rows"], 2)  # Jane's repeat across pages and the blank row dropped
        self.assertEqual(res["skipped_repeats_or_blank"], 2)
        self.assertTrue((self.tmp / res["raw_copy"]).exists())
        clean = self.engine("clean")  # mapping was written automatically
        self.assertEqual(clean["examples"][0]["name"]["after"], "Jane Doe")
        self.assertEqual(self.engine("dedupe")["kept"], 2)

    def test_drag_and_drop_path(self):
        spaced = self.tmp / "my leads.csv"
        shutil.copy(HERE / "fixtures" / "messy_leads.csv", spaced)
        load = self.engine("load", f"'{str(spaced).replace(' ', chr(92) + ' ')}' ")
        self.assertEqual(load["rows"], 9)


if __name__ == "__main__":
    unittest.main()
