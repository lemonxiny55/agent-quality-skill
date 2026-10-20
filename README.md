# Agent Quality Skill

English | [简体中文](README.zh.md)

**Fix what the agent broke. Ignore what was already broken. Prove the change is clean.**

A free, MIT-licensed Agent Skill with a local evidence CLI. Capture the real working
state before a coding task, run the repository's lint/typecheck/tests after it, and
keep historical failures separate from newly observed findings when the evidence
allows it. No DSH runtime, telemetry, account or network service is required by the CLI.

Inspired by [dsh-lint-loop](https://github.com/lemonxiny55/dsh-lint-loop), the
change-aware quality loop for DeepSeek Harness. Using DSH? Explore that original
plugin for integrated edit feedback, lifecycle steering and safe repair.

## Install

Requires Python 3.10+, Git, a repository with a commit and its checking tools already
installed. Clone this repository, run `python scripts/package_skill.py`, inspect the
result in `dist/`, then extract the ZIP's **contents** into one of these directories:

| Agent | Project installation |
| --- | --- |
| Codex CLI | `.agents/skills/agent-quality-skill/` |
| Claude Code | `.claude/skills/agent-quality-skill/` |
| Cursor Agent | `.cursor/skills/agent-quality-skill/` |
| GitHub Copilot | `.github/skills/agent-quality-skill/` |

The resulting path must be `.../agent-quality-skill/SKILL.md`. Personal installation
paths and actual verification status are in [compatibility](references/compatibility.md).
**Verified:** Codex CLI 0.163.0-alpha.10.2 on Windows, explicit Skill invocation.
Claude Code's attempted run was blocked by API connection failure; Cursor and
Copilot were not run. Only the recorded Agent/OS combination is an E2E claim; documented discovery paths
for other hosts are not test results. The ZIP itself is not a published listing.

## Use

Invoke `$agent-quality-skill` in Codex or `/agent-quality-skill` in Claude Code
**before making task edits**, or ask your Agent to read the installed SKILL.md.
Let it review your existing checks and prepare
`.agent-quality.json` in the target repository. See the
[configuration guide](references/configuration.md) and the complete
[Node example](examples/node/.agent-quality.json).

Use absolute paths, quoted as needed. Replace `/skill` and `/repo` below. On Windows,
use the installed `python` or `py -3` command and actual Windows paths.

```sh
python /skill/scripts/quality.py plan --repo /repo
python /skill/scripts/quality.py baseline --repo /repo --before-edit --execute --out /repo/.agent-quality/task-001.before.json
# Now perform the requested code changes.
python /skill/scripts/quality.py verify --repo /repo --baseline /repo/.agent-quality/task-001.before.json --execute --out /repo/.agent-quality/task-001.receipt.json
python /skill/scripts/quality.py check-receipt --repo /repo --receipt /repo/.agent-quality/task-001.receipt.json
```

Review the plan before `--execute`. These commands run repository code with the
current user's privileges and normal Agent permissions. The CLI never fixes code,
installs dependencies, stashes work, resets files or changes your Git index.
Pre-existing staged, unstaged and untracked work is allowed. Use a new baseline
filename for each task; baselines cannot be overwritten.

Already edited without a baseline? Run `verify` without `--baseline`. It records
current checks and reports `incomplete`; never invent a late baseline or substitute HEAD.

## Read a receipt

| Verdict | Meaning |
| --- | --- |
| `no_new_observed` | No new findings observed by the configured checks, within the recorded scope and trust assumptions |
| `regression` | Newly observed diagnostics or a green-to-failed command; causal authorship is unknown |
| `incomplete` | Missing/invalid baseline, unsupported output, uncertain historical attribution, failed test baseline, skipped category, timeout, missing tool or partial evidence |

Receipts contain real commands, cwd, tool entry hashes, raw stdout/stderr, exits,
timings, content hashes, exclusions, historical/new/unclassified findings and reasons.
Matching historical diagnostics require an unchanged diagnostic file. Changed legacy
files are handled conservatively. Node TAP records counts and rejects zero/skipped/
cancelled/todo tests. Failed test commands cannot be matched by individual case;
two failing runs are incomplete. Generic `exit` tests checks always leave the
receipt incomplete. Inspect test output and coverage; exit zero alone is insufficient.

Exit status: 0 for a ready baseline/no-new-observed result, 1 for a regression,
2 for incomplete evidence or invocation error. For `check-receipt`, exit zero means
freshness only: inspect `effectiveVerdict` too.

## Real evidence and reproduction

The checked-in [validation record](references/validation.md) links raw Windows/Linux
test logs, real-tool receipts and the audited Codex E2E summary. The original Agent
transcript and local invocation details are withheld. Archived receipts belong to the workspaces in which they were captured; they do not certify this clone.

To run the real demo from this source directory:

```sh
python scripts/demo.py --install --evidence evidence/my-demo
```

This explicitly permits `npm ci --ignore-scripts` in a **new disposable repository**.
The pinned example starts with one historical lint error and one historical type
error, adds real lint/type/test regressions, repairs only the new changes and checks
missing-baseline and stale-receipt behavior. Raw output is saved without inventing
tool results. Unit-test protocol fixtures are labeled separately from this demo.

To run the suite and create a candidate:

```sh
python scripts/validate_skill.py .
python scripts/record_tests.py --out evidence/my-tests.json
python scripts/package_skill.py
```

The ZIP has SKILL.md at its root, is bounded below 50 MB, and includes the runtime
CLI, instructions, license, and Node example. Test suites and machine-specific
verification records stay in the GitHub source repository, not in the install bundle.
Build metadata includes a SHA-256 and extraction is checked. Agensi's server
acceptance has not been tested.

## Compared with dsh-lint-loop

| | Agent Quality Skill | Original dsh-lint-loop |
| --- | --- | --- |
| Runtime | Python stdlib CLI + host terminal tools | DSH plugin |
| Trigger | Explicit Agent workflow; relevance discovery depends on host | Integrated DSH edit and lifecycle behavior |
| Baseline | Caller captures before task edits; timing is attested | Host-integrated baseline capture |
| Repair | No automatic repair | DSH-specific safe repair facilities |
| Scope | Explicit checks; ESLint JSON, tsc text, Node TAP tests | Broader plugin-specific detection and integrations |
| Receipts | Portable local JSON | Integrated DSH quality receipt tools |

This is a separate implementation, not the original plugin in a ZIP. No unpublished
v0.7 package is required. The original project and its PR #8 are not modified.

## Limits and listing status

This is not a universal auto-blocking plugin. No lifecycle adapters, semantic
authorship proof, full test discovery, automatic impact selection or universal Agent
support are claimed. The baseline and receipt hashes are unsigned, not tamper-proof.
Git-ignored untracked inputs, transitive installed dependencies and external services
are not fully captured. Keep tools/dependencies fixed, use a single writer and read
the exact [evidence contract](references/evidence-contract.md).

[Research and primary sources](references/feasibility.md) ·
[Compatibility](references/compatibility.md) · [Verification](references/validation.md) ·
[Agensi copy and discovery plan](references/agensi-listing.md)

Status: **PUBLIC RELEASE / AGENSI SUBMISSION READY**, scoped to the verified Codex workflow and
documented limitations in the validation record. This does not certify the three
unverified primary hosts or Agensi acceptance. No marketplace submission, price setting or
public promotional message is performed by the project scripts.

MIT © 2026 lemonxiny55. [License](LICENSE) · [Origin attribution](NOTICE).
