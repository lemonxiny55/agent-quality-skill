# DeltaReceipt

[English](README.md) | 简体中文

**Fix what the agent broke. Ignore what was already broken. Prove the change is clean.**

DeltaReceipt 是 Agent Quality Skill v0.1.0 的后继版本：免费、MIT 开源的独立 Agent Skill，附带本地证据 CLI。更名保留既有收据数据，详见[迁移说明](references/migration.md)。编辑前记录真实工作区，
编辑后运行仓库已有 lint、类型检查和测试；只有证据允许时，才区分历史问题与新增结果。
CLI 不依赖 DSH，不包含遥测、账号系统或网络服务。

设计理念来自 [dsh-lint-loop](https://github.com/lemonxiny55/dsh-lint-loop)。
如果使用 DeepSeek Harness，可前往原插件了解集成式编辑反馈、生命周期引导和安全修复。

## 安装和使用

需要 Python 3.10+、Git、有至少一次提交的仓库，以及仓库已安装的检查工具。从 [lemonxiny55/delta-receipt](https://github.com/lemonxiny55/delta-receipt) 克隆源码，运行 `python scripts/package_skill.py` 后再安装。
先检查 ZIP 内容，再把**压缩包内的文件**解压至以下目录之一：

| Agent | 项目内安装位置 |
| --- | --- |
| Codex CLI | `.agents/skills/delta-receipt/` |
| Claude Code | `.claude/skills/delta-receipt/` |
| Cursor Agent | `.cursor/skills/delta-receipt/` |
| GitHub Copilot | `.github/skills/delta-receipt/` |

确保目录内直接包含 `SKILL.md`、`scripts` 和 `references`。
历史 v0.1.0 证据记录了 Windows 上 Codex CLI 0.163.0-alpha.10.2 与 Claude Code CLI 2.1.226 使用旧名称执行的隔离任务。DeltaReceipt v0.2.0 的新名称检查及原生宿主结果见[兼容矩阵](references/compatibility.md)。Claude 任务中的 lint、类型检查和 4/4 TAP 测试分别通过，但总收据为 `incomplete`：配置中的测试入口文件在 baseline 后发生变化，因此本次不声称 `no_new_observed`。此前 Claude 手动读取 SKILL.md 的工作流及收据仍是独立有效证据。原始事件记录中的模型字段为 `glm-5.2`，用户界面报告为“Fable 5”；用户说明实际使用的是中国模型／提供方，不是 Anthropic Claude。Cursor／Copilot 尚未运行。详情见[验证记录](references/validation.md)和[兼容矩阵](references/compatibility.md)。

在开始编辑前于 Codex 调用 `$delta-receipt`、于 Claude Code 调用 `/delta-receipt`，
或让 Agent 阅读安装目录里的 SKILL.md。
让它先检查仓库已有命令，并在目标仓库根目录配置 `.agent-quality.json`，
参照[配置说明](references/configuration.md)或[完整示例](examples/node/.agent-quality.json)。

以下路径须替换成实际绝对路径；Windows 可使用 `python` 或 `py -3`，含空格路径需要引号。

```sh
python /skill/scripts/delta_receipt.py plan --repo /repo
python /skill/scripts/delta_receipt.py baseline --repo /repo --before-edit --execute --out /repo/.agent-quality/task-001.before.json
# 采集完成后，再进行本轮代码编辑。
python /skill/scripts/delta_receipt.py verify --repo /repo --baseline /repo/.agent-quality/task-001.before.json --execute --out /repo/.agent-quality/task-001.receipt.json
python /skill/scripts/delta_receipt.py check-receipt --repo /repo --receipt /repo/.agent-quality/task-001.receipt.json
```

执行前审阅 plan。`--execute` 表示明确选择执行，不会绕过宿主授权，也不是安全沙箱。
仓库命令会以当前用户权限运行。CLI 不自动修复、安装依赖、stash、reset 或修改 Git 暂存区。
已有暂存、未暂存和未跟踪修改可保留；每轮任务使用新的基线文件名，不允许覆盖原基线。

如果已经编辑但没采集基线，执行不带 `--baseline` 的 `verify`，结果为 `incomplete`。
不得补采“编辑前”基线，也不得用 HEAD 冒充实际任务开始状态。

## 结果如何解释

| 结果 | 含义 |
| --- | --- |
| `no_new_observed` | 在配置命令、记录范围及信任前提内，没有观察到新增结果 |
| `regression` | 新出现的诊断，或原通过命令变为失败；不能据此证明作者身份或因果关系 |
| `incomplete` | 缺少／无效基线、历史归因不明、检查未执行、工具缺失、超时、取消或证据不完整 |

Quality Receipt 记录实际 argv、工作目录、工具入口指纹、原始 stdout/stderr、退出码、
时间、内容指纹、排除范围、历史／新增／无法分类结果和原因。
历史诊断只在诊断所在文件字节未变时获得豁免；修改过的旧文件保留相同诊断时，保守标记无法分类。
Node TAP 适配器记录测试数量，零测试、跳过、取消或 todo 会标记不完整。
前后测试都失败时无法按用例隔离，必须标记不完整。通用 `exit` 测试适配器始终保留不完整状态。
Agent 还须检查实际发现范围；退出 0 本身不证明测试真的执行。

退出码 0 表示基线可用或没有观察到新增，1 表示新增结果，2 表示证据不完整或调用错误。
`check-receipt` 的 0 仅代表凭证未过期，仍应读取 `effectiveVerdict`。

## 真实 Demo 与开发验证

[验证记录](references/validation.md)链接 Windows/Linux 原始测试日志、真实工具凭证和经过审计的 Codex E2E 摘要；原始 Agent 转录及本机调用细节不公开。
归档凭证只属于当时记录的工作区，不能证明当前克隆状态。

```sh
python scripts/demo.py --install --evidence evidence/my-demo
python scripts/validate_skill.py .
python scripts/record_tests.py --out evidence/my-tests.json
python scripts/package_skill.py
```

兼容入口 `scripts/quality.py` 会转发至新 CLI，旧脚本仍可继续使用。已有 `.agent-quality.json`、`.agent-quality/` 文件和 `agent-quality/v1` 收据继续保留；不要重命名或重写。

`--install` 明确允许在新建的隔离 Demo 仓库执行 `npm ci --ignore-scripts`。
示例用固定版本的 ESLint、TypeScript 和 Node 测试运行器，保留两个历史问题，
真实引入 lint／类型／测试回归，再只修复新增修改，并验证缺失基线和凭证失效。
单元测试使用的协议 fixture 与真实工具 Demo 分开标记。

ZIP 根目录必须包含 SKILL.md，并小于 50 MB；仅打包运行 CLI、说明、许可证和 Node 示例。
测试及机器相关验证记录保留在 GitHub 源码仓库，不进入安装包。打包元数据附 SHA-256，并校验解压结果；尚未实测 Agensi 服务端验收。

## 与原插件的区别

| | 本 Skill | dsh-lint-loop |
| --- | --- | --- |
| 运行方式 | Python 标准库 CLI + Agent 终端 | DSH 插件 |
| 触发 | 显式流程；自动发现由宿主决定 | DSH 编辑和生命周期集成 |
| 基线 | 调用者保证编辑前采集，时间顺序是声明 | 宿主集成采集 |
| 修复 | 不提供自动修复 | DSH 专用安全修复能力 |
| 证据 | 本地 JSON | DSH 集成 Quality Receipt 工具 |

这是独立实现，不依赖未发布 v0.7 候选包，不修改原项目或 PR #8。

## 技术限制与候选状态

Skill 不自带跨 Agent 自动拦截，未提供宿主钩子适配、语义级作者证明、完整测试发现、
自动影响范围推断或“支持所有 Agent”的承诺。哈希未签名，不能防止恶意重写。
Git 忽略的未跟踪输入、已安装依赖的传递文件及外部服务无法完整记录。
请保持工具／依赖不变、使用单写入者，并阅读[证据边界](references/evidence-contract.md)。

[技术调研与来源](references/feasibility.md) · [兼容矩阵](references/compatibility.md) ·
[验证记录](references/validation.md) · [Agensi 文案与引流计划](references/agensi-listing.md) · [迁移说明](references/migration.md) · [迁移说明](references/migration.md)

当前为 **v0.2.0 更名草案**。v0.1.0 验证记录对应前身版本；v0.2.0 Codex 原生测试因环境变化得到 `incomplete`，Claude Code 则因 API `ConnectionRefused` 未能启动；两者都不能据此声称 `no_new_observed`。Cursor／Copilot 及 Agensi 服务端验收仍未验证。
没有正式上架、设置付费价格或对外发布推广。

MIT © 2026 lemonxiny55。[许可](LICENSE) · [来源归属](NOTICE)。
