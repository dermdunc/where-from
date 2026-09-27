"""End-to-end behaviour of the exhibit, against a temp copy of examples/sources."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "sources"


def run(*args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "wherefrom", *args],
        cwd=cwd, capture_output=True, text=True,
        env={"PYTHONPATH": str(ROOT), "PATH": ""},
    )


class ExhibitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "sources"
        shutil.copytree(EXAMPLES, self.src)
        r = run("build", "--sources", str(self.src), cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def about(self, service, *extra):
        r = run("about", service, "--json", *extra, cwd=self.tmp)
        return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else None)

    def test_joins_both_sources_with_provenance(self):
        code, ans = self.about("checkout")
        self.assertEqual(code, 0)
        by_source = {f["source"] for f in ans["facts"]}
        self.assertEqual(by_source, {"catalog", "adr"})
        owner = [f for f in ans["facts"] if f["field"] == "owner"][0]
        self.assertEqual(owner["value"], "payments-team")
        self.assertEqual(owner["source_path"], "catalog.json#checkout")
        decisions = sorted(f["value"] for f in ans["facts"] if f["field"] == "decision")
        self.assertEqual(len(decisions), 2)
        self.assertTrue(all(f["freshness"] == "fresh" for f in ans["facts"]))

    def test_missing_source_is_reported_not_invented(self):
        code, ans = self.about("notify")
        self.assertEqual(code, 0)
        self.assertEqual(ans["unresolved"], ["catalog"])
        self.assertFalse(any(f["source"] == "catalog" for f in ans["facts"]))

    def test_unknown_subject_is_an_error_not_an_empty_answer(self):
        r = run("about", "billing", cwd=self.tmp)
        self.assertEqual(r.returncode, 3)
        self.assertIn("nothing in the snapshot knows 'billing'", r.stdout + r.stderr)

    def test_unsupported_field_is_explicit(self):
        r = run("about", "checkout", "--field", "on-call", cwd=self.tmp)
        self.assertEqual(r.returncode, 4)
        self.assertIn("unsupported", r.stdout + r.stderr)

    def test_url_citation_is_unverifiable_not_fresh(self):
        code, ans = self.about("search")
        adr = [f for f in ans["facts"] if f["source"] == "adr"][0]
        states = {c["target"]: c["freshness"] for c in adr["cites"]}
        self.assertEqual(states["https://example.com/search-vendor/limits"], "unverifiable")
        self.assertEqual(states["code/search/rebuild.py"], "fresh")
        self.assertEqual(adr["freshness"], "unverifiable")

    def test_drift_is_detected_per_record(self):
        (self.src / "code/checkout/retry.py").write_text("MAX_ATTEMPTS = 5\n")
        (self.src / "code/notify/templates.py").unlink()
        cat = json.loads((self.src / "catalog.json").read_text())
        cat["services"][1]["owner"] = "platform-team"  # search changes owner
        (self.src / "catalog.json").write_text(json.dumps(cat, indent=2))

        _, checkout = self.about("checkout")
        fresh = {(f["field"], f["value"]): f["freshness"] for f in checkout["facts"]}
        self.assertEqual(fresh[("owner", "payments-team")], "fresh")  # its entry did not change
        adr1 = [f for f in checkout["facts"] if "ADR-0001" in f["value"]][0]
        self.assertEqual(adr1["freshness"], "stale")
        adr3 = [f for f in checkout["facts"] if "ADR-0003" in f["value"]][0]
        self.assertEqual(adr3["freshness"], "missing")

        _, search = self.about("search")
        owner = [f for f in search["facts"] if f["field"] == "owner"][0]
        self.assertEqual(owner["value"], "discovery-team")  # what the source said at build time
        self.assertEqual(owner["freshness"], "stale")  # the snapshot is old; we say so

    def test_deleted_record_is_missing_not_fresh(self):
        cat = json.loads((self.src / "catalog.json").read_text())
        cat["services"] = [s for s in cat["services"] if s["name"] != "recommendations"]
        (self.src / "catalog.json").write_text(json.dumps(cat))
        (self.src / "adr/0002-search-index-rebuild.md").unlink()
        _, recs = self.about("recommendations")
        self.assertTrue(all(f["freshness"] == "missing" for f in recs["facts"]))
        _, search = self.about("search")
        adr = [f for f in search["facts"] if f["source"] == "adr"][0]
        self.assertEqual(adr["freshness"], "missing")

    def test_citation_missing_at_build_is_never_fresh(self):
        (self.src / "adr/0004-ghost.md").write_text(
            "---\nid: ADR-0004\ntitle: Cites a file that never existed\nstatus: proposed\n"
            "services: search\ncites: code/search/ghost.py\n---\n")
        run("build", "--sources", str(self.src), cwd=self.tmp)
        _, search = self.about("search")
        ghost = [f for f in search["facts"] if "ADR-0004" in f["value"]][0]
        self.assertEqual(ghost["freshness"], "missing")
        (self.src / "code/search/ghost.py").write_text("appeared later\n")
        _, search = self.about("search")
        ghost = [f for f in search["facts"] if "ADR-0004" in f["value"]][0]
        self.assertEqual(ghost["freshness"], "stale")  # never fresh: we never hashed it

    def edit_catalog(self, change):
        cat = json.loads((self.src / "catalog.json").read_text())
        change(cat["services"])
        (self.src / "catalog.json").write_text(json.dumps(cat))

    def test_duplicate_catalog_names_are_refused_not_hashed_wrong(self):
        self.edit_catalog(lambda s: s.append({"name": "checkout", "owner": "rogue-team"}))
        r = run("build", "--sources", str(self.src), cwd=self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("duplicate service name 'checkout'", r.stderr)
        _, checkout = self.about("checkout")  # old snapshot kept, and it now reads stale
        owner = [f for f in checkout["facts"] if f["field"] == "owner"][0]
        self.assertEqual(owner["freshness"], "stale")

    def test_known_field_missing_for_subject_is_unresolved(self):
        code, ans = self.about("notify", "--field", "owner")
        self.assertEqual((code, ans["facts"], ans["unresolved"]), (0, [], ["catalog"]))

    def test_unsupported_field_wins_over_unknown_subject(self):
        self.assertEqual(run("about", "billing", "--field", "on-call", cwd=self.tmp).returncode, 4)

    def test_records_added_after_build_are_flagged(self):
        (self.src / "adr/0009-billing.md").write_text(
            "---\nid: ADR-0009\ntitle: New\nstatus: proposed\nservices: checkout\n---\n")
        r = run("about", "checkout", cwd=self.tmp)
        self.assertIn("adr/0009-billing.md is new or changed since build", r.stderr)
        code, ans = self.about("checkout")
        self.assertEqual(ans["not_in_snapshot"], ["adr/0009-billing.md"])
        self.assertEqual(run("check", cwd=self.tmp).returncode, 1)
        r = run("about", "billing", cwd=self.tmp)
        self.assertIn("nothing in the snapshot knows", r.stdout)

    def test_corrupt_source_after_build_reads_stale_not_crash(self):
        (self.src / "catalog.json").write_text("{")
        code, ans = self.about("checkout")
        self.assertEqual(code, 0)
        states = {f["source"]: f["freshness"] for f in ans["facts"]}
        self.assertEqual(states["catalog"], "stale")
        self.assertEqual(run("check", cwd=self.tmp).returncode, 1)

    def test_bad_adr_fails_build_with_a_message(self):
        (self.src / "adr/0005-bad.md").write_text("no header here\n")
        r = run("build", "--sources", str(self.src), cwd=self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("adr/0005-bad.md: missing '---' header", r.stderr)

    def test_citations_outside_the_sources_are_unverifiable(self):
        (self.src / "adr/0006-escape.md").write_text(
            "---\nid: ADR-0006\ntitle: Escapes\nstatus: proposed\nservices: search\n"
            "cites: /etc/hosts, ../outside.txt\n---\n")
        run("build", "--sources", str(self.src), cwd=self.tmp)
        _, search = self.about("search")
        adr = [f for f in search["facts"] if "ADR-0006" in f["value"]][0]
        self.assertEqual({c["freshness"] for c in adr["cites"]}, {"unverifiable"})

    def test_check_exit_code_gates_on_drift(self):
        self.assertEqual(run("check", cwd=self.tmp).returncode, 0)
        (self.src / "code/search/rebuild.py").write_text("BATCH_SIZE = 50\n")
        self.assertEqual(run("check", cwd=self.tmp).returncode, 1)

    def test_record_without_facts_that_changes_is_reported(self):
        self.edit_catalog(lambda s: s.append({"name": "latent"}))
        run("build", "--sources", str(self.src), cwd=self.tmp)
        self.edit_catalog(lambda s: s[-1].update(owner="team"))
        r = run("check", cwd=self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("catalog.json#latent is new or changed", r.stderr)

    def test_unreadable_source_after_build_is_stale_not_a_traceback(self):
        (self.src / "catalog.json").unlink()
        (self.src / "catalog.json").mkdir()
        code, ans = self.about("checkout")
        self.assertEqual(code, 0)
        self.assertIn("stale", {f["freshness"] for f in ans["facts"] if f["source"] == "catalog"})

    def test_header_line_without_colon_fails_build(self):
        (self.src / "adr/0007-typo.md").write_text(
            "---\nid: ADR-0007\ntitle: Typo\nstatus: proposed\nservices checkout\n---\n")
        r = run("build", "--sources", str(self.src), cwd=self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("header line without ':'", r.stderr)

    def test_wrong_sources_root_fails_build_and_keeps_snapshot(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        r = run("build", "--sources", str(empty), cwd=self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.about("checkout")[0], 0)

    def test_subject_is_trimmed_like_the_sources(self):
        self.assertEqual(self.about(" checkout ")[0], 0)

    def test_cite_that_becomes_a_symlink_outside_is_not_fresh(self):
        outside = self.tmp / "elsewhere.py"
        target = self.src / "code/checkout/retry.py"
        outside.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(outside)
        _, checkout = self.about("checkout")
        adr1 = [f for f in checkout["facts"] if "ADR-0001" in f["value"]][0]
        self.assertEqual(adr1["freshness"], "stale")
        self.assertEqual(run("check", cwd=self.tmp).returncode, 1)  # can't slip past the gate

    def test_changed_content_behind_outside_symlink_fails_check(self):
        outside = self.tmp / "elsewhere.py"
        outside.write_text("MAX_ATTEMPTS = 99\n")
        target = self.src / "code/checkout/retry.py"
        target.unlink()
        target.symlink_to(outside)
        self.assertEqual(run("check", cwd=self.tmp).returncode, 1)

    def test_record_symlinked_outside_is_refused_and_never_fresh(self):
        adr = self.src / "adr/0001-retry-card-payments.md"
        outside = self.tmp / "adr-copy.md"
        outside.write_bytes(adr.read_bytes())
        adr.unlink()
        adr.symlink_to(outside)
        _, checkout = self.about("checkout")
        adr1 = [f for f in checkout["facts"] if "ADR-0001" in f["value"]][0]
        self.assertNotEqual(adr1["freshness"], "fresh")
        r = run("build", "--sources", str(self.src), cwd=self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("resolves outside the sources root", r.stderr)

    def test_explain_shows_the_chain(self):
        _, ans = self.about("checkout")
        fid = [f for f in ans["facts"] if "ADR-0001" in f["value"]][0]["id"]
        r = run("explain", fid, cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        for needle in ("adr/0001-retry-card-payments.md", "sha256", "code/checkout/retry.py", "adr-reader"):
            self.assertIn(needle, r.stdout)

    def test_snapshot_is_disposable(self):
        _, before = self.about("checkout")
        shutil.rmtree(self.tmp / ".wherefrom")
        run("build", "--sources", str(self.src), cwd=self.tmp)
        _, after = self.about("checkout")
        self.assertEqual(before["facts"], after["facts"])


if __name__ == "__main__":
    unittest.main()
