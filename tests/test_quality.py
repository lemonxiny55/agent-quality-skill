"""Deterministic fixtures test failure modes; these are not the real-tool demo."""
import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from scripts import delta_receipt as q


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


class Workspace(unittest.TestCase):
    def test_legacy_quality_package_import_exposes_core_api(self):
        from scripts import quality as legacy_q

        self.assertIs(legacy_q.main, q.main)
        self.assertIs(legacy_q.verify, q.verify)
        self.assertIs(legacy_q.check_receipt, q.check_receipt)
        legacy = "5da035d8c505de33e8c9bb212c1e0de646f52469e02d4a0be62ea69eab9e62b7"
        self.assertTrue(legacy_q.implementation_identity_is_compatible(legacy))
        self.assertFalse(legacy_q.implementation_identity_is_compatible("0" * 64))

    def test_all_cli_entrypoints_support_help(self):
        root = Path(__file__).resolve().parent.parent
        commands = (
            [sys.executable, "scripts/quality.py", "--help"],
            [sys.executable, "-m", "scripts.quality", "--help"],
            [sys.executable, "scripts/delta_receipt.py", "--help"],
        )
        for command in commands:
            with self.subTest(command=command):
                result = subprocess.run(
                    command,
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout.lower())

    def test_v010_receipt_fingerprint_remains_supported(self):
        legacy = "5da035d8c505de33e8c9bb212c1e0de646f52469e02d4a0be62ea69eab9e62b7"
        self.assertEqual(q.VERSION, "0.2.0")
        self.assertEqual(q.SCHEMA, "agent-quality/v1")
        self.assertEqual(q.STATE_DIR, ".agent-quality")
        self.assertTrue(q.implementation_identity_is_compatible(legacy))
        self.assertTrue(q.implementation_identity_is_compatible(q.implementation_identity()))
        self.assertFalse(q.implementation_identity_is_compatible("0" * 64))
        archived = Path(__file__).resolve().parent.parent / "evidence" / "release" / "demo-windows" / "before.json"
        old_artifact = q.read_artifact(archived)
        self.assertEqual(old_artifact["version"], "0.1.0")
        self.assertTrue(q.implementation_identity_is_compatible(old_artifact["implementationSha256"]))
        baseline = self.capture()
        baseline["version"] = "0.1.0"
        baseline["implementationSha256"] = legacy
        q.save(self.baseline, baseline)
        receipt = self.verify()
        self.assertEqual(receipt["verdict"], "no_new_observed")
        receipt_path = self.root / ".agent-quality" / "receipt.json"
        q.save(receipt_path, receipt)
        receipt["version"] = "0.1.0"
        receipt["implementationSha256"] = legacy
        q.save(receipt_path, receipt)
        from scripts import quality as legacy_q
        checked = legacy_q.check_receipt(self.root.resolve(), receipt_path)
        self.assertTrue(checked["fresh"], checked["reasons"])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aq-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo with spaces"
        self.root.mkdir()
        git(self.root, "init")
        (self.root / "source.txt").write_text("initial\n", encoding="utf-8")
        (self.root / "legacy.txt").write_text("historical\n", encoding="utf-8")
        (self.root / ".gitignore").write_text(".agent-quality/\nignored/\n", encoding="utf-8")
        # Fixture executable: intentionally emits protocol data for adversarial tests.
        (self.root / "check.py").write_text('''import json, pathlib, sys, time
mode = sys.argv[1]
if mode == "eslint":
    rows = []
    for name in ("legacy.txt", "source.txt"):
        content = pathlib.Path(name).read_text()
        messages = [{"ruleId":"fixture", "severity":2, "message":"bad", "line":1, "column":1}] if content.startswith(("historical", "bad")) else []
        rows.append({"filePath":str(pathlib.Path(name).resolve()), "messages":messages})
    print(json.dumps(rows)); sys.exit(int(any(r["messages"] for r in rows)))
elif mode == "timeout": time.sleep(30)
elif mode == "mutate": pathlib.Path("source.txt").write_text("changed by check"); print("ok")
elif mode == "flood": print("x" * (1024 * 1024 + 2))
elif mode == "fail":
    print("TAP version 13\\n1..1\\n# tests 1\\n# suites 0\\n# pass 0\\n# fail 1\\n# cancelled 0\\n# skipped 0\\n# todo 0"); sys.exit(1)
elif mode == "malformed": print("bad json")
elif mode == "descendant":
    import subprocess
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(1.5); open('escaped.txt','w').write('alive')"])
    pathlib.Path(".agent-quality/child.pid").write_text(str(child.pid))
    time.sleep(30)
else: print("TAP version 13\\n1..1\\n# tests 1\\n# suites 0\\n# pass 1\\n# fail 0\\n# cancelled 0\\n# skipped 0\\n# todo 0")
''', encoding="utf-8")
        self.config = {"version": 1, "checks": [
            {"id": "lint", "kind": "lint", "adapter": "eslint-json", "argv": ["{python}", "check.py", "eslint"], "timeoutSeconds": 5},
            {"id": "types", "kind": "typecheck", "adapter": "exit", "argv": ["{python}", "check.py", "pass"], "timeoutSeconds": 5},
            {"id": "tests", "kind": "tests", "adapter": "node-test-tap", "argv": ["{python}", "check.py", "pass"], "timeoutSeconds": 5}]}
        self.write_config()
        git(self.root, "add", ".")
        git(self.root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture")
        self.cancel = threading.Event()
        self.baseline = self.root / ".agent-quality" / "before.json"
        self.baseline.parent.mkdir()

    def write_config(self):
        (self.root / ".agent-quality.json").write_text(json.dumps(self.config), encoding="utf-8")

    def capture(self):
        result = {"schema": q.SCHEMA, "artifact": "baseline", "version": q.VERSION, "implementationSha256": q.implementation_identity(), "id": "fixture-baseline", "createdAt": q.now(),
                  "repo": str(self.root.resolve()), "beforeEditAttested": True, "configDigest": q.digest(self.config),
                  "environment": q.environment_identity(), "execution": q.sweep(self.root.resolve(), self.config, self.cancel)}
        q.save(self.baseline, result, exclusive=True)
        return result

    def verify(self, baseline=True):
        return q.verify(self.root.resolve(), self.config, self.baseline if baseline else None, self.cancel)

    def test_historical_isolated_from_new(self):
        self.capture()
        (self.root / "source.txt").write_text("bad\n", encoding="utf-8")
        receipt = self.verify()
        self.assertEqual(receipt["verdict"], "regression")
        self.assertEqual(len(receipt["comparisons"][0]["historical"]), 1)
        self.assertEqual(len(receipt["comparisons"][0]["introduced"]), 1)
        (self.root / "source.txt").write_text("fixed\n", encoding="utf-8")
        self.assertEqual(self.verify()["verdict"], "no_new_observed")

    def test_changed_legacy_same_diagnostic_unclassified(self):
        self.capture()
        (self.root / "legacy.txt").write_text("historical but changed\n", encoding="utf-8")
        receipt = self.verify()
        self.assertEqual(receipt["verdict"], "incomplete")
        self.assertEqual(len(receipt["comparisons"][0]["unclassified"]), 1)

    def test_missing_baseline_even_if_checks_pass(self):
        (self.root / "legacy.txt").write_text("fixed\n", encoding="utf-8")
        receipt = self.verify(False)
        self.assertEqual(receipt["verdict"], "incomplete")
        self.assertIsNone(receipt["changes"])
        self.assertIsNone(receipt["baseline"])

    def test_dirty_baseline_preserves_staged_and_untracked(self):
        (self.root / "source.txt").write_text("user edit\n", encoding="utf-8")
        git(self.root, "add", "source.txt")
        (self.root / "untracked.txt").write_text("user untracked\n", encoding="utf-8")
        before = git(self.root, "diff", "--cached").stdout
        self.capture()
        (self.root / "source.txt").write_text("agent edit\n", encoding="utf-8")
        result = self.verify()
        self.assertEqual(result["changes"], [{"path": "source.txt", "change": "modified"}])
        self.assertEqual(git(self.root, "diff", "--cached").stdout, before)
        self.assertEqual((self.root / "untracked.txt").read_text(), "user untracked\n")

    def test_baseline_integrity_corruption(self):
        self.capture()
        value = json.loads(self.baseline.read_text())
        value["execution"]["checks"][0]["findings"] = []
        self.baseline.write_text(json.dumps(value), encoding="utf-8")
        self.assertEqual(self.verify()["verdict"], "incomplete")

    def test_environment_fingerprint_does_not_expose_variable_names(self):
        identity = q.environment_identity()
        self.assertEqual(set(identity), {"platform", "python", "environmentSha256"})

    def test_output_symlink_escape_rejected(self):
        state = self.root / ".agent-quality"
        state.mkdir(exist_ok=True)
        outside = Path(self.temp.name) / "outside.json"
        outside.write_text("keep me", encoding="utf-8")
        link = state / "receipt.json"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("OS does not allow symlinks for this user")
        with self.assertRaisesRegex(ValueError, "symlink"):
            q.resolve_output(self.root.resolve(), link)
        self.assertEqual(outside.read_text(encoding="utf-8"), "keep me")

    def test_changed_configuration_and_environment(self):
        self.capture()
        self.config["checks"][1]["timeoutSeconds"] = 4
        self.assertEqual(self.verify()["verdict"], "incomplete")
        self.config["checks"][1]["timeoutSeconds"] = 5
        os.environ["AQ_TEST_ENVIRONMENT"] = "changed"
        try:
            self.assertEqual(self.verify()["verdict"], "incomplete")
        finally:
            del os.environ["AQ_TEST_ENVIRONMENT"]

    def test_changed_tool(self):
        self.capture()
        with (self.root / "check.py").open("a") as stream:
            stream.write("\n# changed tool\n")
        self.assertEqual(self.verify()["verdict"], "incomplete")

    def test_expired_baseline(self):
        self.capture()
        value = q.read_artifact(self.baseline)
        value["createdAt"] = "2020-01-01T00:00:00+00:00"
        q.save(self.baseline, value)
        self.assertEqual(self.verify()["verdict"], "incomplete")

    def test_timeouts_missing_tools_failures_malformed_output(self):
        for mode, expected in (("timeout", "timeout"), ("malformed", "command_error"), ("flood", "output_limit")):
            with self.subTest(mode=mode):
                check = copy.deepcopy(self.config["checks"][0])
                check["argv"][-1] = mode
                check["timeoutSeconds"] = 0.15 if mode == "timeout" else 5
                self.assertEqual(q.run_command(self.root, check, self.cancel)["status"], expected)
        check = copy.deepcopy(self.config["checks"][2])
        check["argv"] = ["aq-command-that-does-not-exist"]
        self.assertEqual(q.run_command(self.root, check, self.cancel)["status"], "missing_tool")
        check["argv"] = ["{python}", "check.py", "fail"]
        self.assertEqual(q.run_command(self.root, check, self.cancel)["exitCode"], 1)

    def test_cancellation(self):
        check = copy.deepcopy(self.config["checks"][2])
        check["argv"][-1] = "timeout"
        timer = threading.Timer(0.15, self.cancel.set)
        timer.start()
        try:
            self.assertEqual(q.run_command(self.root, check, self.cancel)["status"], "cancelled")
        finally:
            timer.cancel()

    def test_descendant_is_killed_on_timeout(self):
        check = copy.deepcopy(self.config["checks"][2])
        check["argv"][-1] = "descendant"
        check["timeoutSeconds"] = 0.5
        self.assertEqual(q.run_command(self.root, check, self.cancel)["status"], "timeout")
        time.sleep(1.6)
        self.assertFalse((self.root / "escaped.txt").exists())

    def test_mutation_during_checks(self):
        self.config["checks"][2]["argv"][-1] = "mutate"
        self.assertFalse(self.capture()["execution"]["complete"])
        self.assertEqual(self.verify()["verdict"], "incomplete")

    def test_failed_test_baseline_not_laundered(self):
        self.config["checks"][2]["argv"][-1] = "fail"
        self.capture()
        result = self.verify()
        self.assertEqual(result["verdict"], "incomplete")
        self.assertIn("both commands failed", result["comparisons"][2]["reason"])

    def test_green_test_baseline_now_fails(self):
        self.capture()
        # Keep command identity identical; fixture pass can be changed through a source input.
        before = {"id": "t", "status": "complete", "command": {}, "adapter": "exit", "exitCode": 0, "findings": []}
        after = {**before, "kind": "tests", "exitCode": 1, "findings": [{"identity": "command failed", "path": None}]}
        result = q.compare_check(before, after, {}, {})
        self.assertEqual(result["status"], "regression")

    def test_receipt_freshness_and_hash(self):
        self.capture()
        receipt = self.verify()
        path = self.root / ".agent-quality" / "receipt.json"
        q.save(path, receipt)
        self.assertTrue(q.check_receipt(self.root.resolve(), path)["fresh"])
        (self.root / "source.txt").write_text("stale\n", encoding="utf-8")
        self.assertFalse(q.check_receipt(self.root.resolve(), path)["fresh"])
        receipt["verdict"] = "forged"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaises(ValueError):
            q.check_receipt(self.root.resolve(), path)

    def test_unconfigured_category_incomplete(self):
        self.config["checks"].pop()
        self.capture()
        self.assertEqual(self.verify()["verdict"], "incomplete")

    def test_generic_test_command_cannot_prove_test_execution(self):
        self.config["checks"][2]["adapter"] = "exit"
        self.assertFalse(self.capture()["execution"]["complete"])
        self.assertEqual(self.verify()["verdict"], "incomplete")

    def test_add_delete_rename(self):
        self.capture()
        (self.root / "source.txt").rename(self.root / "renamed.txt")
        current = q.snapshot(self.root)
        delta = q.changes(q.read_artifact(self.baseline)["execution"]["after"], current)
        self.assertEqual([c["change"] for c in delta], ["added", "deleted"])

    def test_symlink_incomplete(self):
        try:
            (self.root / "link.txt").symlink_to(self.root / "source.txt")
        except OSError:
            self.skipTest("OS does not allow symlinks for this user")
        self.assertFalse(q.snapshot(self.root)["complete"])

    def test_snapshot_budget_exhaustion(self):
        previous = q.MAX_FILE_BYTES
        q.MAX_FILE_BYTES = 1
        try:
            self.assertFalse(q.snapshot(self.root)["complete"])
        finally:
            q.MAX_FILE_BYTES = previous

    def test_head_change_invalidates_baseline(self):
        self.capture()
        git(self.root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-m", "changed HEAD")
        self.assertEqual(self.verify()["verdict"], "incomplete")

    def test_tracked_evidence_directory_invalidates_snapshot(self):
        (self.baseline.parent / "source.py").write_text("print('source')", encoding="utf-8")
        git(self.root, "add", "-f", ".agent-quality/source.py")
        self.assertFalse(q.snapshot(self.root)["complete"])

    def test_config_validation(self):
        self.assertEqual(q.load_config(self.root), self.config)
        original = copy.deepcopy(self.config)
        for mutate in (lambda c: c.update(version=2), lambda c: c["checks"][0].update(argv="unsafe shell string"),
                       lambda c: c["checks"][0].update(timeoutSeconds=float("nan")),
                       lambda c: c["checks"][0].update(adapter="unknown"),
                       lambda c: c["checks"][1].update(id="lint")):
            self.config = copy.deepcopy(original)
            mutate(self.config)
            self.write_config()
            with self.assertRaises(ValueError):
                q.load_config(self.root)

    @unittest.skipIf(os.name == "nt", "POSIX SIGTERM integration; Windows event cancellation tested separately")
    def test_cli_sigterm_saves_cancelled_receipt(self):
        self.config["checks"][2]["argv"][-1] = "timeout"
        self.write_config()
        output = self.baseline.parent / "cancelled.json"
        process = subprocess.Popen([sys.executable, str(Path(q.__file__).resolve()), "verify", "--execute", "--repo", str(self.root), "--out", str(output)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            time.sleep(0.6)
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 2, (stdout, stderr))
            receipt = q.read_artifact(output)
            self.assertEqual(receipt["verdict"], "incomplete")
            self.assertIn("cancelled", [c["status"] for c in receipt["execution"]["checks"]])
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_cli_safety_and_missing_baseline_exit(self):
        script = Path(q.__file__).resolve()
        run = lambda *args: subprocess.run([sys.executable, str(script), *args, "--repo", str(self.root)], capture_output=True, text=True)
        self.assertEqual(run("baseline", "--out", str(self.baseline)).returncode, 2)
        self.assertEqual(run("baseline", "--execute", "--before-edit", "--out", str(self.root / "source.txt")).returncode, 2)
        self.assertEqual(run("baseline", "--execute", "--before-edit", "--out", str(self.baseline)).returncode, 0)
        self.assertEqual(run("baseline", "--execute", "--before-edit", "--out", str(self.baseline)).returncode, 2)
        self.assertEqual(run("verify", "--execute", "--out", str(self.root / ".agent-quality" / "missing.json")).returncode, 2)
        self.assertEqual(run("verify", "--execute", "--baseline", str(self.baseline), "--out", str(self.baseline)).returncode, 2)


class Parsers(unittest.TestCase):
    def test_node_test_summary_zero_skipped_and_inconsistent(self):
        def output(tests=2, passed=2, failed=0, skipped=0):
            return f"TAP version 13\n1..{tests}\n# tests {tests}\n# suites 0\n# pass {passed}\n# fail {failed}\n# cancelled 0\n# skipped {skipped}\n# todo 0\n"
        root = Path.cwd().resolve()
        self.assertEqual(q.node_test_summary(output(), 0)["tests"], 2)
        self.assertEqual(q.parse_output(root, "node-test-tap", output(), "", 0), [])
        for text, code in ((output(0, 0), 0), (output(2, 1, 0, 1), 0), (output(2, 2, 1), 0), ("ok", 0), (output(), 1)):
            with self.assertRaises(ValueError):
                q.parse_output(root, "node-test-tap", text, "", code)

    def test_tsc_strict(self):
        root = Path.cwd().resolve()
        out = "source.ts(2,3): error TS2322: Type 'number' is not assignable to type 'string'.\n"
        self.assertEqual(len(q.parse_output(root, "tsc", out, "", 2)), 1)
        for stdout, stderr, code in (("unknown", "", 1), ("", "", 2), ("", "error", 1), (out, "", 0)):
            with self.assertRaises(ValueError):
                q.parse_output(root, "tsc", stdout, stderr, code)

    def test_eslint_malformed_and_outside_path(self):
        root = Path.cwd().resolve()
        for text in ("{}", "not-json", '[{"filePath":"../outside.js","messages":[]}]', '[{"filePath":"x.js","messages":[{"fatal":true}]}]'):
            with self.assertRaises(ValueError):
                q.parse_output(root, "eslint-json", text, "", 1)

    def test_multiset(self):
        one = {"identity": "a", "path": "x"}
        before = {"status": "complete", "command": {}, "findings": [one]}
        after = {"id": "lint", "kind": "lint", "adapter": "eslint-json", "status": "complete", "command": {}, "findings": [one, one]}
        snap = {"files": {"x": {"sha256": "hash"}}}
        result = q.compare_check(before, after, snap, snap)
        self.assertEqual(len(result["historical"]), 1)
        self.assertEqual(len(result["introduced"]), 1)


if __name__ == "__main__":
    unittest.main()
