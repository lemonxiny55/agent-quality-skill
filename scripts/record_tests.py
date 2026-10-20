#!/usr/bin/env python3
"""Run the actual unittest suite and persist raw output plus platform evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    argv = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    data = {"timestamp": datetime.now(timezone.utc).isoformat(), "argv": argv, "platform": platform.platform(), "python": sys.version,
            "exitCode": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
            "testedSourceSha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for directory in ("scripts", "tests") for p in (ROOT / directory).rglob("*.py")}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(result.stdout + result.stderr)
    sys.exit(result.returncode)
