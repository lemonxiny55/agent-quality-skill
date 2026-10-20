# Feasibility and source register

Research date: 2026-10-20. Decision: **feasible as an explicitly invoked Skill plus
CLI**. A portable Skill cannot guarantee before-edit capture or enforce an Agent's
completion lifecycle. Those claims require a separately implemented and tested host
adapter. This MVP ships no lifecycle hook adapters.

## Shared core and optional host facilities

| Capability | Portable core in an Agent with terminal/file tools | Host-specific enhancement | DSH integration not migrated |
| --- | --- | --- | --- |
| Discovery | Name/description YAML + SKILL.md body, supporting files | Per-host installation directories, slash commands, automatic relevance selection | Cordis plugin registration |
| Run tools | Agent calls local CLI under normal terminal permissions | Tool preapproval fields and sandbox policies vary | `ctx.tools.register`, model-visible DSH tools |
| Workspace access | Explicit Git root, source snapshots, dirty starting work | Remote/cloud workspaces have different filesystem and tool availability | DSH workingDirectory service and actor/session binding |
| Before/after identity | Caller captures baseline before edits, then verifies | PreToolUse-like hooks can trigger capture if correctly configured | Canonical DSH file-tool before/after bytes and event observation |
| Lint/types/tests | Explicit installed command argv, recorded stdout/exits | Automatic impact analysis or IDE diagnostics require adapters | Plugin tool dispatch and repair pipeline |
| Lifecycle | Agent instructed to invoke verification before reporting | Host hook APIs differ; installation/configuration is separate | Awaited `agent/turn-stopping`, bounded steering and turn-end cancellation |
| Permissions | No automatic fixes or installs; inspect commands and use host authorization | Host allow/deny and organization policies differ | DSH-owned execution/session permission context |

“Shared” assumes a coding Agent session with local file and command execution tools.
Read-only review modes or cloud sessions without Python/Git cannot run the CLI.
Automatic relevance selection does not establish that a baseline ran before edits.

## Primary sources

- [Agent Skills specification](https://agentskills.io/specification): folder with
  SKILL.md, required name/description YAML; optional resources. Tool execution is
  provided by the host. The name must match its directory, be at most 64 characters,
  and the description at most 1,024. The portable package uses only name,
  description and license; no host-specific frontmatter.
- [Claude Code skills](https://code.claude.com/docs/en/skills): project
  `.claude/skills/` and personal `~/.claude/skills/`; explicit `/skill-name` and
  relevance selection. Additional fields, injected commands and skill-local hook
  behavior are Claude extensions; omitted here. Normal execution permissions apply.
- [Claude Code hooks](https://code.claude.com/docs/en/hooks): distinct hook events
  can observe tools or affect continuation; they require configured handlers.
  This is evidence of an optional integration surface, not shipped support.
- [Cursor skills](https://cursor.com/docs/skills): project `.cursor/skills/` and
  `.agents/skills/`, corresponding user locations and compatibility directories;
  skills can include scripts. Local personal skills have separate cloud sync rules.
  Installing a folder locally does not automatically install it remotely.
- [Cursor hooks](https://cursor.com/docs/hooks): separate lifecycle extension API;
  event payloads and control capabilities must be tested independently.
- [Copilot skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
  and [adding skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills):
  `.github/skills/`, `.claude/skills/`, `.agents/skills/` project discovery;
  personal `.copilot/skills/` or `.agents/skills/`. Supports scripts through host tools.
  Capabilities vary by product surface; do not generalize a CLI test to all IDE modes.
- [Copilot hooks](https://docs.github.com/en/copilot/concepts/agents/hooks): distinct
  hooks feature, not an automatic consequence of including SKILL.md.
- [Codex skill evaluation](https://developers.openai.com/blog/eval-skills) and
  [noninteractive execution](https://learn.chatgpt.com/docs/non-interactive-mode):
  explicit skill invocation and JSONL tool events provide an auditable extra target.
  The installed CLI help was also inspected; its actual executed version is recorded
  in the invocation evidence, rather than inferred from another shim on PATH.
- [ESLint CLI](https://eslint.org/docs/latest/use/command-line-interface): JSON
  formatting and nonzero exit meanings inform the strict lint adapter.
- [TypeScript CLI](https://www.typescriptlang.org/docs/handbook/compiler-options.html):
  noEmit and pretty flags inform the conservative text diagnostic adapter.
- [Original dsh-lint-loop](https://github.com/lemonxiny55/dsh-lint-loop): studied
  the change-aware quality principle, per-session baseline, historical debt,
  bounded verification and receipt concepts. Local v0.7 design files were read
  only; this independent implementation does not load its source or candidate bundle.

## Agensi constraints and evidence status

[Agensi sell page](https://agensi.io/sell) was requested and attempted twice by the
research browser; it returned an internal fetch error. The following are **operator
requirements supplied by the user**, not independently confirmed current platform
behavior: ZIP <=50 MB, SKILL.md at archive root, valid name/description, scripts /
references / assets allowed, free listing and original GitHub links allowed.

The packager enforces those local constraints and validates extraction. No listing
has been submitted and no server-side acceptance is claimed. The current candidate
has no paid feature, license check, telemetry, account requirement or runtime network
service. Development dependency installation and real Agent evaluation use their
respective network services; they are not requirements of the shipped CLI.

## MVP choice and tradeoffs

Use a Python standard-library CLI for Windows/Linux subprocess management and JSON
evidence, rather than binding to one Agent's SDK. First-class diagnostic adapters
are ESLint JSON and plain TypeScript diagnostics; tests use the installed command's
exit status with explicit limits. Full configured scopes are checked each time;
there is no inferred impact graph or automatic language/framework proliferation.
The stricter changed-file rule sacrifices some debt deduplication to avoid silently
exempting a changed diagnostic. Generic failed-test baselines remain incomplete.
No claim of semantic equivalence, complete test discovery or causal authorship is made.
