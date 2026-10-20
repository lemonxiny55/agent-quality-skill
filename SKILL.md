---
name: agent-quality-skill
description: Use when preparing code changes or verifying an agent task with repository lint, typecheck and tests, especially when pre-existing failures need separation from newly observed findings. Captures a pre-edit baseline and produces a conservative, inspectable Quality Receipt through a local CLI.
license: MIT
---

# Agent Quality Skill

**Fix what the agent broke. Ignore what was already broken. Prove the change is clean.**

This is an explicitly orchestrated workflow with executable evidence collection.
It does not install lifecycle hooks, intercept edits, block completion, or prove
authorship. Automatic skill selection is a host feature, not an execution guarantee.

## Run the workflow

Requirements: Python 3.10+, Git, a repository with at least one commit, and the
repository's installed checking tools. No DSH runtime is needed.

1. Locate this skill directory and the target Git root. Read its existing checking
   commands and configuration. Read [configuration.md](references/configuration.md)
   to prepare `.agent-quality.json` at the **target repository root**, using
   repository-owned lint, typecheck and test commands. Preserve user work. Include
   all checks relevant to the change; the CLI cannot establish tool coverage for you.
2. Inspect the configuration and `plan` output before running commands. Honor the
   user's existing authorization and host permission rules. `--execute` records
   an explicit execution choice; it does not grant permissions or sandbox commands.
   Tools, plugins and tests execute repository code. Avoid fix/install/watch modes.
3. **Before task edits**, capture a fresh session baseline. Existing uncommitted
   changes are allowed and become part of that baseline. `--before-edit` attests
   timing; the CLI cannot independently verify that it predates the task. Use the
   same execution environment and permission context for capture and verification;
   a host's sandbox/elevation switch can invalidate comparability. A single terminal
   process can preserve the environment across an automated baseline/edit/verify task.
4. Make only the requested edits. Verify against that same session baseline.
   Read the receipt's actual stdout/stderr, exits, comparisons and reasons.
5. Repair confirmed in-scope regressions only with user authorization, then verify
   again against the original baseline. No automatic source repairs are provided.
6. Run `check-receipt` just before reporting. Summarize verdict, changed paths,
   executed checks, historical findings, new findings, unknowns and artifact paths.

Example commands (replace `/skill` and `/repo` with real absolute paths; quote
paths with spaces; on Windows use the available `python` or `py -3` command):

```sh
python /skill/scripts/quality.py plan --repo /repo
python /skill/scripts/quality.py baseline --repo /repo --before-edit --execute --out /repo/.agent-quality/task-001.before.json
# Perform the user's task only after baseline capture.
python /skill/scripts/quality.py verify --repo /repo --baseline /repo/.agent-quality/task-001.before.json --execute --out /repo/.agent-quality/task-001.receipt.json
python /skill/scripts/quality.py check-receipt --repo /repo --receipt /repo/.agent-quality/task-001.receipt.json
```

## Evidence contract

| Observation | Required report |
| --- | --- |
| Valid baseline and complete, comparable executions with no new findings | `no_new_observed`, limited to configured checks and recorded scope |
| New diagnostic or green-to-failed command | `regression`; observed during the interval, authorship unknown |
| Missing/expired/invalid baseline | `incomplete`; current checks alone cannot prove no new regressions |
| Repeated diagnostic in a changed file | Unclassified; no historical-debt exemption |
| Both baseline and final generic test commands fail | `incomplete`; exit codes cannot isolate individual failures |
| Missing tool, timeout, cancellation, malformed output, changed tool/config/environment, check side effects, skipped category or partial snapshot | `incomplete` with actual reason |

If edits already happened without a credible pre-edit capture, run `verify`
without `--baseline` and report the incomplete receipt. **Do not create a late
baseline, use HEAD as a substitute, reset/stash the workspace, or copy results
from another session.** A receipt copied from a different environment is archival
evidence, not a fresh result for the current workspace.

Do not repair legacy debt just to make checks green. Do not equate Git dirty
paths with agent authorship, infer that an exit-zero test command ran tests, or
claim universal absence of regressions. Verify the runner's output for test
counts, skips and discovery scope. The Node TAP adapter records test counts and
rejects zero/skipped/cancelled/todo tests. A generic `exit` tests check remains
incomplete; it does not prove that tests ran. Other test frameworks need a real
adapter and validation before receiving complete test coverage.

The receipt is unsigned. Its hash detects accidental corruption; it cannot stop
someone rewriting the artifact and recomputing its hash. Snapshots are bounded
observations, not an atomic filesystem or a hostile-writer monitor. See
[evidence-contract.md](references/evidence-contract.md) for exclusions and trust.

## Host integration and origins

See [compatibility.md](references/compatibility.md) for supported discovery paths
and the distinction between documentation support and real Agent tests.

This portable implementation is inspired by the MIT-licensed
[dsh-lint-loop](https://github.com/lemonxiny55/dsh-lint-loop). For integrated DSH
edit feedback, lifecycle steering and safe repair capabilities, visit that
original plugin. This skill does not ship those DSH-specific integrations.
