# Agent and OS compatibility

A supported SKILL.md discovery folder is not a successful Agent E2E result.

| Host | Discovery path documented | Real E2E status |
| --- | --- | --- |
| Codex CLI 0.163.0-alpha.10.2, Windows | `.agents/skills/agent-quality-skill/` | **Verified for one isolated task**: explicit invocation, baseline before edit, requested rename only, 2/2 configured tests, receipt freshness passed. See [audit summary](https://github.com/lemonxiny55/agent-quality-skill/blob/main/evidence/release/agent-e2e-codex.json). Automatic selection and hooks were not tested. |
| Claude Code CLI 2.1.226, Windows 11 | `.claude/skills/agent-quality-skill/` | **Native Skill invocation verified for one isolated task**: task prompt event 7 began with `/agent-quality-skill`; the JSONL trace records a successful `Skill(agent-quality-skill)` call, then plan, before-edit baseline, source/test edits, verify and receipt check. ESLint, TypeScript and TAP commands each passed; the overall receipt was honestly `incomplete` because the configured TAP entry file changed after baseline, so this run does not establish `no_new_observed`. The transcript model field is `glm-5.2`; the UI was reported as “Fable 5” and the user clarified the provider/model is Chinese and not Anthropic. Labels are retained with provenance and are not reconciled. See [sanitized event evidence](../evidence/release/agent-e2e-claude-native/events.json) and [summary](../evidence/release/agent-e2e-claude-native/summary.json). Prior manual-SKILL.md workflow evidence remains separately available at [the earlier audit](../evidence/release/agent-e2e-claude/summary.json). |
| Cursor Agent | `.cursor/skills/agent-quality-skill/` | Documentation-only; no real Cursor session tested. |
| GitHub Copilot agent mode / CLI | `.github/skills/agent-quality-skill/` | Documentation-only; no real Copilot session tested. Read-only surfaces cannot execute this workflow. |
| Other Agent Skills hosts | Host-specific folder named `agent-quality-skill` | Not verified; no universal compatibility claim. |

The ZIP has files at its root, not an enclosing directory. Extract its contents into a directory named `agent-quality-skill`, so `SKILL.md`, `scripts/` and `references/` are immediate children. Use one install location per host to avoid duplicate or stale skill copies. Explicit invocation is preferred for the first task; automatic relevance selection is host-dependent and untested.

The CLI itself was exercised on Windows 11 with Python 3.13.9 and Ubuntu 24.04 WSL with Python 3.12.3, Git, Node 24.19.0, ESLint 9.39.5 and TypeScript 5.9.3. A reported Claude Code workflow used the same Windows tool versions. WSL is real Linux userspace on a Windows-mounted filesystem, not native Linux CI or a distro sweep. Python 3.10+ is the declared requirement; Python 3.10 was not run in this session.

No host-specific hooks, completion blocking or automatic source repairs are shipped.
