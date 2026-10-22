# Public release evidence

These files preserve the current Windows/Linux test runs and real-tool demo receipts.
Machine-specific repository/home paths were removed from public demo command evidence by
retaining only the operation sequence and exit codes. Receipt paths were replaced with generic
paths and hashes were recomputed; receipts remain unsigned. Original raw logs remain local.

The successful Codex CLI E2E was independently audited from a raw local transcript.
Its summary and transcript SHA-256 are public; the original transcript, invocation paths,
and raw agent logs are kept locally and are intentionally excluded from this repository.
Claude Code's failed connection attempt is documented without its host-specific raw log.

Reproduce tests and demos from a clean clone using the commands in
`references/validation.md`. The demo fixture uses pinned npm dependencies.
