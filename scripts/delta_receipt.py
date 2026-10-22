#!/usr/bin/env python3
"""Explicit, local, conservative quality evidence. Python 3.10+; Git required."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid

VERSION = "0.2.0"
# v0.1.0 receipts used this exact, immutable CLI source fingerprint. Accept it so an
# in-flight baseline or receipt remains verifiable after the distribution rename.
LEGACY_IMPLEMENTATION_IDENTITIES = frozenset({
    "5da035d8c505de33e8c9bb212c1e0de646f52469e02d4a0be62ea69eab9e62b7",
})
SCHEMA = "agent-quality/v1"
MAX_OUTPUT = 1024 * 1024
MAX_FILES = 20000
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
STATE_DIR = ".agent-quality"
KINDS = ("lint", "typecheck", "tests")


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def implementation_identity():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def implementation_identity_is_compatible(value):
    """Recognize this CLI and the unchanged v0.1.0 implementation for old receipts."""
    return value == implementation_identity() or value in LEGACY_IMPLEMENTATION_IDENTITIES


def seal(value):
    return {**value, "integritySha256": digest({k: v for k, v in value.items() if k != "integritySha256"})}


def read_artifact(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("integritySha256") != seal(value)["integritySha256"]:
        raise ValueError("artifact integrity mismatch (hash is not an authentication signature)")
    if value.get("schema") != SCHEMA:
        raise ValueError("unsupported artifact schema")
    return value


def save(path, value, *, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("artifact output must not be a symlink")
    data = json.dumps(seal(value), ensure_ascii=True, indent=2) + "\n"
    if exclusive:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(data)
        return
    fd, temporary = tempfile.mkstemp(prefix=".quality-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def git(root, *args):
    done = subprocess.run(["git", "-c", "core.quotePath=false", "-C", str(root), *args],
                          capture_output=True, timeout=15, check=False)
    if done.returncode:
        raise ValueError("git failed: " + done.stderr.decode("utf-8", "replace").strip())
    return done.stdout


def repository(path):
    root = Path(path).resolve(strict=True)
    actual = Path(os.fsdecode(git(root, "rev-parse", "--show-toplevel")).strip()).resolve()
    if root != actual:
        raise ValueError("--repo must name the Git working-tree root")
    return root


def snapshot(root):
    """Hash tracked and nonignored untracked files without stashing/rewinding."""
    files, reasons = {}, []
    started, total = time.monotonic(), 0
    try:
        head = os.fsdecode(git(root, "rev-parse", "--verify", "HEAD")).strip()
        index = git(root, "ls-files", "--stage", "-z")
        if any(row.startswith(b"160000 ") for row in index.split(b"\0")):
            reasons.append("submodule contents unsupported")
        paths = sorted(set(os.fsdecode(p) for p in git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split(b"\0") if p))
        ignored = [os.fsdecode(p) for p in git(root, "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--directory").split(b"\0") if p]
        status = os.fsdecode(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all"))
        for name in paths:
            if name == STATE_DIR or name.startswith(STATE_DIR + "/"):
                if any(row.split(b"\t", 1)[-1] == os.fsencode(name) for row in index.split(b"\0")):
                    reasons.append("tracked files in reserved evidence directory")
                continue
            if len(files) >= MAX_FILES or time.monotonic() - started > 15:
                reasons.append("snapshot file/time budget exhausted")
                break
            path = root / name
            try:
                current = path
                while current != root:
                    if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
                        raise ValueError("symlink/junction not followed")
                    current = current.parent
                if not path.exists():
                    continue
                info = path.stat()
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError("special file or submodule not hashed")
                if info.st_size > MAX_FILE_BYTES or total + info.st_size > MAX_TOTAL_BYTES:
                    raise ValueError("snapshot byte budget exhausted")
                data = path.read_bytes()
                after = path.stat()
                if (info.st_mtime_ns, info.st_size, info.st_ino) != (after.st_mtime_ns, after.st_size, after.st_ino):
                    raise ValueError("file changed while hashing")
                files[name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                               "executable": bool(info.st_mode & stat.S_IXUSR) if os.name != "nt" else None}
                total += len(data)
            except (OSError, ValueError) as error:
                reasons.append(f"{name}: {error}")
        end_paths = sorted(set(os.fsdecode(p) for p in git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split(b"\0") if p))
        if end_paths != paths or git(root, "ls-files", "--stage", "-z") != index:
            reasons.append("Git inventory changed during snapshot")
        result = {"head": head, "indexSha256": hashlib.sha256(index).hexdigest(), "files": files,
                  "excluded": sorted(set(ignored + [STATE_DIR + "/"])), "gitStatusPorcelainZ": status,
                  "reasons": reasons, "complete": not reasons}
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        result = {"head": None, "files": files, "reasons": [str(error)], "complete": False, "excluded": []}
    result["digest"] = digest({k: result.get(k) for k in ("head", "indexSha256", "files", "excluded")})
    return result


def changes(before, after):
    old, new = before["files"], after["files"]
    return [{"path": name, "change": "added" if name not in old else "deleted" if name not in new else "modified"}
            for name in sorted(old.keys() | new.keys()) if old.get(name) != new.get(name)]


def load_config(root):
    value = json.loads((root / ".agent-quality.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {"version", "checks"} or value["version"] != 1 or not isinstance(value["checks"], list):
        raise ValueError("configuration requires version=1 and checks array only")
    if not 1 <= len(value["checks"]) <= 12:
        raise ValueError("configure 1..12 checks")
    ids = set()
    for check in value["checks"]:
        if not isinstance(check, dict) or set(check) != {"id", "kind", "adapter", "argv", "timeoutSeconds"}:
            raise ValueError("each check requires id, kind, adapter, argv, timeoutSeconds only")
        if not isinstance(check["id"], str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", check["id"]) or check["id"] in ids:
            raise ValueError("check ids must be unique lower-case identifiers")
        ids.add(check["id"])
        if check["kind"] not in KINDS or check["adapter"] not in ("eslint-json", "tsc", "node-test-tap", "exit"):
            raise ValueError("unsupported check kind or adapter")
        if (check["adapter"] == "eslint-json" and check["kind"] != "lint") or (check["adapter"] == "tsc" and check["kind"] != "typecheck") or (check["adapter"] == "node-test-tap" and check["kind"] != "tests"):
            raise ValueError("diagnostic adapter used with wrong check kind")
        if not isinstance(check["argv"], list) or not check["argv"] or not all(isinstance(a, str) and a and "\0" not in a for a in check["argv"]):
            raise ValueError("argv requires nonempty strings; no shell string")
        if type(check["timeoutSeconds"]) not in (int, float) or not 0.05 <= check["timeoutSeconds"] <= 600:
            raise ValueError("timeoutSeconds must be 0.05..600")
    return value


def command_identity(root, check):
    argv = [sys.executable if item == "{python}" else item for item in check["argv"]]
    candidate = shutil.which(argv[0])
    resolved = Path(candidate).resolve() if candidate else None
    files = {}
    for item in ([str(resolved)] if resolved else []) + argv[1:]:
        path = Path(item)
        if not path.is_absolute():
            path = root / path
        if path.is_file():
            try:
                files[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                files[str(path)] = "unreadable"
    return {"argv": argv, "resolvedExecutable": str(resolved) if resolved else None, "fileSha256": files}


def environment_identity():
    env = {k: v for k, v in os.environ.items() if k not in ("_", "SHLVL", "OLDPWD", "PWD")}
    # Keep only one fingerprint; per-variable hashes can expose predictable values
    # and unnecessarily disclose secret variable names.
    return {"platform": sys.platform, "python": sys.version, "environmentSha256": digest(env)}


def stop_process(process):
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=5, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)


def run_command(root, check, cancel):
    identity = command_identity(root, check)
    result = {"id": check["id"], "kind": check["kind"], "adapter": check["adapter"], "command": identity,
              "cwd": str(root), "startedAt": now(), "status": "not_run", "exitCode": None, "stdout": "", "stderr": "", "findings": []}
    started = time.monotonic()
    if cancel.is_set():
        result.update(status="cancelled", reason="cancelled before launch")
    elif not identity["resolvedExecutable"]:
        result.update(status="missing_tool", reason="executable not found; no installation attempted")
    elif Path(identity["resolvedExecutable"]).suffix.lower() in (".cmd", ".bat", ".ps1"):
        result.update(status="not_run", reason="shell wrappers unsupported; invoke interpreter and script with argv")
    else:
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            try:
                process = subprocess.Popen([identity["resolvedExecutable"], *identity["argv"][1:]], cwd=root,
                                           stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, shell=False,
                                           start_new_session=os.name != "nt",
                                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
                result["status"] = "complete"
                while True:
                    code = process.poll()
                    if cancel.is_set():
                        result.update(status="cancelled", reason="cancellation requested")
                    elif time.monotonic() - started > check["timeoutSeconds"]:
                        result.update(status="timeout", reason="command time budget exhausted")
                    elif max(os.fstat(stdout.fileno()).st_size, os.fstat(stderr.fileno()).st_size) > MAX_OUTPUT:
                        result.update(status="output_limit", reason="output exceeded 1 MiB per stream")
                    if result["status"] != "complete":
                        stop_process(process)
                        break
                    if code is not None:
                        break
                    cancel.wait(0.02)
                result["exitCode"] = process.returncode
                for key, stream in (("stdout", stdout), ("stderr", stderr)):
                    stream.seek(0)
                    raw = stream.read(MAX_OUTPUT + 1)
                    result[key] = raw[:MAX_OUTPUT].decode("utf-8", "replace")
                    result[key + "Sha256"] = hashlib.sha256(raw[:MAX_OUTPUT]).hexdigest()
                    if len(raw) > MAX_OUTPUT:
                        result.update(status="output_limit", reason="output exceeded 1 MiB per stream")
                if result["status"] == "complete":
                    if result["exitCode"] is None or result["exitCode"] < 0:
                        raise ValueError("command terminated by signal")
                    if check["adapter"] == "node-test-tap":
                        result["testSummary"] = node_test_summary(result["stdout"], result["exitCode"])
                    result["findings"] = parse_output(root, check["adapter"], result["stdout"], result["stderr"], result["exitCode"])
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                result.update(status="command_error", reason=str(error))
    result["elapsedSeconds"] = round(time.monotonic() - started, 4)
    result["finishedAt"] = now()
    return result


def relative_file(root, text):
    path = Path(text)
    if not path.is_absolute():
        path = root / path
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        raise ValueError("diagnostic path outside repository") from None


def node_test_summary(stdout, code):
    if "TAP version 13" not in stdout.splitlines():
        raise ValueError("Node test adapter requires --test-reporter=tap")
    summary = {}
    for key in ("tests", "suites", "pass", "fail", "cancelled", "skipped", "todo"):
        matches = re.findall(r"^# " + key + r" (\d+)\s*$", stdout, re.M)
        if len(matches) != 1:
            raise ValueError("missing or ambiguous Node test summary: " + key)
        summary[key] = int(matches[0])
    if code not in (0, 1) or bool(code) != bool(summary["fail"] or summary["cancelled"]):
        raise ValueError("Node test exit code/summary mismatch")
    if sum(summary[k] for k in ("pass", "fail", "cancelled", "skipped", "todo")) != summary["tests"]:
        raise ValueError("inconsistent Node test totals")
    return summary


def parse_output(root, adapter, stdout, stderr, code):
    if adapter == "exit":
        return [] if code == 0 else [{"identity": "command failed", "path": None}]
    if stderr.strip():
        raise ValueError("unexpected stderr from diagnostic tool; inspect raw output")
    findings = []
    if adapter == "node-test-tap":
        summary = node_test_summary(stdout, code)
        if summary["tests"] == 0 or any(summary[k] for k in ("cancelled", "skipped", "todo")):
            raise ValueError("zero tests or cancelled/skipped/todo tests: execution incomplete")
        return [] if code == 0 else [{"identity": "Node test command failed", "path": None}]
    if adapter == "eslint-json":
        rows = json.loads(stdout)
        if not isinstance(rows, list) or code not in (0, 1):
            raise ValueError("ESLint requires JSON array and exit 0/1")
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("filePath"), str) or not isinstance(row.get("messages"), list):
                raise ValueError("malformed ESLint result")
            name = relative_file(root, row["filePath"])
            for message in row["messages"]:
                if not isinstance(message, dict) or message.get("fatal") or message.get("severity") not in (1, 2) or not isinstance(message.get("message"), str):
                    raise ValueError("fatal or malformed ESLint diagnostic")
                identity = json.dumps([name, message.get("ruleId"), message["severity"], message["message"], message.get("line"), message.get("column")], ensure_ascii=True)
                findings.append({"identity": identity, "path": name})
        if (code == 1) != any(json.loads(f["identity"])[2] == 2 for f in findings):
            raise ValueError("ESLint exit code/diagnostic mismatch; use default warning threshold")
    elif adapter == "tsc":
        if code not in (0, 1, 2):
            raise ValueError("unexpected TypeScript exit code")
        active = None
        for line in stdout.splitlines():
            match = re.match(r"^(.+)\((\d+),(\d+)\): error (TS\d+): (.+)$", line)
            if match:
                name, row, column, rule, message = match.groups()
                name = relative_file(root, name)
                active = {"identity": json.dumps([name, row, column, rule, message]), "path": name}
                findings.append(active)
            elif line.startswith(" ") and active:
                active["identity"] += "\n" + line
            elif line.strip():
                raise ValueError("unrecognized TypeScript output; requires --pretty false --noEmit")
        if bool(code) != bool(findings):
            raise ValueError("TypeScript exit code/diagnostic mismatch")
    else:
        raise ValueError("unsupported output adapter")
    return findings


def sweep(root, config, cancel):
    before = snapshot(root)
    checks, reasons = [], list(before["reasons"])
    for check in config["checks"]:
        result = run_command(root, check, cancel)
        checks.append(result)
        after = snapshot(root)
        if not after["complete"] or after["digest"] != before["digest"]:
            reasons.append(f"workspace changed or coverage incomplete during {check['id']}")
        if command_identity(root, check) != result["command"]:
            reasons.append(f"tool identity changed during {check['id']}")
        reasons.extend(after["reasons"])
    after = snapshot(root)
    reasons.extend(after["reasons"])
    if after["digest"] != before["digest"]:
        reasons.append("workspace changed during checks")
    for kind in KINDS:
        if not any(c["kind"] == kind for c in checks):
            reasons.append(f"{kind}: not configured / not run")
    if any(c["kind"] == "tests" and c["adapter"] == "exit" for c in checks):
        reasons.append("generic test exit status does not prove test execution; use a supported test adapter")
    reasons.extend(f"{c['id']}: {c.get('reason', c['status'])}" for c in checks if c["status"] != "complete")
    return {"before": before, "after": after, "checks": checks, "reasons": sorted(set(reasons)), "complete": not reasons}


def compare_check(baseline, current, old_snapshot, new_snapshot):
    result = {"id": current["id"], "kind": current["kind"], "status": "incomplete", "historical": [], "introduced": [], "unclassified": []}
    if not baseline or baseline["status"] != "complete" or current["status"] != "complete":
        result["reason"] = "comparable completed baseline and current execution required"
        return result
    if baseline["command"] != current["command"]:
        result["reason"] = "tool identity changed"
        return result
    if current["adapter"] in ("exit", "node-test-tap"):
        if current["exitCode"] == 0:
            result["status"] = "no_new_observed"
        elif baseline["exitCode"] == 0:
            result.update(status="regression", introduced=current["findings"])
        else:
            result.update(reason="both commands failed; exit status cannot isolate historical test failures", unclassified=current["findings"])
        return result
    counts = Counter(f["identity"] for f in baseline["findings"])
    for finding in current["findings"]:
        key, name = finding["identity"], finding["path"]
        if counts[key] and name in old_snapshot["files"] and old_snapshot["files"].get(name) == new_snapshot["files"].get(name):
            result["historical"].append(finding)
            counts[key] -= 1
        elif counts[key]:
            result["unclassified"].append(finding)
            counts[key] -= 1
        else:
            result["introduced"].append(finding)
    result["status"] = "regression" if result["introduced"] else "incomplete" if result["unclassified"] else "no_new_observed"
    return result


def verify(root, config, baseline_path, cancel, max_age=86400):
    environment = environment_identity()
    execution = sweep(root, config, cancel)
    reasons, baseline = list(execution["reasons"]), None
    try:
        baseline = read_artifact(baseline_path) if baseline_path else None
        if not baseline:
            raise ValueError("missing pre-edit baseline; current results cannot establish absence of new regressions")
        if baseline.get("artifact") != "baseline" or not baseline.get("beforeEditAttested"):
            raise ValueError("expected a baseline captured with --before-edit")
        if not implementation_identity_is_compatible(baseline.get("implementationSha256")):
            raise ValueError("CLI implementation changed since baseline")
        if baseline["repo"] != str(root) or baseline["execution"]["after"]["head"] != execution["before"]["head"]:
            raise ValueError("baseline belongs to different repository or HEAD")
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(baseline["createdAt"])).total_seconds()
        if not 0 <= age <= max_age:
            raise ValueError("baseline expired or timestamp in future")
        if baseline["configDigest"] != digest(config):
            raise ValueError("check plan changed since baseline")
        if baseline["environment"] != environment:
            raise ValueError("execution environment changed since baseline")
        if not baseline["execution"]["complete"]:
            raise ValueError("baseline execution/coverage incomplete")
        if any(command_identity(root, c) != b["command"] for c, b in zip(config["checks"], baseline["execution"]["checks"])):
            raise ValueError("configured executable/entry file changed since baseline")
    except (OSError, ValueError, KeyError, TypeError) as error:
        reasons.append(str(error))
        baseline = None
    if baseline and execution["complete"]:
        old = baseline["execution"]
        comparisons = [compare_check(next((c for c in old["checks"] if c["id"] == check["id"]), None), check, old["after"], execution["after"]) for check in execution["checks"]]
    else:
        comparisons = [{"id": c["id"], "kind": c["kind"], "status": "incomplete", "historical": [], "introduced": [], "unclassified": c["findings"], "reason": "baseline/verification evidence unavailable or incomplete"} for c in execution["checks"]]
    if any(c["status"] == "incomplete" or c["unclassified"] for c in comparisons):
        reasons.append("one or more checks have unclassified or incomplete evidence")
    verdict = "regression" if any(c["introduced"] for c in comparisons) else "incomplete" if reasons else "no_new_observed"
    return {"schema": SCHEMA, "artifact": "receipt", "version": VERSION, "implementationSha256": implementation_identity(), "createdAt": now(), "repo": str(root),
            "environment": environment, "configDigest": digest(config), "config": config,
            "baseline": {"id": baseline["id"], "integritySha256": baseline["integritySha256"], "trust": "local capture; user attests it predates edits; unsigned"} if baseline else None,
            "changes": changes(baseline["execution"]["after"], execution["after"]) if baseline else None,
            "authorship": "unknown: observed interval changes may include other writers",
            "scope": "configured commands; tracked and nonignored untracked content; exclusions listed in snapshots",
            "execution": execution, "comparisons": comparisons, "verdict": verdict, "reasons": sorted(set(reasons)),
            "claim": "No new findings observed by the configured checks within the recorded scope." if verdict == "no_new_observed" else "Absence of new regressions has not been established."}


def check_receipt(root, path):
    receipt = read_artifact(path)
    if receipt.get("artifact") != "receipt" or receipt.get("repo") != str(root):
        raise ValueError("expected receipt from this repository")
    current, reasons = snapshot(root), []
    if not implementation_identity_is_compatible(receipt.get("implementationSha256")):
        reasons.append("receipt stale: CLI implementation changed")
    if not current["complete"] or current["digest"] != receipt["execution"]["after"]["digest"]:
        reasons.append("receipt stale: workspace content/index/HEAD/exclusions changed")
    config = load_config(root)
    if digest(config) != receipt["configDigest"] or environment_identity() != receipt["environment"]:
        reasons.append("receipt stale: configuration/environment changed")
    for check, executed in zip(config["checks"], receipt["execution"]["checks"]):
        if command_identity(root, check) != executed["command"]:
            reasons.append("receipt stale: tool identity changed")
    return {"artifactIntegrity": "verified hash (unsigned; not tamper-proof)", "fresh": not reasons,
            "savedVerdict": receipt["verdict"], "effectiveVerdict": "incomplete" if reasons else receipt["verdict"], "reasons": reasons}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "baseline", "verify", "check-receipt"))
    parser.add_argument("--repo", required=True)
    parser.add_argument("--out")
    parser.add_argument("--baseline")
    parser.add_argument("--receipt")
    parser.add_argument("--before-edit", action="store_true", help="attest capture occurs before task edits")
    parser.add_argument("--execute", action="store_true", help="execute reviewed repository command plan")
    parser.add_argument("--max-age", type=float, default=86400)
    args = parser.parse_args(argv)
    cancel = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: cancel.set())
    try:
        root = repository(args.repo)
        config = load_config(root)
        if not 0 < args.max_age <= 86400:
            raise ValueError("--max-age must be within (0, 86400] seconds")
        if args.action == "plan":
            print(json.dumps({"repo": str(root), "checks": config["checks"], "configDigest": digest(config), "workspace": snapshot(root), "execution": "not requested; inspect commands before --execute"}, indent=2))
            return 0
        if args.action == "check-receipt":
            if not args.receipt:
                raise ValueError("--receipt is required")
            result = check_receipt(root, args.receipt)
            print(json.dumps(result, indent=2))
            return 0 if result["fresh"] else 2
        if not args.execute or not args.out:
            raise ValueError("review plan first; --execute and --out required for execution")
        output = resolve_output(root, args.out)
        if args.baseline and output == Path(args.baseline).resolve():
            raise ValueError("receipt must not overwrite baseline")
        if args.action == "baseline":
            if not args.before_edit:
                raise ValueError("--before-edit attestation required; do not manufacture a baseline after editing")
            if output.exists():
                raise ValueError("baseline exists; use a new session file before the next task")
            result = {"schema": SCHEMA, "artifact": "baseline", "version": VERSION, "implementationSha256": implementation_identity(), "id": str(uuid.uuid4()), "createdAt": now(),
                      "repo": str(root), "beforeEditAttested": True, "configDigest": digest(config), "environment": environment_identity(),
                      "execution": sweep(root, config, cancel)}
            save(output, result, exclusive=True)
            verdict = "baseline_ready" if result["execution"]["complete"] else "incomplete"
        else:
            result = verify(root, config, args.baseline, cancel, args.max_age)
            save(output, result)
            verdict = result["verdict"]
        print(json.dumps({"artifact": str(output), "verdict": verdict, "reasons": result.get("reasons", result["execution"]["reasons"])}, indent=2))
        return 0 if verdict in ("baseline_ready", "no_new_observed") else 1 if verdict == "regression" else 2
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({"verdict": "incomplete", "error": str(error)}), file=sys.stderr)
        return 2


def resolve_output(root, value):
    """Resolve an artifact path without letting repo symlinks escape its state dir."""
    raw = Path(value)
    if not raw.is_absolute():
        raw = Path.cwd() / raw
    raw = Path(os.path.abspath(raw))
    try:
        relative = raw.relative_to(root)
    except ValueError:
        if raw.is_symlink():
            raise ValueError("artifact output must not be a symlink") from None
        return raw.resolve()
    if not relative.parts or relative.parts[0] != STATE_DIR:
        raise ValueError("inside repository, output must be in reserved .agent-quality/ directory")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("artifact output path must not traverse symlinks")
    resolved = raw.resolve()
    state = (root / STATE_DIR).resolve()
    if not resolved.is_relative_to(state):
        raise ValueError("artifact output resolves outside reserved .agent-quality/ directory")
    return resolved


if __name__ == "__main__":
    sys.exit(main())
