# What a Quality Receipt establishes

`schema: agent-quality/v1`, `artifact: receipt`, `version`, UTC `createdAt`, Git
root, environment digest, check-plan digest, baseline link, changes, scope,
authorship, execution, comparisons, verdict, reasons and claim form the receipt.
`integritySha256` hashes canonical JSON excluding that field. Full executed argv,
resolved executable and file hashes, cwd, start/end/duration, exit code,
status, stdout and stderr are stored for every configured command.

Verdict precedence is regression when a comparable check observes new findings,
otherwise incomplete if there are unknowns, otherwise no_new_observed. A regression
receipt can still contain incomplete comparisons: inspect reasons. The CLI currently
conservatively withholds all delta classification if a sweep is incomplete.

The baseline is a separate, hashed, local artifact. It records pre/post snapshots
of the capture sweep, command executions, HEAD, configuration/environment identity,
and the caller's pre-edit timing attestation. A nonzero diagnostic check can be a
valid baseline if output parses and snapshot coverage is complete. Failed Node TAP
test commands remain usable evidence of failure but cannot establish a clean delta
when they fail again. Generic `exit` tests checks always leave execution evidence
incomplete. Node TAP records counts and rejects zero/skipped/cancelled/todo tests.
Baseline timing is **attested**, not cryptographically proved.
There is no import of unverified foreign baseline formats.

Diagnostic matching is a multiset: path, rule, severity/message and position must
match, and the diagnostic's source file must be byte-identical for a historical
exemption. Matching diagnostics in modified files are unclassified. Position shifts
can conservatively appear newly observed. These labels describe observed tool
output and do not prove cause, identical semantics, or agent authorship. Unchanged
diagnostic text can hide changed semantics even in unchanged files if dependencies
change; historical means the same observable diagnostic, not proof of identical cause.

Snapshots cover Git tracked files plus nonignored untracked files, including staged,
unstaged and untracked starting work. Renames are delete/add. Git index identity is
recorded and freshness checked. HEAD changes invalidate the baseline. Files are hashed
with SHA-256 and size; POSIX executable mode is recorded. No source contents are saved.
Git-ignored untracked content and `.agent-quality/` are excluded and listed. Tracked
ignored files still count. Avoid ignoring source/config used by the checks.

Budgets: 20,000 source files, 8 MiB/file, 256 MiB aggregate, 15 seconds of per-file
scan work, and 15 seconds for each Git call. Git inventories are buffered in memory;
the CLI is intended for bounded trusted repositories, not adversarially huge trees.
Symlinks, junctions, special files, submodules and budget exhaustion invalidate
coverage. No atomic snapshot or live watcher exists; edits restored between scans,
remote mount stalls, external data/services and escaped child processes may evade
observation. Use one writer and deterministic offline tools during the interval.

Tool identity covers the resolved executable and configured file arguments. Lockfiles
and tracked tool/config files are included in content snapshots; installed transitive
dependencies, system libraries, interpreter imports and external configs are **not
recursively hashed**. Keep those unchanged. Environment values are represented only
by one aggregate SHA-256 fingerprint; variable names and individual hashes are not
written to receipts. Volatile shell PWD/OLDPWD/SHLVL/_ are excluded. The fingerprint
still lets the CLI detect whether the environment changed, without listing secret
variable names or per-value hashes. Capture and verification must use the same
permission and environment context; changing a host's sandbox/elevation context can
invalidate an otherwise unchanged task baseline.
The CLI implementation is also fingerprinted. The CLI records observed checking
results under these trust assumptions, not a reproducible hermetic build.

`check-receipt` validates artifact hash, current content/index/HEAD/exclusions,
configuration, environment and tool entry identities. It cannot authenticate a
receipt against a malicious author who can recompute its hash. Raw command output
may contain private data; inspect it before sharing. CLI code has no telemetry,
network calls or external service dependency. Repository tools may have their own
network behavior and side effects; `--execute` is an explicit opt-in, not a sandbox.

For a claim beyond executed scope, omitted checks, zero/skipped tests, untracked
ignored inputs, nondeterminism or unclear diagnostic attribution: say **incomplete**
in the Agent's summary, even if the CLI observed `no_new_observed` for its commands.
