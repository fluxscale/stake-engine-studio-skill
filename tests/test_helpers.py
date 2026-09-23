import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

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
    def test_replay_search_finds_both_collections(self):
        pages = json.loads(docs.INDEX.read_text())["pages"]
        found = docs.search(pages, "replay")
        self.assertEqual({p["collection"] for p in found}, {"studio", "source"})
        self.assertIn("/docs/approval-guidelines/game-replay-requirements", [p["route"] for p in found])

    def test_collection_filter(self):
        pages = json.loads(docs.INDEX.read_text())["pages"]
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
        self.assertEqual(result["command"][3], query)
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


class MathTests(unittest.TestCase):
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
        (self.root / "weights.csv").write_text("0,1,0\n1,1,190\n2,0,99999\n")
        mode = math.inspect(self.root)["modes"][0]
        self.assertEqual(mode["max_recorded_payout_hundredths"], 99999)
        self.assertEqual(mode["max_reachable_payout_hundredths"], 190)
        self.assertEqual(mode["zero_weight_outcomes"], 1)

    def test_invalid_tables(self):
        for content in ["", "id,weight,payout\n", "1,0,5\n", "1,-1,5\n", "1,1,1.5\n", "1,1,5,9\n", "1,1,5\n1,1,5\n", f"1,{2**64},5\n"]:
            with self.subTest(content=content):
                (self.root / "weights.csv").write_text(content)
                with self.assertRaises(math.Invalid):
                    math.inspect(self.root)

    def test_uint64_above_sqlite_signed_range(self):
        value = 2**64 - 1
        (self.root / "weights.csv").write_text(f"{value},1,{value}\n")
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
            target.write_text("1,1,190\n")
            link = self.root / "escape.csv"
            link.symlink_to(target)
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
        try:
            import zstandard
        except ImportError:
            self.skipTest("Optional zstandard dependency not installed")
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
        try:
            import zstandard
        except ImportError:
            self.skipTest("Optional zstandard dependency not installed")
        payload = (self.record(0, 0) + self.record(1, 190)).encode()
        data = zstandard.ZstdCompressor(write_checksum=True).compress(payload)
        (self.root / "books.jsonl.zst").write_bytes(data[:-4])
        with self.assertRaisesRegex(math.Invalid, "Incomplete"):
            math.inspect(self.root, True)

    def test_compressed_records_across_frame_boundaries(self):
        try:
            import zstandard
        except ImportError:
            self.skipTest("Optional zstandard dependency not installed")
        payload = (self.record(0, 0) + self.record(1, 190)).encode().rstrip(b"\n")
        # A JSON line can span frames, and a final newline is optional.
        compressor = zstandard.ZstdCompressor(write_checksum=True)
        (self.root / "books.jsonl.zst").write_bytes(compressor.compress(payload[:17]) + compressor.compress(payload[17:]))
        self.assertTrue(math.inspect(self.root, True)["modes"][0]["books_verified"])


if __name__ == "__main__":
    unittest.main()
