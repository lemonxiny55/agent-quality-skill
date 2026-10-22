# CLI configuration

The CLI never auto-installs tools or guesses a safe command from a package script.
Prepare `.agent-quality.json` at the target Git root before capturing the baseline. This name and its `version: 1` format remain stable from Agent Quality Skill v0.1.0; DeltaReceipt does not rename existing project configuration or receipt files.
Reuse its installed tools. Review commands and their transitive behavior; `shell=False`
prevents implicit shell parsing, not execution of malicious repository code.

```json
{
  "version": 1,
  "checks": [
    {"id":"eslint","kind":"lint","adapter":"eslint-json","argv":["node","node_modules/eslint/bin/eslint.js","src","--format","json"],"timeoutSeconds":60},
    {"id":"types","kind":"typecheck","adapter":"tsc","argv":["node","node_modules/typescript/bin/tsc","--noEmit","--pretty","false"],"timeoutSeconds":60},
    {"id":"tests","kind":"tests","adapter":"node-test-tap","argv":["node","--test","--test-reporter=tap","test/calculator.test.mjs"],"timeoutSeconds":60}
  ]
}
```

Windows: use interpreter + script paths instead of `.cmd`, `.bat` or `.ps1`
wrappers; no `npm.cmd`, `npx`, PowerShell quoting, Bash operators or shell strings
are necessary. Relative script arguments are resolved from `--repo`. `argv[0]`
must be on PATH or an absolute executable; use `{python}` for the CLI's interpreter.
Native executables and explicit interpreters work on both operating systems.
The checked-in demo shows real ESLint and TypeScript tools and Node's test runner.

The exact accepted keys are `version`, `checks`, and for each check `id`, `kind`,
`adapter`, `argv`, `timeoutSeconds`. Up to 12 checks; unique identifiers; timeout
0.05–600 seconds per check. At least one lint, typecheck and tests check is needed
for a complete receipt. Multiple packages/checks can be configured explicitly;
automatic monorepo discovery and impacted-test selection are outside this MVP.

Adapters:

- `eslint-json` (lint): JSON array on stdout, default warning threshold, exit 0/1.
  Warnings are also compared. Fatal/configuration errors or stderr are incomplete.
- `tsc` (typecheck): `--noEmit --pretty false`, ordinary file diagnostics and
  indented continuations. Configuration/global diagnostics and unknown output
  are incomplete. Do not use incremental, build, watch or emit modes.
- `node-test-tap` (tests): Node's built-in runner with `--test-reporter=tap`.
  Records tests/pass/fail/cancelled/skipped/todo counts. Missing or contradictory
  summaries, zero tests, cancelled/skipped/todo tests and unexpected stderr are
  incomplete. Compares command outcomes, not individual failed cases.
- `exit` (any category): records command outcome only. A green baseline becoming
  failed is a newly observed command failure. Two failed executions cannot be
  isolated by case and remain incomplete. A green final exit is only an observation
  about that command. A tests check using this adapter makes the overall sweep
  incomplete because exit status cannot prove test execution. Use the Node TAP
  adapter for the verified test path. Other test frameworks are unverified.

Outputs inside the repository must live in reserved `.agent-quality/`; these are
excluded from content snapshots. Do not track source files there. Baselines cannot
be overwritten, and a receipt cannot overwrite its baseline. Store each task's
baseline under a new filename. Maximum baseline age is 24 hours, reducible with
`--max-age SECONDS` on `verify`. Re-capture before the next task, never after it.

Exit codes: 0 = baseline ready / no new observed / receipt fresh / plan emitted;
1 = newly observed regression; 2 = incomplete evidence or invocation error.
`check-receipt` exit 0 means **fresh**, even if the saved verdict was regression
or incomplete: inspect `effectiveVerdict`. It does not re-run quality checks.

Each command receives EOF on stdin. Ctrl+C/SIGTERM requests cancellation and a
receipt; external forced termination cannot guarantee a saved artifact. Timeouts
and cancellation kill the process group on Linux and use Windows `taskkill /T /F`.
Detached or privileged descendants may escape OS process-tree cleanup. Commands
have a 1 MiB per-stream output budget, polled every 20 ms (not an absolute disk quota).
Checks are sequential; at most 12 × 600 seconds plus bounded Git/content scans.
