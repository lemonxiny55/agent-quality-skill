"""Verify Skill format, root layout, extraction and runtime shipped inside ZIP."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from scripts.validate_skill import validate

ROOT = Path(__file__).resolve().parent.parent


class Package(unittest.TestCase):
    def test_skill_format(self):
        self.assertTrue(validate(ROOT)["valid"])

    def test_invalid_name_and_reference_rejected(self):
        with tempfile.TemporaryDirectory(prefix="aq-format-") as temporary:
            skill = Path(temporary) / "agent-quality-skill"
            skill.mkdir()
            for name in ("SKILL.md", "LICENSE", "NOTICE"):
                shutil.copy2(ROOT / name, skill / name)
            for directory in ("references", "scripts"):
                shutil.copytree(ROOT / directory, skill / directory, ignore=shutil.ignore_patterns("__pycache__"))
            original = (skill / "SKILL.md").read_text(encoding="utf-8")
            (skill / "SKILL.md").write_text(original.replace("name: agent-quality-skill", "name: Uppercase"), encoding="utf-8")
            with self.assertRaises(ValueError):
                validate(skill)
            (skill / "SKILL.md").write_text(original + "\n[escaping](../secret.txt)\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                validate(skill)

    def test_zip_extract_and_runtime(self):
        with tempfile.TemporaryDirectory(prefix="aq-package-") as temporary:
            output = Path(temporary) / "candidate.zip"
            done = subprocess.run([sys.executable, str(ROOT / "scripts/package_skill.py"), "--out", str(output)], capture_output=True, text=True, encoding="utf-8", timeout=60)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            metadata = json.loads(done.stdout)
            self.assertTrue(metadata["rootSkill"])
            self.assertLess(metadata["bytes"], 50 * 1000 * 1000)
            destination = Path(temporary) / "agent-quality-skill"
            with zipfile.ZipFile(output) as archive:
                self.assertIn("SKILL.md", archive.namelist())
                names = archive.namelist()
                self.assertFalse(any("node_modules" in name or ".work/" in name for name in names))
                self.assertFalse(any(name.startswith("tests/") or name.startswith("evidence/") for name in names))
                self.assertIn("scripts/quality.py", names)
                self.assertIn("references/configuration.md", names)
                archive.extractall(destination)
            self.assertTrue(validate(destination)["valid"])
            smoke = subprocess.run([sys.executable, str(destination / "scripts/quality.py"), "--help"], capture_output=True, text=True, timeout=10)
            self.assertEqual(smoke.returncode, 0, smoke.stderr)


if __name__ == "__main__":
    unittest.main()
