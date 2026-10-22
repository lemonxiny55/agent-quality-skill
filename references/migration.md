# DeltaReceipt v0.2.0 migration

DeltaReceipt is the rebranded successor to Agent Quality Skill v0.1.0. The Git
repository and Skill names change; the runtime receipt interface stays stable.

## Stable runtime data

- Keep `.agent-quality.json` at the target repository root. Its `version: 1`
  format is unchanged.
- Keep existing baselines and receipts under `.agent-quality/`. Do not rename,
  regenerate, edit, or reseal archived files. Their timestamps, hashes, schema
  (`agent-quality/v1`) and provenance remain historical facts.
- The v0.2.0 CLI recognizes the exact v0.1.0 implementation fingerprint so an
  in-flight v0.1.0 baseline and receipt can still be checked. Other implementation
  fingerprints remain incompatible. New artifacts record v0.2.0.
- `scripts/quality.py` remains as a deprecated forwarding entry point. New examples
  use `scripts/delta_receipt.py`.

## Install the renamed Skill

Install the ZIP contents into `delta-receipt/` so its entrypoint is
`delta-receipt/SKILL.md`. Use `.agents/skills/delta-receipt/` for Codex and
`.claude/skills/delta-receipt/` for Claude Code. Invoke `$delta-receipt` in Codex
or `/delta-receipt` in Claude Code. Remove an old Skill folder only after the new
folder is installed and validated; keep one active copy per host to avoid duplicate
discovery. Project receipts are separate from the Skill install folder.

## Git and releases

The rebrand branch targets `lemonxiny55/agent-quality-skill` until a maintainer
renames it. After the Draft PR is reviewed and merged, rename the GitHub repository
to `lemonxiny55/delta-receipt`, then update local remotes:

```sh
git remote set-url origin https://github.com/lemonxiny55/delta-receipt.git
# or: git remote set-url origin git@github.com:lemonxiny55/delta-receipt.git
# Confirm: git remote -v
```

GitHub documents redirects for repository web and Git URLs after a rename, and
recommends updating local remotes. See [Renaming a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository).
After the rename, verify the old v0.1.0 release page and its direct asset download
URL still resolve before announcing the change; release download links are tied to
the repository URL. Do not create a replacement repository at the old slug, because
that can break GitHub's redirects. Keep the published v0.1.0 Release and attached
ZIP untouched; v0.2.0 uses its own versioned tag and asset name
(`delta-receipt-0.2.0.zip`). Users should install
the new Skill side-by-side, verify `SKILL.md` and CLI `--help`, then retire the old
Skill folder. Existing `.agent-quality/` data is not migrated.

The Draft PR does not perform the remote rename or publish v0.2.0.
