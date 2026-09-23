import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/stake-engine-studio/scripts"


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


docs = module("docs")
issues = module("issues")
math = module("inspect_math")


class NavigationTests(unittest.TestCase):
    def test_exact_page_ranking_and_whole_words(self):
        pages = json.loads(docs.INDEX.read_text(encoding="utf-8"))["pages"]
        self.assertEqual(docs.search(pages, "play")[0]["route"], "/docs/api/play")
        self.assertIn("/docs/rgs/wallet", [p["route"] for p in docs.search(pages, "wallet")[:3]])
        self.assertIn("/docs/rgs/wallet", [p["route"] for p in docs.search(pages, "wallet play")[:3]])
        self.assertEqual(docs.search([{"route": "/replay", "title": "Display replay"}], "play"), [])

    def test_word_prefix_matches_rank_below_whole_words(self):
        pages = json.loads(docs.INDEX.read_text(encoding="utf-8"))["pages"]
        self.assertIn("/docs/api/authenticate", [p["route"] for p in docs.search(pages, "auth")[:5]])
        exact = {"collection": "source", "route": "/docs/auth", "title": "Auth"}
        prefix = {"collection": "source", "route": "/docs/authenticate", "title": "Authenticate"}
        self.assertEqual(docs.search([prefix, exact], "auth"), [exact, prefix])
        self.assertEqual(docs.search([prefix], "au"), [])

    def test_punctuation_only_query_is_usage_error(self):
        with patch("sys.stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as raised:
                docs.main(["search", "!!!"])
        self.assertEqual(raised.exception.code, 2)

    def test_fetch_resolves_symbolic_ref_before_content(self):
        page = {"collection": "source", "path": "src/routes/docs/api/play/+page.svx"}
        commit = "a" * 40
        with patch.object(docs, "read_url", side_effect=[json.dumps({"sha": commit}), "# Play"]) as fetch:
            result = docs.fetch_source(page, "feature/docs")
        self.assertEqual(result["fetched_commit"], commit)
        self.assertEqual(result["requested_ref"], "feature/docs")
        self.assertIn("/commits/feature%2Fdocs", fetch.call_args_list[0].args[0])
        self.assertIn("/" + commit + "/", fetch.call_args_list[1].args[0])
        self.assertIn(commit, result["citation_url"])

    def test_fetch_locked_ref_uses_recorded_revision(self):
        page = {"collection": "source", "path": "src/routes/docs/api/play/+page.svx"}
        commit = next(r["commit"] for r in json.loads(docs.LOCK.read_text(encoding="utf-8"))["repositories"] if r["name"] == "docs")
        with patch.object(docs, "read_url", return_value="# Play") as fetch:
            result = docs.fetch_source(page, "locked")
        self.assertEqual(result["fetched_commit"], commit)
        self.assertEqual(fetch.call_count, 1)

    def test_show_fetch_reports_provenance(self):
        with patch.object(docs, "fetch_source", return_value={"content": "# Play", "fetched_commit": "a" * 40}):
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(docs.main(["show", "/docs/api/play", "--collection", "source", "--fetch"]), 0)
        self.assertIn('"fetched_commit": "' + "a" * 40, out.getvalue())
        self.assertIn("# Play", out.getvalue())

    def test_fetch_size_and_encoding_failures(self):
        for content in [b"a" * 2_000_001, b"\xff"]:
            with self.subTest(size=len(content)):
                with patch.object(docs, "urlopen", return_value=io.BytesIO(content)):
                    with self.assertRaises(ValueError):
                        docs.read_url("https://raw.githubusercontent.com/engineio/docs/main/page")

    def test_fetch_http_error_is_visible(self):
        error = HTTPError("https://api.github.com", 403, "rate limited", {}, None)
        with patch.object(docs, "urlopen", side_effect=error), patch.object(docs.subprocess, "run", side_effect=FileNotFoundError("gh unavailable")):
            with patch("sys.stderr", new_callable=io.StringIO) as out:
                self.assertEqual(docs.main(["show", "/docs/api/play", "--collection", "source", "--fetch"]), 1)
        self.assertIn("403", out.getvalue())

    def test_rate_limit_can_use_existing_gh_authentication(self):
        error = HTTPError("https://api.github.com", 403, "rate limited", {}, None)
        result = subprocess.CompletedProcess([], 0, json.dumps({"sha": "b" * 40}), "")
        with patch.object(docs, "read_url", side_effect=error):
            with patch.object(docs.subprocess, "run", return_value=result) as run:
                self.assertEqual(docs.resolve_commit("main"), "b" * 40)
        self.assertEqual(run.call_args.args[0], ["gh", "api", "repos/engineio/docs/commits/main"])

    def test_missing_ref_does_not_retry_or_silently_use_lock(self):
        error = HTTPError("https://api.github.com", 404, "not found", {}, None)
        with patch.object(docs, "read_url", side_effect=error):
            with patch.object(docs.subprocess, "run", side_effect=AssertionError("unexpected fallback")):
                with self.assertRaises(HTTPError):
                    docs.resolve_commit("missing-ref")

    def test_replay_search_finds_both_collections(self):
        pages = json.loads(docs.INDEX.read_text(encoding="utf-8"))["pages"]
        found = docs.search(pages, "replay")
        self.assertEqual({p["collection"] for p in found}, {"studio", "source"})
        self.assertIn("/docs/approval-guidelines/game-replay-requirements", [p["route"] for p in found])

    def test_collection_filter(self):
        pages = json.loads(docs.INDEX.read_text(encoding="utf-8"))["pages"]
        self.assertTrue(all(p["collection"] == "source" for p in docs.search(pages, "replay", "source")))

    def test_ambiguous_route_needs_collection(self):
        with patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(docs.main(["show", "/docs"]), 1)

    def test_studio_cannot_be_misreported_as_fetched(self):
        with self.assertRaisesRegex(ValueError, "rendered browser"):
            docs.fetch_source({"collection": "studio"})

    def test_preview_makes_no_network_request(self):
        with patch.object(docs, "urlopen", side_effect=AssertionError("network")):
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(docs.main(["search", "RGS"]), 0)
                self.assertGreater(json.loads(out.getvalue())["total"], 0)


class IssueTests(unittest.TestCase):
    def test_repo_and_organization_scope(self):
        scoped = issues.make_search("payout", ["math-sdk"], "issues")
        self.assertIn("engineio/math-sdk", scoped["command"])
        self.assertNotIn("--state", scoped["command"])
        broad = issues.make_search("replay", [], "prs")
        self.assertIn("--owner", broad["command"])
        self.assertIn("engineio", broad["command"])

    def test_query_is_one_argument_not_shell_code(self):
        query = '"payout mismatch"; $(touch should-not-exist)'
        result = issues.make_search(query, ["math-sdk"], "issues")
        self.assertEqual(result["command"][-2:], ["--", query])
        self.assertIn("%24", result["url"])

    def test_default_is_preview_only(self):
        with patch.object(issues.subprocess, "run", side_effect=AssertionError("execution")):
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(issues.main(["replay"]), 0)
                report = json.loads(out.getvalue())
                self.assertFalse(report["executed"])
                self.assertEqual(len(report["searches"]), 2)

    def test_network_failure_is_not_empty_success(self):
        with patch.object(issues.subprocess, "run", side_effect=FileNotFoundError("gh unavailable")):
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(issues.main(["replay", "--run"]), 1)
                self.assertIn("error", json.loads(out.getvalue())["searches"][0])

    def test_results_flag_possible_truncation(self):
        result = subprocess.CompletedProcess([], 0, '[{"number":1}]', '')
        with patch.object(issues.subprocess, "run", return_value=result):
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(issues.main(["replay", "--kind", "issues", "--run", "--limit", "1"]), 0)
                self.assertTrue(json.loads(out.getvalue())["searches"][0]["possibly_truncated"])

    def test_leading_negation_is_supported_as_query_not_option(self):
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            self.assertEqual(issues.main(["--repo", "math-sdk", "--", "-label:bug payout"]), 0)
        command = json.loads(out.getvalue())["searches"][0]["command"]
        self.assertEqual(command[-2:], ["--", "-label:bug payout"])

    def test_execution_error_branches_are_visible(self):
        failures = [subprocess.TimeoutExpired("gh", 45), subprocess.CalledProcessError(1, "gh", stderr="rate limited")]
        for failure in failures:
            with self.subTest(error=type(failure).__name__):
                with patch.object(issues.subprocess, "run", side_effect=failure):
                    with patch("sys.stdout", new_callable=io.StringIO) as out:
                        self.assertEqual(issues.main(["replay", "--run"]), 1)
                self.assertTrue(json.loads(out.getvalue())["searches"][0]["error"])
        for output in ["invalid json", "{}"]:
            with patch.object(issues.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, output, "")):
                with patch("sys.stdout", new_callable=io.StringIO) as out:
                    self.assertEqual(issues.main(["replay", "--run"]), 1)
            self.assertIn("error", json.loads(out.getvalue())["searches"][0])


class MathTests(unittest.TestCase):
    def zstandard(self):
        try:
            import zstandard
            return zstandard
        except ImportError:
            if os.environ.get("CI"):
                self.fail("CI must install zstandard; compressed-book tests cannot be skipped")
            self.skipTest("Optional zstandard dependency not installed")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = {"modes": [{"name": "base", "cost": 1, "events": "books.jsonl.zst", "weights": "weights.csv"}]}
        self.write_manifest()
        (self.root / "weights.csv").write_text("0,1,0\n1,1,190\n", encoding="utf-8")
        (self.root / "books.jsonl.zst").write_bytes(b"not inspected without --books")

    def write_manifest(self):
        (self.root / "index.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def table_db(self):
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        math.load_table(self.root / "weights.csv", db)
        return db

    def record(self, identifier, payout, **extra):
        return json.dumps({"id": identifier, "payoutMultiplier": payout, "events": [], **extra}) + "\n"

    def test_weighted_statistics_and_explicit_partial_scope(self):
        report = math.inspect(self.root)["modes"][0]
        self.assertEqual(report["rtp_fraction"], "0.95")
        self.assertEqual(report["nonzero_hit_probability"], "0.5")
        self.assertFalse(report["books_verified"])

    def test_mode_cost_is_not_applied_twice(self):
        self.manifest["modes"][0]["cost"] = 100
        self.write_manifest()
        self.assertEqual(math.inspect(self.root)["modes"][0]["rtp_fraction"], "0.0095")

    def test_zero_weight_cap_is_not_reachable(self):
        (self.root / "weights.csv").write_text("0,1,0\n1,1,190\n2,0,99999\n", encoding="utf-8")
        mode = math.inspect(self.root)["modes"][0]
        self.assertEqual(mode["max_recorded_payout_hundredths"], 99999)
        self.assertEqual(mode["max_reachable_payout_hundredths"], 190)
        self.assertEqual(mode["zero_weight_outcomes"], 1)

    def test_invalid_tables(self):
        for content in ["", "id,weight,payout\n", "1,0,5\n", "1,-1,5\n", "1,1,1.5\n", "1,1,5,9\n", "1,1,5\n1,1,5\n", f"1,{2**64},5\n"]:
            with self.subTest(content=content):
                (self.root / "weights.csv").write_text(content, encoding="utf-8")
                with self.assertRaises(math.Invalid):
                    math.inspect(self.root)

    def test_uint64_above_sqlite_signed_range(self):
        value = 2**64 - 1
        (self.root / "weights.csv").write_text(f"{value},1,{value}\n", encoding="utf-8")
        db = self.table_db()
        self.assertEqual(math.verify_lines([self.record(value, value)], db), 1)

    def test_invalid_mode_costs(self):
        for value in [0, -1, True, "1", float("nan"), float("inf")]:
            with self.subTest(value=value):
                self.manifest["modes"][0]["cost"] = value
                self.write_manifest()
                with self.assertRaises(math.Invalid):
                    math.inspect(self.root)

    def test_duplicate_mode_names(self):
        self.manifest["modes"].append(self.manifest["modes"][0].copy())
        self.write_manifest()
        with self.assertRaisesRegex(math.Invalid, "unique"):
            math.inspect(self.root)

    def test_path_traversal_is_rejected(self):
        self.manifest["modes"][0]["weights"] = "../outside.csv"
        self.write_manifest()
        with self.assertRaisesRegex(math.Invalid, "escapes"):
            math.inspect(self.root)

    def test_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "weights.csv"
            target.write_text("1,1,190\n", encoding="utf-8")
            link = self.root / "escape.csv"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(math.Invalid, "escapes"):
                math.artifact(self.root, "escape.csv", ".csv")

    def test_id_matching_does_not_require_sort_order(self):
        db = self.table_db()
        self.assertEqual(math.verify_lines([self.record(1, 190), self.record(0, 0)], db), 2)

    def test_payout_mismatch(self):
        db = self.table_db()
        with self.assertRaisesRegex(math.Invalid, "Payout mismatch"):
            math.verify_lines([self.record(0, 0), self.record(1, 191)], db)

    def test_missing_book_id(self):
        db = self.table_db()
        with self.assertRaisesRegex(math.Invalid, "no book record"):
            math.verify_lines([self.record(0, 0)], db)

    def test_extra_book_id(self):
        db = self.table_db()
        with self.assertRaisesRegex(math.Invalid, "no CSV row"):
            math.verify_lines([self.record(2, 0)], db)

    def test_duplicate_book_id(self):
        db = self.table_db()
        with self.assertRaisesRegex(math.Invalid, "Duplicate book"):
            math.verify_lines([self.record(0, 0), self.record(0, 0)], db)

    def test_invalid_record_types(self):
        for record in ["\n", "{}\n", "[]\n", self.record(True, 0), self.record("0", 0), self.record(0, 0.0), self.record(0, 0, events=[3])]:
            with self.subTest(record=record):
                db = self.table_db()
                with self.assertRaises(math.Invalid):
                    math.verify_lines([record], db)

    def test_full_compressed_cli_and_corrupt_stream(self):
        zstandard = self.zstandard()
        events = self.root / "books.jsonl.zst"
        compressor = zstandard.ZstdCompressor()
        # Two frames also exercise production exports concatenated from batches.
        events.write_bytes(compressor.compress(self.record(0, 0).encode()) + compressor.compress(self.record(1, 190).encode()))
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        result = subprocess.run([sys.executable, str(SCRIPTS / "inspect_math.py"), str(self.root), "--books"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["modes"][0]["books_verified"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        events.write_bytes(b"invalid zstd")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            self.assertEqual(math.main([str(self.root), "--books"]), 1)
            self.assertFalse(json.loads(out.getvalue())["ok"])

    def test_truncated_checksum_is_rejected_even_with_complete_records(self):
        zstandard = self.zstandard()
        payload = (self.record(0, 0) + self.record(1, 190)).encode()
        data = zstandard.ZstdCompressor(write_checksum=True).compress(payload)
        (self.root / "books.jsonl.zst").write_bytes(data[:-4])
        with self.assertRaisesRegex(math.Invalid, "Incomplete"):
            math.inspect(self.root, True)

    def test_compressed_records_across_frame_boundaries(self):
        zstandard = self.zstandard()
        payload = (self.record(0, 0) + self.record(1, 190)).encode().rstrip(b"\n")
        # A JSON line can span frames, and a final newline is optional.
        compressor = zstandard.ZstdCompressor(write_checksum=True)
        (self.root / "books.jsonl.zst").write_bytes(compressor.compress(payload[:17]) + compressor.compress(payload[17:]))
        self.assertTrue(math.inspect(self.root, True)["modes"][0]["books_verified"])

    def test_duplicate_record_and_nested_keys_are_rejected(self):
        records = [
            '{"id":0,"payoutMultiplier":999,"payoutMultiplier":0,"events":[]}',
            '{"id":999,"id":0,"payoutMultiplier":0,"events":[]}',
            '{"id":0,"payoutMultiplier":0,"events":[],"events":[]}',
            '{"id":0,"payoutMultiplier":0,"events":[{"amount":999,"amount":0}]}',
        ]
        for record in records:
            with self.subTest(record=record):
                with self.assertRaisesRegex(math.Invalid, "Duplicate JSON key"):
                    math.verify_lines([record], self.table_db())

    def test_duplicate_manifest_key_is_rejected(self):
        (self.root / "index.json").write_text('{"modes":[],"modes":' + json.dumps(self.manifest["modes"]) + '}', encoding="utf-8")
        with self.assertRaisesRegex(math.Invalid, "Duplicate JSON key"):
            math.inspect(self.root)

    def test_shared_artifacts_warn_without_inventing_approval_rule(self):
        self.manifest["modes"].append({**self.manifest["modes"][0], "name": "bonus", "cost": 100})
        self.write_manifest()
        report = math.inspect(self.root)
        self.assertTrue(report["ok"])
        self.assertEqual(len(report["warnings"]), 2)
        self.assertTrue(all(w["modes"] == ["base", "bonus"] for w in report["warnings"]))

    def test_standard_deviation_units_and_cost_normalization(self):
        self.manifest["modes"][0]["cost"] = 100
        self.write_manifest()
        result = math.inspect(self.root)["modes"][0]
        self.assertEqual(result["payout_variance_base_bets_squared"], "0.9025")
        self.assertEqual(result["payout_std_dev_base_bets"], "0.95")
        self.assertEqual(result["payout_std_dev_per_mode_cost"], "0.0095")
        self.assertEqual(result["max_reachable_payout_base_bets"], "1.9")

    def test_constant_large_payout_has_zero_variance(self):
        (self.root / "weights.csv").write_text(f"0,1,{2**64-1}\n1,2,{2**64-1}\n", encoding="utf-8")
        self.assertEqual(math.inspect(self.root)["modes"][0]["payout_std_dev_base_bets"], "0")

    def test_encoding_and_blank_line_diagnostics(self):
        for text, message in [("\ufeff0,1,0\n", "UTF-8 BOM"), ("0,1,0\n\n", "blank CSV row")]:
            (self.root / "weights.csv").write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(math.Invalid, message):
                math.inspect(self.root)
        (self.root / "weights.csv").write_text("0,1,0\n", encoding="utf-8")
        for line, message in [(b"\xff", "Book line 1: not UTF-8"), (b"\n", "blank JSONL record")]:
            with self.assertRaisesRegex(math.Invalid, message):
                math.verify_lines([line], self.table_db())

    def test_internal_error_has_distinct_exit_and_kind(self):
        with patch.object(math, "inspect", side_effect=TypeError("helper bug")):
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(math.main([str(self.root)]), 3)
        self.assertEqual(json.loads(out.getvalue())["kind"], "internal_error")
        with patch.object(math, "inspect", side_effect=math.Invalid("bad book")):
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(math.main([str(self.root)]), 1)
        self.assertEqual(json.loads(out.getvalue())["kind"], "invalid")

    def test_large_utf8_record_crosses_compressed_chunks(self):
        import random
        zstandard = self.zstandard()
        payload = (self.record(0, 0, events=[{"data": random.Random(0).randbytes(100_000).hex(), "label": "勝利"}]) + self.record(1, 190)).encode("utf-8")
        compressed = zstandard.ZstdCompressor().compress(payload)
        self.assertGreater(len(compressed), 16_384)
        (self.root / "books.jsonl.zst").write_bytes(compressed)
        self.assertTrue(math.inspect(self.root, True)["modes"][0]["books_verified"])


if __name__ == "__main__":
    unittest.main()
