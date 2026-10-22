#!/usr/bin/env python3
"""Audit actual Codex JSONL tool events against the saved baseline and receipt."""
import argparse
import hashlib
import json
import re
from pathlib import Path

import delta_receipt as q

ROOT = Path(__file__).resolve().parent.parent


def audit(directory):
    invocation = json.loads((directory / "invocation.json").read_text(encoding="utf-8"))
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    transcript = directory / "transcript.jsonl"
    assert summary["exitCode"] == 0
    assert hashlib.sha256(transcript.read_bytes()).hexdigest() == summary["transcriptSha256"]
    assert invocation["skillSha256"] == hashlib.sha256((ROOT / "SKILL.md").read_bytes()).hexdigest()
    paths = [directory / a["file"] for a in summary["artifacts"]]
    artifacts = [q.read_artifact(p) for p in paths]
    before = next(a for a in artifacts if a["artifact"] == "baseline")
    receipt = next(a for a in artifacts if a["artifact"] == "receipt")
    assert before["implementationSha256"] == receipt["implementationSha256"] and q.implementation_identity_is_compatible(before["implementationSha256"])
    original = (ROOT / "examples/node/src/calculator.mjs").read_bytes()
    original_hash = hashlib.sha256(original).hexdigest()
    assert before["execution"]["before"]["files"]["src/calculator.mjs"]["sha256"] == original_hash
    assert before["execution"]["after"]["files"]["src/calculator.mjs"]["sha256"] == original_hash
    assert before["environment"] == receipt["environment"]
    assert receipt["verdict"] == "no_new_observed"
    assert receipt["changes"] == [{"path": "src/calculator.mjs", "change": "modified"}]
    expected_source = original.replace(b"add(a, b) { return a + b; }", b"add(left, right) { return left + right; }")
    actual_source = (Path(invocation["cwd"]) / "src" / "calculator.mjs").read_bytes()
    assert actual_source.replace(b"\r\n", b"\n") == expected_source
    assert receipt["execution"]["after"]["files"]["src/calculator.mjs"]["sha256"] == hashlib.sha256(actual_source).hexdigest()
    assert receipt["baseline"]["integritySha256"] == before["integritySha256"]
    for old, new, compared in zip(before["execution"]["checks"], receipt["execution"]["checks"], receipt["comparisons"]):
        assert q.compare_check(old, new, before["execution"]["after"], receipt["execution"]["after"]) == compared
        assert not compared["introduced"] and not compared["unclassified"]
        assert q.parse_output(Path(receipt["repo"]), new["adapter"], new["stdout"], new["stderr"], new["exitCode"]) == new["findings"]
    assert sum(len(c["historical"]) for c in receipt["comparisons"]) == 2
    assert receipt["execution"]["checks"][2]["testSummary"] == {"tests": 2, "suites": 0, "pass": 2, "fail": 0, "cancelled": 0, "skipped": 0, "todo": 0}
    events = [json.loads(line) for line in transcript.read_text(encoding="utf-8").splitlines()]
    completed = [e["item"] for e in events if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "command_execution"]
    assert any("SKILL.md" in e["command"] and ("# DeltaReceipt" in e.get("aggregated_output", "") or "# Agent Quality Skill" in e.get("aggregated_output", "")) for e in completed)
    actions = []
    for event in completed:
        output = event.get("aggregated_output", "")
        lines = output.splitlines()
        for index, line in enumerate(lines):
            if not line.startswith("COMMAND: "):
                continue
            cli_name = "delta_receipt.py" if "delta_receipt.py" in line else "quality.py" if "quality.py" in line else None
            if not cli_name:
                continue
            action = line.split(cli_name, 1)[1].strip().split()[0]
            if action not in ("baseline", "verify", "check-receipt"):
                continue
            assert index + 3 < len(lines) and lines[index + 1] == "EXIT: 0" and lines[index + 2] == "STDOUT:"
            finish = next((n for n in range(index + 3, len(lines)) if lines[n] == "STDERR:"), len(lines))
            actions.append({"action": action, "stdout": json.loads("\n".join(lines[index + 3:finish]))})

        # PowerShell-hosted Codex runs print argv and stdout with terminal-style
        # markers instead of the simple COMMAND:/EXIT:/STDOUT: format above.
        for match in re.finditer(r"COMMAND=\[(.*?)--- STDOUT ---", output, re.S):
            segment = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", match.group(1))
            if "--before-edit" in segment:
                action = "baseline"
            elif "--receipt" in segment:
                action = "check-receipt"
            elif "--baseline" in segment and "--execute" in segment:
                action = "verify"
            else:
                continue
            finish = output.find("--- STDERR ---", match.end())
            assert finish >= 0, "CLI output did not include its stderr boundary"
            payload = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output[match.end():finish]).replace("\r", "").strip()
            stdout = json.loads(payload) if action == "check-receipt" else {}
            actions.append({"action": action, "stdout": stdout})
    assert [a["action"] for a in actions] == ["baseline", "verify", "check-receipt"]
    freshness = actions[-1]["stdout"]
    assert freshness["fresh"] and freshness["effectiveVerdict"] == "no_new_observed"
    assert any(e.get("type") == "turn.completed" for e in events)
    return {"agent": summary["version"], "status": "passed", "explicitSkillLoad": True, "automaticSelectionTested": False,
            "baselineBeforeRequestedEdit": True, "sameEnvironment": True, "onlyRequestedSourceChanged": True,
            "configuredTestsPassed": 2, "historicalFindingsRetained": 2, "receiptVerdict": receipt["verdict"],
            "agentCheckedFreshness": True, "rawToolEventsAudited": True, "transcriptSha256": summary["transcriptSha256"],
            "scope": "one isolated Windows task, explicit invocation and one inherited terminal environment; no host-hook test"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.directory.resolve())
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
