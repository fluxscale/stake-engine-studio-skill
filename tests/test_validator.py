import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate", ROOT / "scripts/validate.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Explicit public inputs only: no Git metadata, audit directory, or venv.
        for file in [*ROOT.glob("*.md"), ROOT / "LICENSE"]:
            shutil.copy2(file, self.root / file.name)
        for directory in ("skills", "scripts"):
            shutil.copytree(ROOT / directory, self.root / directory, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (self.root / "tests").mkdir()
        shutil.copy2(ROOT / "tests/scenarios.md", self.root / "tests/scenarios.md")
        self.skill = self.root / "skills/stake-engine-studio"

    def check(self, expected, message=""):
        with patch("sys.stderr", new_callable=io.StringIO) as err, patch("sys.stdout", new_callable=io.StringIO):
            actual = validator.validate(self.root)
        self.assertEqual(actual, expected, err.getvalue())
        if message:
            self.assertIn(message, err.getvalue())

    def edit(self, path, before, after):
        content = path.read_text(encoding="utf-8")
        self.assertIn(before, content)
        path.write_text(content.replace(before, after), encoding="utf-8")

    def test_valid_copy_and_offline_default(self):
        with patch.object(validator.subprocess, "run", side_effect=AssertionError("network")):
            self.check(0)

    def test_broken_local_link(self):
        self.edit(self.skill / "SKILL.md", "references/rgs.md", "references/missing.md")
        self.check(1, "Broken local link")

    def test_link_outside_installed_bundle(self):
        with (self.skill / "SKILL.md").open("a", encoding="utf-8") as handle:
            handle.write("\n[External dependency](../../README.md)\n")
        self.check(1, "outside its bundle")

    def test_duplicate_route(self):
        file = self.skill / "references/docs-index.json"
        data = json.loads(file.read_text(encoding="utf-8"))
        data["pages"].append(data["pages"][0])
        file.write_text(json.dumps(data), encoding="utf-8")
        self.check(1, "Duplicate documentation identity")

    def test_stale_markdown_row(self):
        with (self.skill / "references/docs-index.md").open("a", encoding="utf-8") as handle:
            handle.write("\n| `/docs/removed` | [Removed](https://studio.engine.io/docs/removed) |\n")
        self.check(1, "Markdown index differs")

    def test_changed_markdown_title(self):
        self.edit(self.skill / "references/docs-index.md", "[API Documentation]", "[Wrong title]")
        self.check(1, "Markdown index differs")

    def test_readme_count_drift(self):
        self.edit(self.root / "README.md", "158 indexed routes", "159 indexed routes")
        self.check(1, "README route counts")

    def test_heading_count_drift(self):
        self.edit(self.skill / "references/docs-index.md", "(64 routes)", "(65 routes)")
        self.check(1, "Markdown index route counts")

    def test_baseline_date_drift(self):
        self.edit(self.skill / "references/sources.md", "2026-09-23", "2026-09-22")
        self.check(1, "Research baseline date differs")

    def test_lock_commit_validation(self):
        file = self.skill / "references/upstream-lock.json"
        data = json.loads(file.read_text(encoding="utf-8"))
        data["repositories"][0]["commit"] = "not-a-commit"
        file.write_text(json.dumps(data), encoding="utf-8")
        self.check(1, "Invalid repository evidence")

    def test_license_mismatch(self):
        (self.skill / "LICENSE").write_text("different", encoding="utf-8")
        self.check(1, "license must match")

    def test_malformed_frontmatter_reports_without_traceback(self):
        file = self.skill / "SKILL.md"
        for content in ("---\n---\n", "---\nscalar\n---\n", "---\n[\n---\n", "# no frontmatter"):
            with self.subTest(content=content):
                file.write_text(content, encoding="utf-8")
                self.check(1, "frontmatter")

    def test_name_length_limit(self):
        self.edit(self.skill / "SKILL.md", "name: stake-engine-studio", "name: " + "a" * 65)
        self.check(1, "at most 64")

    def test_missing_interface(self):
        (self.skill / "agents/openai.yaml").write_text("{}", encoding="utf-8")
        self.check(1, "interface mapping")

    def test_bad_inventory_type(self):
        (self.skill / "references/docs-index.json").write_text('{"pages": null}', encoding="utf-8")
        self.check(1, "nonempty pages array")

    def test_invalid_utf8_is_reported(self):
        (self.skill / "references/rgs.md").write_bytes(b"\xff")
        self.check(1, "Cannot read")

    def test_source_version_drift(self):
        self.edit(self.skill / "scripts/docs.py", 'VERSION = "1.0.0"', 'VERSION = "0.0.0"')
        self.check(1, "User-Agent version differs")


class OnlineValidationTests(unittest.TestCase):
    def test_tree_verifies_paths(self):
        result = subprocess.CompletedProcess([], 0, json.dumps({"tree": [{"path": "README.md", "type": "blob"}]}), "")
        with patch.object(validator.subprocess, "run", return_value=result) as run:
            self.assertEqual(validator.online_errors({("docs", "main", "README.md")}), [])
        self.assertEqual(run.call_args.args[0][0:2], ["gh", "api"])

    def test_missing_path_is_a_failure(self):
        result = subprocess.CompletedProcess([], 0, '{"tree": []}', "")
        with patch.object(validator.subprocess, "run", return_value=result):
            errors = validator.online_errors({("docs", "main", "missing.md")})
        self.assertIn("Missing upstream file", errors[0])

    def test_truncated_or_unavailable_tree_is_not_a_pass(self):
        result = subprocess.CompletedProcess([], 0, '{"truncated":true,"tree": []}', "")
        with patch.object(validator.subprocess, "run", return_value=result):
            self.assertTrue(validator.online_errors({("docs", "main", "README.md")}))
        with patch.object(validator.subprocess, "run", side_effect=FileNotFoundError("gh unavailable")):
            self.assertTrue(validator.online_errors({("docs", "main", "README.md")}))


if __name__ == "__main__":
    unittest.main()
