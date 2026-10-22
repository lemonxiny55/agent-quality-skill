#!/usr/bin/env python3
"""Build and validate a deterministic, root-SKILL.md Agensi candidate ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

from delta_receipt import VERSION
from validate_skill import validate

ROOT = Path(__file__).resolve().parent.parent
FILES = ("SKILL.md", "README.md", "README.zh.md", "LICENSE", "NOTICE", ".gitignore", ".gitattributes", "pyproject.toml")
FOLDERS = ("scripts", "references", "examples")


def build(output):
    validate(ROOT)
    paths = [ROOT / name for name in FILES]
    paths += [p for directory in FOLDERS for p in (ROOT / directory).rglob("*")
              if p.is_file() and not any(part in ("node_modules", "__pycache__", ".git", ".agent-quality") for part in p.relative_to(ROOT).parts)
              and p.suffix != ".pyc"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(paths):
            if path.is_symlink():
                raise ValueError("symlinks are forbidden in candidate")
            data = path.read_bytes()
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        assert "SKILL.md" in names and len(names) == len(set(names))
        assert not any(n.startswith("/") or ".." in Path(n).parts or "\\" in n for n in names)
        assert archive.testzip() is None
        assert sum(i.file_size for i in archive.infolist()) < 50 * 1000 * 1000
        with tempfile.TemporaryDirectory(prefix="aq-zip-") as temporary:
            destination = Path(temporary) / "delta-receipt"
            archive.extractall(destination)
            validate(destination, require_directory_name=True)
            for path in destination.rglob("*.py"):
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
    assert output.stat().st_size < 50 * 1000 * 1000
    result = {"archive": str(output), "skillName": "delta-receipt", "version": VERSION, "bytes": output.stat().st_size, "files": len(names),
              "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "rootSkill": True, "formatValidatedAfterExtraction": True}
    output.with_suffix(".zip.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / "delta-receipt-0.2.0.zip")
    build(parser.parse_args().out.resolve())
