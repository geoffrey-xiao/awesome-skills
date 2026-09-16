from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "validate_release_inputs.py"
SPEC = importlib.util.spec_from_file_location("validate_release_inputs", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def write_skill(root: Path, name: str = "example-skill") -> None:
    (root / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Test skill for release validation.\n---\n\n# Test\n",
        encoding="utf-8",
    )


def finding_codes(result: dict) -> set[str]:
    return {item["code"] for item in result["findings"]}


class ValidatorTests(unittest.TestCase):
    def test_safe_skill_has_deterministic_publish_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root)
            (root / "references").mkdir()
            (root / "references" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (root / "skill-card.md").write_text("generated\n", encoding="utf-8")
            (root / ".clawhubignore").write_text("tests/\n", encoding="utf-8")

            first = validator.validate(str(root))
            second = validator.validate(str(root))

            self.assertEqual(first["status"], "pass")
            self.assertEqual([item["path"] for item in first["publish_files"]], ["SKILL.md", "references/guide.md"])
            self.assertEqual(first["fingerprint"], second["fingerprint"])
            self.assertIn("skill-card.md", {item["path"] for item in first["excluded_files"]})

    def test_expected_fingerprint_blocks_changed_contents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root)

            result = validator.validate(str(root), expected_fingerprint="0" * 64)

            self.assertEqual(result["status"], "fail")
            self.assertIn("fingerprint-mismatch", finding_codes(result))

    def test_directory_symlink_outside_root_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            write_skill(root)
            (root / "escape").symlink_to(Path(outside), target_is_directory=True)

            result = validator.validate(str(root))

            self.assertEqual(result["status"], "fail")
            self.assertIn("unsafe-symlink", finding_codes(result))

    def test_invalid_skill_name_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root, name="Invalid Name")

            result = validator.validate(str(root))

            self.assertEqual(result["status"], "fail")
            self.assertIn("invalid-skill-name", finding_codes(result))

    def test_multiline_description_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SKILL.md").write_text(
                "---\nname: example-skill\ndescription: |\n  A valid multiline description.\n---\n\n# Test\n",
                encoding="utf-8",
            )

            result = validator.validate(str(root))

            self.assertEqual(result["status"], "pass")

    def test_ignore_rule_excludes_release_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root)
            (root / "notes.txt").write_text("private notes\n", encoding="utf-8")
            (root / ".clawhubignore").write_text("notes.txt\n", encoding="utf-8")

            result = validator.validate(str(root))

            self.assertNotIn("notes.txt", {item["path"] for item in result["publish_files"]})
            self.assertIn("notes.txt", {item["path"] for item in result["excluded_files"]})

    def test_secret_inside_archive_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root)
            token = b"npm_" + (b"A" * 24)
            with zipfile.ZipFile(root / "payload.zip", "w") as archive:
                archive.writestr("config.txt", token)

            result = validator.validate(str(root))

            self.assertEqual(result["status"], "fail")
            self.assertIn("possible-secret", finding_codes(result))

    def test_archive_path_traversal_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root)
            with zipfile.ZipFile(root / "payload.zip", "w") as archive:
                archive.writestr("../escape.txt", "not safe")

            result = validator.validate(str(root))

            self.assertEqual(result["status"], "fail")
            self.assertIn("unsafe-archive-path", finding_codes(result))

    def test_total_publish_size_limit_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root)
            (root / "extra.txt").write_text("content", encoding="utf-8")

            with mock.patch.object(validator, "MAX_TOTAL_BYTES", 8):
                result = validator.validate(str(root))

            self.assertEqual(result["status"], "fail")
            self.assertIn("total-size-limit", finding_codes(result))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is unavailable")
    def test_special_file_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root)
            os.mkfifo(root / "unexpected.pipe")

            result = validator.validate(str(root))

            self.assertEqual(result["status"], "fail")
            self.assertIn("special-file", finding_codes(result))

    def test_missing_plugin_entrypoint_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "openclaw.plugin.json").write_text(
                '{"name":"example-plugin","version":"1.0.0","entry":"./dist/index.js"}',
                encoding="utf-8",
            )
            (root / "package.json").write_text(
                '{"name":"example-plugin","version":"1.0.0","openclaw":{},"main":"./dist/index.js"}',
                encoding="utf-8",
            )

            result = validator.validate(str(root))

            self.assertEqual(result["status"], "fail")
            self.assertTrue({"missing-entrypoint", "missing-plugin-path"}.issubset(finding_codes(result)))

    def test_bare_plugin_entrypoint_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text(
                '{"name":"example-plugin","version":"1.0.0","openclaw":{},"main":"index.js"}',
                encoding="utf-8",
            )

            result = validator.validate(str(root))

            self.assertEqual(result["status"], "fail")
            self.assertIn("missing-entrypoint", finding_codes(result))

    def test_plugin_lifecycle_and_non_registry_dependency_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dist").mkdir()
            (root / "dist" / "index.js").write_text("export {};\n", encoding="utf-8")
            (root / "openclaw.plugin.json").write_text(
                '{"name":"example-plugin","version":"1.0.0","entry":"./dist/index.js"}',
                encoding="utf-8",
            )
            (root / "package.json").write_text(
                '{"name":"example-plugin","version":"1.0.0","openclaw":{},'
                '"main":"./dist/index.js","scripts":{"postinstall":"node setup.js"},'
                '"dependencies":{"example":"git+https://example.invalid/repo.git"}}',
                encoding="utf-8",
            )

            result = validator.validate(str(root))

            self.assertEqual(result["status"], "warn")
            self.assertTrue({"lifecycle-script", "non-registry-dependency"}.issubset(finding_codes(result)))

    def test_skill_and_plugin_markers_are_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root)
            (root / "openclaw.plugin.json").write_text("{}", encoding="utf-8")

            result = validator.validate(str(root))

            self.assertEqual(result["status"], "fail")
            self.assertIn("ambiguous-type", finding_codes(result))


if __name__ == "__main__":
    unittest.main()
