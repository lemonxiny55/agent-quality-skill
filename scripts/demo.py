#!/usr/bin/env python3
"""Reproducible real ESLint/TypeScript/Node test demo in a NEW disposable repo."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="explicitly allow npm ci --ignore-scripts in demo repo")
    parser.add_argument("--work", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    work = (args.work or ROOT / ".work" / ("demo-" + uuid.uuid4().hex[:10])).resolve()
    if work.exists():
        parser.error("--work must not exist (will never overwrite a user repository)")
    if not args.install:
        parser.error("the real demo requires explicit --install to run npm ci --ignore-scripts")
    args.evidence.mkdir(parents=True, exist_ok=True)
    evidence = args.evidence.resolve()
    shutil.copytree(ROOT / "examples" / "node", work, ignore=shutil.ignore_patterns("node_modules", ".agent-quality", ".git"))
    records = []

    def run(argv, expected=0, cwd=work):
        result = subprocess.run([str(a) for a in argv], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        record = {"argv": [str(a) for a in argv], "cwd": str(cwd), "exitCode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        records.append(record)
        (evidence / "commands.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
        if result.returncode != expected:
            raise RuntimeError(f"expected exit {expected}, got {result.returncode}: {argv}\n{result.stdout}\n{result.stderr}")
        return result

    # Calling npm's JS entry avoids cmd.exe shell quoting on Windows.
    node = shutil.which("node")
    npm = shutil.which("npm")
    if not node or not npm:
        raise RuntimeError("install Node and npm before the demo")
    if os.name == "nt":
        npm_script = Path(node).parent / "node_modules" / "npm" / "bin" / "npm-cli.js"
        npm_argv = [node, str(npm_script)]
    else:
        npm_argv = [str(Path(npm).resolve())]
    run([*npm_argv, "ci", "--ignore-scripts", "--no-audit", "--no-fund"])
    run(["git", "init", "-b", "main"])
    run(["git", "add", "."])
    run(["git", "-c", "user.name=Quality Demo", "-c", "user.email=demo@example.invalid", "commit", "-m", "real-tool fixture"])
    # Pre-existing staged and untracked user work must survive all checks.
    current = work / "types" / "current.ts"
    current.write_text("// Pre-existing user change\nexport const current: number = 1;\n", encoding="utf-8")
    run(["git", "add", "types/current.ts"])
    (work / "user-note.txt").write_text("Pre-existing untracked user work.\n", encoding="utf-8")
    staged = run(["git", "diff", "--cached"]).stdout
    cli = [sys.executable, str(ROOT / "scripts" / "delta_receipt.py")]
    state = work / ".agent-quality"
    state.mkdir()
    baseline = state / "before.json"
    run([*cli, "plan", "--repo", work])
    run([*cli, "baseline", "--repo", work, "--before-edit", "--execute", "--out", baseline])
    (work / "src" / "calculator.mjs").write_text("export function add(a, b) { const accidentallyUnused = 1; return a - b; }\n", encoding="utf-8")
    current.write_text("// Pre-existing user change\nexport const current: number = 'regression';\n", encoding="utf-8")
    run([*cli, "verify", "--repo", work, "--baseline", baseline, "--execute", "--out", state / "regression.json"], 1)
    regression = json.loads((state / "regression.json").read_text())
    assert [c["status"] for c in regression["comparisons"]] == ["regression"] * 3
    assert [len(c["historical"]) for c in regression["comparisons"]] == [1, 1, 0]
    (work / "src" / "calculator.mjs").write_text("// Requested change: document addition.\nexport function add(a, b) { return a + b; }\n", encoding="utf-8")
    current.write_text("// Pre-existing user change\nexport const current: number = 1;\n", encoding="utf-8")
    run([*cli, "verify", "--repo", work, "--baseline", baseline, "--execute", "--out", state / "clean.json"])
    clean = json.loads((state / "clean.json").read_text())
    assert clean["verdict"] == "no_new_observed"
    assert sum(len(c["historical"]) for c in clean["comparisons"]) == 2
    run([*cli, "check-receipt", "--repo", work, "--receipt", state / "clean.json"])
    run([*cli, "verify", "--repo", work, "--execute", "--out", state / "missing-baseline.json"], 2)
    with (work / "src" / "calculator.mjs").open("a", encoding="utf-8") as stream:
        stream.write("// Subsequent external write invalidates saved receipt.\n")
    stale = run([*cli, "check-receipt", "--repo", work, "--receipt", state / "clean.json"], 2)
    (evidence / "stale-check.json").write_text(stale.stdout, encoding="utf-8")
    assert run(["git", "diff", "--cached"]).stdout == staged
    assert (work / "user-note.txt").read_text() == "Pre-existing untracked user work.\n"
    for path in state.glob("*.json"):
        shutil.copy2(path, evidence / path.name)
    versions = {"python": sys.version, "platform": sys.platform, "node": run([node, "--version"]).stdout.strip(),
                "eslint": run([node, "node_modules/eslint/bin/eslint.js", "--version"]).stdout.strip(),
                "typescript": run([node, "node_modules/typescript/bin/tsc", "--version"]).stdout.strip()}
    summary = {"realTools": versions, "work": str(work), "regressionVerdict": regression["verdict"], "finalVerdict": clean["verdict"],
               "historicalFindingsRetained": 2, "testCommandExit": clean["execution"]["checks"][2]["exitCode"],
               "testSummary": clean["execution"]["checks"][2]["testSummary"],
               "missingBaseline": "incomplete", "staleReceipt": "incomplete", "stagedAndUntrackedPreserved": True,
               "artifacts": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence.glob("*.json") if p.name != "summary.json"}}
    (evidence / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
