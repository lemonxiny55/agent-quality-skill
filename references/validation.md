# Release validation — 0.1.0

Date: 2026-10-20. Candidate status: **PUBLIC SOURCE RELEASE READY / AGENSI SUBMISSION READY**, limited to the verified scope in this file. No Agensi upload or server acceptance is claimed.

## Fresh verification

| Check | Result | Public evidence |
| --- | --- | --- |
| Skill structure | `validate_skill.py` and package extraction smoke check passed | [Windows tests](https://github.com/lemonxiny55/agent-quality-skill/blob/main/evidence/release/tests-windows.json) · [Linux tests](https://github.com/lemonxiny55/agent-quality-skill/blob/main/evidence/release/tests-linux.json) |
| Windows suite | Python 3.13.9, 34 tests; 31 passed, 3 skipped | [Raw test record](https://github.com/lemonxiny55/agent-quality-skill/blob/main/evidence/release/tests-windows.json) |
| Linux suite | Ubuntu 24.04 WSL, Python 3.12.3, 34 tests passed | [Raw test record](https://github.com/lemonxiny55/agent-quality-skill/blob/main/evidence/release/tests-linux.json) |
| Real-tool Windows demo | ESLint 9.39.5, TypeScript 5.9.3, Node 24.19.0; regression detected, repair returned `no_new_observed`; 2 historical findings retained; 2/2 Node tests passed | [Sanitized receipts and command output](https://github.com/lemonxiny55/agent-quality-skill/tree/main/evidence/release/demo-windows) · [Replay audit](https://github.com/lemonxiny55/agent-quality-skill/blob/main/evidence/release/demo-windows-audit.json) |
| Real-tool Linux demo | Same pinned tools and outcomes in Ubuntu 24.04 WSL Linux userspace | [Sanitized receipts and command output](https://github.com/lemonxiny55/agent-quality-skill/tree/main/evidence/release/demo-linux) · [Replay audit](https://github.com/lemonxiny55/agent-quality-skill/blob/main/evidence/release/demo-linux-audit.json) |
| Full host Skill E2E | Codex CLI 0.163.0-alpha.10.2 on Windows; explicit skill load, same environment, requested rename only, 2/2 tests, freshness check passed | [Independent audit summary](https://github.com/lemonxiny55/agent-quality-skill/blob/main/evidence/release/agent-e2e-codex.json) |
| Claude Code quality CLI workflow (partial) | CLI 2.1.226, Windows 11, reported runtime model Fable 5 (not requested Sonnet). Receipts show baseline, injected lint/test regression, repair, 2/2 tests, and missing/corrupt baseline `incomplete`. The run report says native Skill invocation was unavailable; agent manually read `SKILL.md` and ran the CLI. This does not verify native Claude Skill discovery/invocation. The raw CLI event transcript was not provided. | [Sanitized receipts, metadata and replay audit](../evidence/release/agent-e2e-claude/summary.json) |
| Agensi ZIP | Root `SKILL.md`, free MIT, scripts/references/example present, under 50 MB, extracted and validated | See generated `dist/agent-quality-skill-0.1.0.zip.json` locally; its SHA-256 is supplied with the final delivery |

The Windows skips are one POSIX-only SIGTERM test and two symlink tests unavailable to this Windows user. All three passed in Linux. Linux is real Ubuntu 24.04 WSL userspace on a Windows-mounted filesystem, not a native Linux host. GitHub Actions' Python 3.10/3.13 matrix is authored but not run in GitHub.

## Compatibility boundary

Codex CLI is the only host with a fully verified native Skill invocation. A Claude Code 2.1.226 run report and replayed receipts support the quality CLI workflow, but the report says the native Skill command was unavailable and the agent manually read the Skill file; the runtime-reported Fable model also differed from the requested Sonnet. Claude Code native Skill discovery/invocation is therefore **not verified**. Cursor and GitHub Copilot were not tested. Their discovery paths are documentation-only. No lifecycle interception, automatic blocking, or automatic repairs are included.

## Privacy and evidence

Raw Codex/Claude transcripts and old receipts containing local paths and per-variable hashes remain outside the public tree. The Claude run's quality receipts are published after machine-path redaction and integrity resealing; the raw Claude event transcript was not provided, so the model and Skill-discovery details in its summary are attributed to the returned run report. A later PowerShell check of the final receipt verified its artifact hash but returned stale because that process had a different aggregate environment fingerprint than the reported Git Bash run; it does not reproduce the run's same-session freshness result. The published demo evidence is similarly path-redacted and resealed. The Codex audit summary is backed by a local transcript whose SHA-256 is recorded, while that transcript itself is withheld.

The CLI records one aggregate environment fingerprint to check comparability; it no longer writes variable names or individual variable hashes to receipts. See [evidence contract](evidence-contract.md), [compatibility](compatibility.md), and [Agensi listing copy](agensi-listing.md).
