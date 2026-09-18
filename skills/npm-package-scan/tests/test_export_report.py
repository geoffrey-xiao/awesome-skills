from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "export_report.py"
SPEC = importlib.util.spec_from_file_location("export_report", MODULE_PATH)
assert SPEC and SPEC.loader
export_report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(export_report)


class ExportReportTests(unittest.TestCase):
    def sample(self) -> dict:
        return {
            "schemaVersion": "1.0",
            "scan": {
                "projectName": "demo/app",
                "packageManager": "npm",
                "scope": "workspace",
                "completedAt": "2026-09-18T12:34:00+08:00",
                "networkChecks": {"executed": False, "note": "Skipped"},
            },
            "dependencies": [{"name": "demo", "version": "1.0.0", "kind": "runtime", "path": "app"}],
            "findings": [{
                "id": "rule:demo",
                "ruleId": "rule",
                "severity": "Medium",
                "title": "Demo finding",
                "packagePath": "demo",
                "evidence": "lockfile",
                "confidence": "confirmed",
                "impact": "Example impact",
                "action": "Review it",
                "verify": "npm explain demo",
                "blastRadius": "runtime",
            }],
            "actions": ["Review it"],
        }

    def test_markdown_contains_required_context(self) -> None:
        report = export_report.render_markdown(self.sample())
        self.assertIn("Network checks executed: no", report)
        self.assertIn("Finding ID:** rule:demo", report)
        self.assertIn("npm explain demo", report)

    def test_default_output_is_project_and_timestamped(self) -> None:
        destination = export_report.default_output(self.sample(), "markdown", Path("reports"))
        self.assertEqual(destination.as_posix(), "reports/npm-package-scan-demo-app-20260918-1234.md")

    def test_load_model_adds_defaults_without_mutating_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "scan.json"
            source.write_text('{"scan":{"projectName":"demo"}}', encoding="utf-8")
            loaded = export_report.load_model(source)

            self.assertEqual(export_report.load_model(source)["scan"]["projectName"], "demo")
            self.assertEqual(loaded["schemaVersion"], "1.0")
            self.assertEqual(json.loads(source.read_text(encoding="utf-8")), {"scan": {"projectName": "demo"}})


if __name__ == "__main__":
    unittest.main()
