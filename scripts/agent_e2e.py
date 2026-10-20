#!/usr/bin/env python3
"""Run an installed Skill with a real Claude Code or Codex CLI in a NEW repo."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=("claude", "codex"), default="claude")
    parser.add_argument("--execute-agent", action="store_true", help="use the configured Claude login for one real evaluation")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--dependencies-from", type=Path, required=True, help="reuse this demo repo's already installed node_modules")
    args = parser.parse_args()
    if not args.execute_agent:
        parser.error("explicit --execute-agent required")
    work = ROOT / ".work" / (args.agent + "-e2e-" + uuid.uuid4().hex[:10])
    args.evidence.mkdir(parents=True, exist_ok=True)
    evidence = args.evidence.resolve()
    shutil.copytree(ROOT / "examples" / "node", work, ignore=shutil.ignore_patterns("node_modules", ".agent-quality", ".git"))
    shutil.copytree(args.dependencies_from / "node_modules", work / "node_modules")
    skill = work / (".claude" if args.agent == "claude" else ".agents") / "skills" / "agent-quality-skill"
    skill.mkdir(parents=True)
    shutil.copy2(ROOT / "SKILL.md", skill / "SKILL.md")
    for folder in ("scripts", "references"):
        shutil.copytree(ROOT / folder, skill / folder, ignore=shutil.ignore_patterns("__pycache__"))
    # Disable unrelated project customizations; normal per-tool permissions stay active.
    for argv in (["git", "init", "-b", "main"], ["git", "add", "."],
                 ["git", "-c", "user.name=Agent Evaluation", "-c", "user.email=eval@example.invalid", "commit", "-m", "isolated agent fixture"]):
        subprocess.run(argv, cwd=work, capture_output=True, check=True)
    claude = shutil.which("claude.exe") or shutil.which("claude")
    if args.agent == "codex":
        codex = shutil.which("codex.exe") or shutil.which("codex")
        script = Path(shutil.which("node")).parent / "node_modules/@openai/codex/bin/codex.js"
        if codex and Path(codex).suffix.lower() not in (".cmd", ".ps1"):
            launcher = [codex]
        elif script.is_file():
            launcher = [shutil.which("node"), str(script)]
        else:
            raise RuntimeError("cannot resolve Codex native executable or codex.js")
    elif not claude or Path(claude).suffix.lower() in (".ps1", ".cmd"):
        # Standard npm installation used on this Windows host.
        package = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/claude-code/node_modules/@anthropic-ai/claude-code"
        native = package / "bin" / "claude.exe"
        cli = package / "cli.js"
        if native.is_file():
            launcher = [str(native)]
        elif cli.is_file():
            launcher = [shutil.which("node"), str(cli)]
        else:
            raise RuntimeError("cannot resolve native Claude executable or npm cli.js")
    else:
        launcher = [claude]
    prompt = (("/agent-quality-skill " if args.agent == "claude" else "Use $agent-quality-skill. ") + "Rename add(a, b) parameters in src/calculator.mjs to left and right, "
              "keeping the same addition behavior. Use this installed skill and the existing .agent-quality.json "
              "to verify the task. Save your task baseline and final Quality Receipt in .agent-quality/. "
              "Do not alter the legacy fixtures or any unrelated configuration. "
              "Run your Python commands using the absolute interpreter path " + sys.executable.replace("\\", "/") + ". "
              "You are authorized to execute the reviewed local check plan in this disposable repository. "
              "Preserve the same execution environment and permission context across baseline and verification; "
              "you may orchestrate CLI capture, the requested edit, and CLI verification sequentially inside "
              "one terminal Python process to keep the environment identical. Never recapture after editing. "
              "Report the actual evidence and limitations.")
    argv = [*launcher, "-p", prompt, "--output-format", "stream-json", "--verbose", "--no-session-persistence",
            "--setting-sources", "project", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
            "--permission-mode", "acceptEdits", "--allowedTools", "Bash,Read,Edit,Write,Skill,Glob,Grep",
            "--tools", "Bash,Read,Edit,Write,Skill,Glob,Grep", "--max-budget-usd", "3"]
    if args.agent == "codex":
        argv = [*launcher, "exec", "--json", "--ephemeral", "--approve-for-me", "-C", str(work), prompt]
    version = subprocess.run([*launcher, "--version"], capture_output=True, text=True, check=True).stdout.strip()
    (evidence / "invocation.json").write_text(json.dumps({"argv": argv, "cwd": str(work), "version": version,
            "permissions": "acceptEdits with local tools allowed" if args.agent == "claude" else "workspace-write with automatic approval review; no sandbox bypass",
            "skillSha256": hashlib.sha256((skill / "SKILL.md").read_bytes()).hexdigest()}, indent=2), encoding="utf-8")
    started = time.monotonic()
    stdout = evidence / "transcript.jsonl"
    stderr = evidence / "stderr.txt"
    with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
        process = subprocess.Popen(argv, cwd=work, stdout=out, stderr=err, stdin=subprocess.DEVNULL)
        try:
            code = process.wait(timeout=480)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
            else:
                process.kill()
            code = -1
    artifacts = []
    state = work / ".agent-quality"
    if state.exists():
        for path in state.glob("*.json"):
            shutil.copy2(path, evidence / path.name)
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
                artifacts.append({"file": path.name, "artifact": item.get("artifact"), "verdict": item.get("verdict"), "integritySha256": item.get("integritySha256")})
            except ValueError:
                pass
    diff = subprocess.run(["git", "diff", "--", "src/calculator.mjs", "src/legacy.js", "types/legacy.ts"], cwd=work, capture_output=True, text=True, check=True).stdout
    (evidence / "change.diff").write_text(diff, encoding="utf-8")
    summary = {"version": version, "exitCode": code, "elapsedSeconds": round(time.monotonic() - started, 2),
               "work": str(work), "artifacts": artifacts, "status": "requires transcript audit", "transcriptSha256": hashlib.sha256(stdout.read_bytes()).hexdigest()}
    (evidence / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
