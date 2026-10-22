# Public release evidence

These files preserve the current Windows/Linux test runs and real-tool demo receipts.
Machine-specific repository/home paths were replaced with generic paths; receipt hashes
were recomputed after redaction and remain unsigned. Do not treat them as signatures.

The successful Codex CLI E2E was independently audited from a raw local transcript.
Its summary and transcript SHA-256 are public; the original transcript, invocation paths,
and raw agent logs are kept locally and are intentionally excluded from this repository.
The earlier Claude manual-workflow receipts and replay audit remain in
`agent-e2e-claude/`. Their public copies replace machine paths in structured fields,
object keys, and nested command output with synthetic placeholders; hashes were
recomputed, and original receipts remain local. Claude Code's failed connection attempt
is documented without its host-specific raw log. A later Claude Code 2.1.226 native Skill
task is documented in `agent-e2e-claude-native/`; its raw JSONL transcript was audited
locally and withheld because it contains broader session context. The public minimized
timeline proves the slash invocation and successful native Skill tool call, while the
overall quality receipt remains `incomplete` because a configured test entry changed
after baseline.

Reproduce tests and demos from a clean clone using the commands in
`references/validation.md`. The demo fixture uses pinned npm dependencies.
