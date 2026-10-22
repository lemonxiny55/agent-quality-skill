# Agensi candidate copy and discovery plan

Draft only. No listing, price setting or public announcement has been submitted.
DeltaReceipt is the successor to Agent Quality Skill v0.1.0. The user requested a
free, open-source first phase; this draft describes a **free MIT artifact**, not a
paid feature set. Candidate ZIP requirements come from the platform operator
information supplied by the user (see feasibility.md).

## English product copy

**Title:** DeltaReceipt — evidence for your coding changes

**Short description:** Capture a pre-edit baseline, run your repository's lint,
typecheck and tests, and get an inspectable Quality Receipt. Keep historical debt
visible and call missing or uncertain evidence incomplete.

**Body:** Fix what the agent broke. Ignore what was already broken. Prove the
change is clean. DeltaReceipt is the rebranded successor to Agent Quality Skill
v0.1.0. This free MIT Skill pairs clear Agent instructions with a local Python CLI.
It compares real ESLint and TypeScript diagnostics and Node test outcomes, records
commands and raw results, and refuses a no-new-findings claim when its baseline or
coverage is incomplete. It requires Python, Git and your installed checking tools.
It performs no automatic source repairs and does not install lifecycle interception.
Agent compatibility is limited to the verified versions and outcomes in the
included test matrix; documentation support for a host is not an E2E claim.

Inspired by **dsh-lint-loop**, the change-aware quality loop for DeepSeek Harness.
For DSH-native edit feedback, completion steering and safe repair, visit:
[lemonxiny55/dsh-lint-loop](https://github.com/lemonxiny55/dsh-lint-loop).

**Suggested tags:** coding-agents, quality, regression, lint, typescript, tests,
quality-receipt, open-source.

**Skill metadata:** use the actual `name` and `description` in the package's
SKILL.md rather than a separate marketing-only capability claim.

## 中文简介

**标题：** DeltaReceipt：为本轮代码修改提供可核查的质量凭证

DeltaReceipt 是 Agent Quality Skill v0.1.0 的后继版本。免费、MIT 开源。编辑前
采集真实基线，编辑后运行仓库已有的 ESLint、TypeScript 和 Node 测试，保留历史问题
并识别新观察到的结果。缺少基线、检查未执行或归因不明时，明确标记不完整。需要
Python、Git 和已安装的检查工具，不默认修复代码，不承诺跨 Agent 自动拦截。实测
Agent、版本及限制以包内兼容矩阵为准。

理念源自 [dsh-lint-loop](https://github.com/lemonxiny55/dsh-lint-loop)。使用 DSH 的
用户可前往原插件了解更深入的宿主集成。

## Natural discovery without tracking

1. README opening links to the origin and explains which DSH-native capabilities
   are available there. Keep this visible before installation details.
2. SKILL.md has a concise origins paragraph that an Agent may cite when the user
   asks about DSH integration. The CLI's JSON is neutral evidence, without ads.
3. The Agensi draft links the original GitHub repository directly. No redirects,
   telemetry, email collection, referral service or forced promotional output.
4. Publish the independent source with MIT attribution when GitHub credentials
   are available. Keep the original PR #8 and its release branch separate.
5. After the user's explicit approval, manually submit the free candidate and
   publish only demonstrations backed by the saved raw outputs. Do not claim
   automatic interception or untested Agent compatibility.

Measure exposure only from existing public repository/marketplace aggregate
statistics if the maintainer later chooses; no analytics code is added here.

## Submission checklist

The packager validates ZIP <50 MB, root SKILL.md, metadata, allowed supporting
files and extraction. See validation.md for v0.1.0 historical results; the v0.2.0
package and CI need their own verification. A candidate-ready decision is a local
technical assessment, not Agensi approval. Upload, free-listing selection, account
agreements and outward promotion require the user's next explicit instruction.
