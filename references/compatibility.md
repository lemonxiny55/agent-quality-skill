# Agent and OS compatibility

The folder name and SKILL.md frontmatter name must both be `delta-receipt`. The ZIP
contains files at its root; extract its contents so the Skill file is directly at
`<host-skill-dir>/delta-receipt/SKILL.md`.

| Host | Project install | Personal install | DeltaReceipt v0.2.0 result |
| --- | --- | --- | --- |
| [Codex CLI](https://developers.openai.com/codex/skills) | `.agents/skills/delta-receipt/` | `~/.agents/skills/delta-receipt/` | Explicit `$delta-receipt` invocation passed with Codex CLI 0.163.0-alpha.11 in an isolated Windows project. Baseline and verification shared the same environment fingerprint; only the requested calculator parameter rename was made; 2/2 tests passed; the audited receipt was `no_new_observed` with two historical findings retained. Automatic selection was not tested. |
| [Claude Code](https://code.claude.com/docs/en/skills) | `.claude/skills/delta-receipt/` | `~/.claude/skills/delta-receipt/` | One bounded retry with Claude Code CLI 2.1.226 ended after ten internal API retries with `ConnectionRefused` before task execution, producing no artifacts. Package extraction and the four CLI/import entry points are tested; native Claude invocation remains externally blocked and unverified. |
| Cursor Agent | `.cursor/skills/delta-receipt/` | — | Documentation path only; no Cursor session tested. |
| GitHub Copilot agent mode / CLI | `.github/skills/delta-receipt/` | — | Documentation path only; no Copilot session tested. Read-only surfaces cannot execute this workflow. |
| Other Agent Skills hosts | Host-specific folder named `delta-receipt` | Host-specific | Not verified; no universal compatibility claim. |

Codex user skills are installed under `$HOME/.agents/skills`; Claude Code supports
project `.claude/skills` and personal `~/.claude/skills` locations. See the linked
official documentation for host-specific discovery rules.

The historical Codex native invocation record is available at [the v0.1.0 audit
summary](https://github.com/lemonxiny55/delta-receipt/blob/main/evidence/release/agent-e2e-codex.json).
The historical Claude task used `/agent-quality-skill` and recorded an `incomplete`
receipt because a configured test entry file changed after baseline; see its
[original minimized event evidence](../evidence/release/agent-e2e-claude-native/events.json)
and [summary](../evidence/release/agent-e2e-claude-native/summary.json). Those
artifacts were not relabeled or edited during the rebrand.

For project installs, keep one active copy per host to avoid duplicate or stale
discovery. Explicit invocation is preferred for the first task; automatic relevance
selection and hooks are host-dependent and untested.

The CLI supports Python 3.10+ and requires Git. Its cross-platform CI matrix runs
Windows and Ubuntu with Python 3.10 and 3.13. The saved v0.1.0 manual validation
record also covers Windows 11 and Ubuntu 24.04 WSL; WSL is not native Linux CI.
No host lifecycle hooks, completion blocking, or automatic source repairs are
shipped.
