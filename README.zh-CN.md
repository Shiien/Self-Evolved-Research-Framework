# SER — 自进化科研框架 (Self-Evolved Research)

> 面向 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 与 Codex
> 的行为驱动科研协作框架。
> 技能自动触发，框架会在使用过程中持续改进自身技能。
>
> **[English README](README.md)**

<p align="center">
  <img src="ser_architecture_overview.svg" alt="SER 架构总览" width="700"/>
</p>

## 功能简介

你只需用自然语言描述需求，SER 会自动识别意图并路由到对应的微技能：

| 你说 | SER 触发 |
|------|---------|
| "我在读这篇论文……" | `paper-read` — 生成结构化笔记 |
| "帮我 arxiv 搜一下 X" | `paper-lit-search` — arXiv + Semantic Scholar 检索 |
| "这个证明对不对？" | `proof`（CRITIQUE 模式）— 逐步核查 |
| "证明一下……" | `proof`（WRITE 模式）— 从零起草证明 |
| "接下来该做什么？" | `plan-suggest` — 排序任务建议 |
| "设计一下实验" | `experiment-plan` — 主张 / 变量 / 基线 |
| "扫一下这几个超参" | `experiment-dse` — 搜索策略 + 配置 |
| "跑实验" | `experiment-run` — 通过 `harness ext-launch` 做契约门控启动 |
| "有没有 X 的新 idea？" | `idea`（DISCOVER）→ `idea-verify` → `idea`（REFINE） |
| "写一下 introduction" | `writing`（DRAFT 模式）— 章节初稿 |
| "把结果画成柱状图" | `paper-assets`（FIGURE 模式）— PGFPlots / matplotlib |
| "编译论文" | `paper-assets`（COMPILE 模式）— `scripts/compile_paper.sh` |
| "实现一下这个功能" | `code`（ROADMAP）→ `code-implement` → `code-review` → `code`（COMMIT） |
| （结束对话） | `session-close` — 证据优先的收尾与持久化 |

当技能执行产生真实 reward signal 时，SER 才记录反馈。跨多轮会话后，
SER 可基于自然语言 TD 学习对自身技能说明书提出改进建议——**今天你用的
技能，明天会更好用**。

## 快速开始

### 1. 克隆仓库

```bash
git clone --recurse-submodules https://github.com/Shiien/Self-Evolved-Research-Framework.git
cd Self-Evolved-Research-Framework
```

> **已经 clone 过但没有带 `--recurse-submodules`？** 执行：
> ```bash
> git submodule update --init --recursive
> ```

### 2. 运行 Setup

```bash
bash scripts/setup.sh
```

该脚本生成 `config.yaml`、初始化记忆系统并建好所有目录结构。可重复执行，幂等。

### 3. 配置项目

编辑 `config.yaml`：

```yaml
project:
  name: "你的研究项目"
  status: "phase-0-exploration"
  created_at: "2026-03-19"

research:
  domain: "你的领域"
  sub_domain: "你的子方向"
  keywords: [...]
```

### 4. 选择运行时并开始工作

Claude Code 与 Codex 是两套独立的单模型运行时。当前运行时直接完成
实现、评审、写作、判断与验证，不会调用另一套运行时。

使用 Claude Code：

```bash
claude
```

SER 会自动：
1. 由 `scripts/session_context.sh` 注入确定性的会话上下文
2. 由 `session-open` 输出研究问题、实验 ledger 与最近运行状态
3. 直接等待你的科研请求——无需任何命令

使用 Codex 时，先按下一节安装 Codex manifest，再运行 `codex`。

### 5. 安装技能

安装器默认选择 Claude 运行时：优先使用 `SKILL.claude.md`，否则使用
通用 `SKILL.md`，目标目录为 `.claude/skills/`。

```bash
bash scripts/install-skills.sh            # 复制到 ./.claude/skills
bash scripts/install-skills.sh --link     # 通用 manifest 链接；原生 manifest 实体化复制
bash scripts/install-skills.sh --user     # 安装到 ~/.claude/skills
bash scripts/install-skills.sh --list     # 列出已识别的技能
bash scripts/install-skills.sh --dry-run  # 预演，不写入
bash scripts/install-skills.sh --force    # 覆盖已存在的技能
```

**按族选装** —— 用通配符挑选或排除：

```bash
bash scripts/install-skills.sh --only 'paper-*'
bash scripts/install-skills.sh --only 'code*,paper-assets'
bash scripts/install-skills.sh --exclude 'theory,proof'
```

Codex 运行时需显式指定：优先使用 `SKILL.openai.md`，否则使用通用
`SKILL.md`，并将实体化副本写入 `.agents/skills/`。

```bash
bash scripts/install-skills.sh --runtime codex
codex
```

四项判断密集、职责独立的能力会在两端都作为单独技能安装：
`code-implement`、`code-review`、`idea-verify`、`writing-review`。
它们由当前运行时直接执行。

Claude 的 `--link` 只有在来源是通用 `SKILL.md` 时才创建软链接；若技能
使用运行时原生 manifest，安装器会把所选 manifest 实体化为安装目录中的
`SKILL.md`。Codex 始终使用项目内实体化副本，因此 `--runtime codex`
不支持 `--link` 与 `--user`。

## 技能总览（27 个核心 SER + 11 个随附辅助/专家 + 1 个外部）

每个技能位于 `skills/{skill-name}/`，并带标准 YAML frontmatter。大多数
技能使用通用 `SKILL.md`；运行时特定技能提供 `SKILL.claude.md` 与
`SKILL.openai.md`，安装时统一实体化为 `SKILL.md`。

不加筛选条件的全新安装会创建 **39 个技能目录**。下表只列出由原始 57 个
技能整合而来的 **27 个核心 SER 技能**（见 `REFACTOR_PLAN.md §7`）。
不计入核心数量的 11 个随附目录是：

- `peer-review` 协调技能；
- 9 个同行评审专家技能：`peer-review-correctness`、
  `peer-review-critique`、`peer-review-evaluations`、`peer-review-for-ddl`、
  `peer-review-presentation`、`peer-review-qa`、`peer-review-sac`、
  `peer-review-significance`、`peer-review-story`；
- 特殊用途技能 `play-tic-tac-toe`。

第 39 个目录是下一节介绍的外部技能 `fey-r`。

| 分类 | 技能 | 用途 |
|------|------|------|
| **会话生命周期** | `session-open`, `session-close` | 状态横幅 / 证据优先收尾 |
| **读论文** | `paper-read`（STANDARD / DEEP / COMPARE / INDEX 模式）, `paper-lit-search` | 阅读、对比、索引、arXiv + Semantic Scholar 检索 |
| **写论文** | `writing`（OUTLINE / DRAFT / POLISH 模式）, `writing-review` | 提纲 → 初稿 → 同行评审 → 润色 |
| **论文构建** | `paper-assets`（ILLUSTRATE / FIGURE / ART / COMPILE 模式） | 架构图、数据图、装饰图、LaTeX 构建 |
| **理论** | `theory`（FORMALIZE / DECOMPOSE / SEARCH / COUNTEREXAMPLE / GENERALIZE 模式） | 形式化与证明策略 |
| **证明** | `proof`（WRITE / CRITIQUE / FIX / FORMALIZE / VERIFY 模式） | 起草 → 评审 → 修补 → 发表级 LaTeX → 局部验算 |
| **Idea** | `idea`（EXPLORE / DISCOVER / REFINE 模式）, `idea-verify` | 方向探索 → 缺口分析 → 新颖性核查 → 精炼提案 |
| **实验** | `experiment-plan`, `experiment-dse`, `experiment-run`, `experiment-monitor`, `experiment-analyze` | 设计 → 超参扫描 → 派发 → 监控 → 分析 |
| **编码** | `code`（BRANCH / ROADMAP / DEBUG / COMMIT 模式）, `code-implement`, `code-review` | 分支 → 计划 → 实现 → 调试 → 评审 → 提交 |
| **规划** | `plan-suggest`（含 MILESTONE 模式）, `decision-analyze`（含 CONVERGE 模式） | 项目管理；只读状态由 `python -m harness status` 提供 |
| **Checklist** | `checklist`（CREATE / UPDATE / VERIFY / RECOUNT 模式） | 交付物审计与主张追踪 |
| **记忆** | `memory`（WRITE / RETRIEVE / CONSOLIDATE / FORGET 模式） | 持久化非科学上下文 |
| **元技能** | `skill-feedback`, `evolve-suggest`, `evolve-apply` | TD-NL 技能自进化 |
| **集成** | `project-integrate` | 将 SER 并入已有项目 |

## 外部技能

| 技能 | 来源 | 用途 |
|------|------|------|
| [Fey-R](https://github.com/xvirobotics/fey-r) | `skills/external/fey-r/` | 交互式费曼法读论文——通过重现作者推导来深度理解论文 |

外部技能以 git submodule 形式接入，`scripts/setup.sh` 会自动初始化。
添加自定义外部技能：`git submodule add <url> skills/external/<name>/`。

## 技能自进化（TD-NL）

只有技能使用产生真实 reward signal 时，SER 才更新技能价值。审计与说明书
修改始终需要显式触发和用户批准：

```
真实 reward signal → signal-gated skill-feedback
                   → 在线 EWMA Q 更新 + 可选 pending flag

用户显式 audit 或 session-close 时主动选择审计 → evolve-suggest
                                                → 检查 pending flags、派生 V^L、
                                                  可选起草一项 proposal

用户批准 proposal → evolve-apply → 归档 + 修改（或经批准回滚）
```

优化目标是 `skills/{skill-name}/SKILL.md` 本身。
`skills/td-nl/history/` 下保留版本归档以支持安全回滚。

## 研究 Harness

仓库内实验统一走带预注册契约的确定性路径。每个 `runs/<id>/` 都保存
解析后的配置、契约及其 hash、元数据、指标、checkpoint、evaluation、
failure 与 summary。进程结束不等于实验完成；只有 evaluation 对照契约
给出 verdict 后，结果才能成为科学证据。

```bash
python -m harness setup                          # 环境检查
python -m harness smoke-test                     # 确定性基线检查
python -m harness run configs/<experiment>.yaml # 运行一个仓库内实验
python -m harness evaluate <run>                 # 按已存契约评估
python -m harness resume <run>                   # 续跑失败或不完整运行
python -m harness compare <run> <run> ...        # 指标与 verdict 对比
python -m harness status                         # ledger、run 与外部状态
python -m harness loop step                      # 执行下一个合法 planned 实验
```

## 目录结构

```
├── CLAUDE.md              # Claude 运行时的 v6 研究协议
├── AGENTS.md              # Codex 运行时的 v6 研究协议
├── .agents/skills/        # Codex 技能实体化安装目标
├── RESEARCH_STATE.md      # 科学状态：问题、假设、证据、不确定性
├── EXPERIMENTS.json       # 实验 ledger：状态、运行引用与 verdict
├── IDEA_BACKLOG.md        # 暂不进入当前问题的想法
├── harness/               # 契约、运行目录、CLI 与研究循环
├── configs/               # 带预注册契约的实验配置
├── runs/                  # 自包含实验运行记录
├── config.template.yaml   # 拷贝为 config.yaml 后自定义
├── README.md / README.zh-CN.md / LICENSE
├── skills/
│   ├── {skill-name}/      # 27 个核心 + 11 个随附辅助/专家技能
│   ├── _shared/           # 四份共享协议，不是可安装技能
│   │   ├── checklist-engine.md
│   │   ├── memory-tiers.md
│   │   ├── evolve-cycle.md
│   │   └── git-conventions.md      # 共享 git 工作流
│   ├── external/          # 外部技能（git submodule）
│   │   └── fey-r/         # 费曼法读论文
│   └── td-nl/             # 技能自进化基础设施
│       ├── feedback-log.md
│       ├── value-function.md
│       ├── skill-values/   # 单技能 Q^L 估计
│       └── history/        # SKILL.md 版本归档，支持回滚
├── scripts/               # 会话上下文、引用、通知与技能安装工具
├── memory/                # 三层持久化的非科学上下文
│   ├── episodes/          # 近期观察（7 天保留）
│   ├── topics/            # 汇总知识（90 天）
│   └── procedures/        # 永久流程
├── background/            # 背景资料
├── methodology/           # 研究方法 + ideas
├── experiments/           # 实验代码 + 结果
├── outputs/               # 交付物（短 / 中 / 长期 + paper/）
├── resources/             # 参考资料（papers/ + repos/）
├── logs/                  # 外部实验记录 + 可选 digest
└── docs/                  # 计划与报告
```

## CLAUDE.md 是怎么工作的

Claude Code 由 `CLAUDE.md` 驱动，Codex 由 `AGENTS.md` 驱动。两份根协议
采用相同的证据优先状态模型，并为各自运行时定义：

- **意图路由**：把自然语言需求映射到最具体的 SER 技能
- **会话生命周期**：打开时读取状态，结束时把证据写回 canonical owner
- **实验协议**：执行前预注册契约，评估后才形成科学证据
- **状态所有权**：科学事实写入 `RESEARCH_STATE.md` 与 `EXPERIMENTS.json`
- **进化回路**：真实 reward signal 驱动 `skill-feedback` 与后续审计

每个子目录都有自己的 `CLAUDE.md`，为该区域提供局部上下文。
在 Codex 安装面，`AGENTS.md` 是根行为协议，安装后的 `SKILL.md` 是
针对 Codex 选择并实体化的单模型 manifest。

## 典型工作流

### 日常科研

```
（打开 claude）
→ session-open 输出状态横幅

"我想继续读 LAPA 这篇论文"
→ paper-read 生成结构化笔记

"这个推导步骤对吗？[粘贴]"
→ proof（CRITIQUE 模式）核查

"今天就到这里"
→ session-close 将证据、ledger 变化与未解决事项持久化到 canonical state
→ 只有用户显式要求或主动选择审计时才运行 evolve-suggest
```

### Idea 探索

```
"agent memory 方向有哪些 open problem？"
→ idea（DISCOVER 模式）生成候选

"第二个 idea 有新颖性吗？"
→ idea-verify 比对现有文献

"把这个想法变成可验证的提案"
→ idea（REFINE 模式）写出差异点、falsifier 与最小验证实验

"就走这个方向"
→ decision-analyze 记录决策
```

### 写论文

```
"开始写"
→ writing（OUTLINE 模式）生成结构与 Claims-Evidence Matrix

"写 introduction"
→ writing（DRAFT 模式）只写已有证据支持的主张

"评审一下这个版本"
→ writing-review 由当前运行时直接做同行评审

"润色这一段"
→ writing（POLISH 模式）收紧表达并解释关键修改

"编译论文"
→ paper-assets（COMPILE 模式）运行 scripts/compile_paper.sh 并报告错误

"画论文架构图"
→ paper-assets（ILLUSTRATE 模式）生成可编辑的架构图

"把结果画成图"
→ paper-assets（FIGURE 模式）生成出版级数据图
```

### 实验全流程

```
"设计一个实验验证主张 C"
→ experiment-plan 写出 主张 / 变量 / 基线

"扫一下学习率和 batch size"
→ experiment-dse 生成配置并配合早停运行

"开跑"
→ experiment-run 派发（带 GPU 预检与 SSH 感知）

"分析结果"
→ experiment-analyze 对照预注册契约给出 verdict
→ paper-assets（FIGURE 模式）渲染出版级图表
```

### 编码工作流

```
"为 ingest 重构开个分支"
→ code（BRANCH 模式）创建 feat/... 分支（可选创建 worktree）

"先写个实现计划"
→ code（ROADMAP 模式）拆成带验收条件的步骤

"实现第 2 步"
→ code-implement 由当前运行时按 TDD 执行

"review 一下 diff"
→ code-review 由当前运行时审查完成的 diff

"commit"
→ code（COMMIT 模式）按共享 git 规范提交
```

## License

MIT — 见 [LICENSE](LICENSE)
