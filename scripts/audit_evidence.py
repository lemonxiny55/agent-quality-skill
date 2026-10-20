#!/usr/bin/env python3
"""Replay archived demo output parsers and comparisons; never re-label stale files fresh."""
import argparse
import json
from pathlib import Path
import sys

import quality as q

ROOT = Path(__file__).resolve().parent.parent


def audit(directory):
    before = q.read_artifact(directory / "before.json")
    baseline = before["execution"]
    if before["environment"]["platform"] != sys.platform:
        raise ValueError("replay archive on its captured OS; foreign paths are archival evidence")
    assert before["implementationSha256"] == q.implementation_identity()
    assert baseline["complete"]
    results = {}
    for name, expected in (("regression.json", "regression"), ("clean.json", "no_new_observed"), ("missing-baseline.json", "incomplete")):
        receipt = q.read_artifact(directory / name)
        assert receipt["verdict"] == expected
        assert receipt["implementationSha256"] == q.implementation_identity()
        for check in receipt["execution"]["checks"]:
            assert check["status"] == "complete"
            replayed = q.parse_output(Path(receipt["repo"]), check["adapter"], check["stdout"], check["stderr"], check["exitCode"])
            assert replayed == check["findings"]
            if check["adapter"] == "node-test-tap":
                assert q.node_test_summary(check["stdout"], check["exitCode"]) == check["testSummary"]
        if receipt["baseline"]:
            assert receipt["baseline"]["integritySha256"] == before["integritySha256"]
            for old, new, compared in zip(baseline["checks"], receipt["execution"]["checks"], receipt["comparisons"]):
                assert q.compare_check(old, new, baseline["after"], receipt["execution"]["after"]) == compared
        results[name] = {"verdict": expected, "outputAndComparisonsReplayed": True}
    stale = json.loads((directory / "stale-check.json").read_text(encoding="utf-8"))
    assert not stale["fresh"] and stale["effectiveVerdict"] == "incomplete"
    clean = q.read_artifact(directory / "clean.json")
    assert sum(len(c["historical"]) for c in clean["comparisons"]) == 2
    assert clean["execution"]["checks"][2]["testSummary"]["pass"] == 2
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    import hashlib
    for filename, expected_hash in summary["artifacts"].items():
        assert hashlib.sha256((directory / filename).read_bytes()).hexdigest() == expected_hash
    return {"directory": str(directory), "checks": results, "historicalFindings": 2,
            "testCount": 2, "hashesAndRawOutputConsistent": True, "authentication": "unsigned local evidence"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="+", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = {"audits": [audit(path.resolve()) for path in args.directories], "implementationSha256": q.implementation_identity()}
    data = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.write_text(data, encoding="utf-8")
    print(data)
