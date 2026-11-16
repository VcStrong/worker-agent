# worker-agent：互联网研发角色 agent 套件

让 AI 像一个互联网产品研发团队那样，以不同的职业身份协作完成需求。宿主是 **Claude Code subagent**：装上就能用，没有服务端。

- **14 个专家**（由图谱里的 48 个原始岗位合并而成）：9 个传统专家 + 5 个 AI 专家
- **总控**（orchestrator，兼项目经理 / Scrum Master）：选角、调度、拍板、日志、仲裁
- **技术情报员**（tech-scout）：只管技能维护，用户批准后才侦察
- **技能层**：98 个可更新的技能包，带成熟度（采用 / 试用 / 评估 / 暂缓）、as_of 和官方来源
- 只依赖 `python3`（3.8+），不需要 pip 包

| 专家 | slug | 合并的原始岗位 | 模型 |
|---|---|---|---|
| 产品经理 | product-manager | 产品经理、产品负责人、用户研究员 | opus |
| 体验设计师 | ux-designer | 交互、UI / 视觉、设计系统 | sonnet |
| 架构师 / 技术负责人 | architect | 架构师、基础架构 / 中间件、研发经理、技术总监 | opus |
| 前端工程师 | frontend-engineer | 前端、全栈（Web 部分） | sonnet |
| 客户端工程师 | client-engineer | 客户端（Android / iOS / 鸿蒙 / 小程序 / 跨端） | sonnet |
| 后端工程师 | backend-engineer | 后端、全栈（服务端部分）、DBA、数据开发 | sonnet |
| 测试专家 | qa-expert | 测试、测试开发 | sonnet |
| SRE 与安全工程师 | sre-security | SRE / 运维、安全 | sonnet |
| 数据与增长运营 | data-growth | 数据分析、产品运营、用户 / 内容 / 活动运营、增长投放、AIGC 运营、客服 | sonnet |
| AI 产品经理 | ai-product-manager | AI 产品经理、AI 体验设计、AI 解决方案架构 | opus |
| AI 应用 / Agent 工程师 | ai-app-engineer | 大模型应用、RAG、Agent、AI 研发效能 | sonnet |
| 模型与算法工程师 | model-algorithm-engineer | 算法、搜索推荐、训练微调、语音多模态、数据训练师 | sonnet |
| AI Infra / MLOps 工程师 | ai-infra-mlops | 推理优化、MLOps | sonnet |
| AI 评测与安全合规专家 | ai-eval-compliance | AI 评测、AI 安全合规、法务合规 | sonnet |

项目经理、Scrum Master 由总控兼；HRBP 和研发流程无关，不做 agent（`who.py HRBP` 可查）。完整映射见 `data/merge_map.json`。

## 安装

```bash
./install.sh --project /path/to/your-app     # 项目级：装到 <项目>/.claude/
./install.sh --user                          # 用户级：装到 ~/.claude/
```

安装会：

1. 按本机检测结果渲染 16 个 agent 到 `.claude/agents/`，101 个 skill 到 `.claude/skills/`：98 个技能包，加上 /who、/skills-refresh、/orchestrate；流程、规则、模板、配置复制到 `.claude/role-agents/`。
   - 检测到 **kb MCP**（知识库）：所有专家加只读 kb 工具，总控加 kb_log / kb_ask / kb_wait_answer / kb_write_doc。没检测到就打印「未检测到 kb MCP，已退回只靠 workspace 文件交接」。
   - 检测到 **Context7** 等文档类 MCP：工程角色查官方文档时优先用它。没有就退回 WebFetch 官方站点。
2. 同名文件先备份成 `*.bak-<时间>`。
3. 把 hooks 合并进 `.claude/settings.json`：原文件先备份为 `settings.json.bak`，只追加本套件的 hooks。这些 hook 都是纯本地 Python，不调用模型：
   - `usage_hook.py`：使用度统计（PreToolUse: Task|Agent|Skill|Read，SubagentStop）
   - `guard_hook.py`：安全边界（PreToolUse: Bash|Write|Edit…）
   - `refresh_check.py`：技能更新提醒（SessionStart）
   - 不想改 settings.json 就加 `--no-hooks`。

其他选项：`--mcp none|kb,context7` 强制指定，`--dry-run` 只看不写，`--uninstall` 只删本套件装进去的文件和 hooks。

## 怎么用

在装好的项目里打开 Claude Code，直接提需求：

- **完整需求**：`/orchestrate 做一个带积分的每日签到功能`，或者 `claude --agent orchestrator`。总控会先给出执行计划，再按 9 个阶段调度专家。（子 agent 不能再调子 agent，所以完整调度要在主会话里做。）
- **单个专家**：直接说活儿，宿主 AI 会按 description 自动选角。用旧岗位名也能路由到合并后的专家，比如「请 DBA 看下这条慢 SQL」会交给后端工程师，「让用户运营设计召回活动」会交给数据与增长运营。
- **查角色**：`/who 灰度`、`/who DBA`、`/who ArkTS`、`/who --usage`，或者 `python3 scripts/who.py <词>`。

交付物写到 `workspace/<需求名>/<阶段序号>-<产物名>.md`，流转日志在 `workspace/<需求名>/log.md`。中断后重新运行会从日志里的断点继续。

### 接入知识库（角色团）

本地知识库（kb）的后台会话可以把 14 个专家当子 agent 派：知识库管流程和拍板，专家只出意见。套件这边提供：

- `config/kb_scenes.json`：场景表契约。场景（管家 / 流程设计 / 需求 / 需求体检 / 方案 / 开发 / 开发·端 / 审查·端 / Bug分析 / Bug修复 / 跟进 / 发布）→ 主导角色、参与角色、触发条件、每会话调用上限、是否只读、产物名；「标准」「精简」两档各给一份显式名单（知识库只用标准库，不解析 YAML），`@端` 按「端角色」换成对应端的工程师。安装时拷到 `~/.claude/role-agents/config/kb_scenes.json`，知识库读不到时用它自己的内置兜底表。`validate.py` 检查角色名都存在、精简名单只用 `team.yaml` tiers.lite 的角色。
- **知识库宿主模式**：每个专家的「工作方式」末尾都有这一段（不论安装时是否检测到 kb MCP）。任务说明里写了「知识库会话」时，不写 `workspace/`、不用 Write 建文件，产物正文作为最终回复交回主会话，由主会话用 kb 工具落库（其他产物写到 `其他资料/角色产物/`）；建议注明「建议来自：<角色>」，拍板由主会话发 kb_ask。
- **guard hook 无人值守**：环境变量 `KB_SESSION` 非空（知识库后台会话）时，原来要弹确认（ask）的危险操作直接拒绝（deny），提示「无人值守：用 kb_ask 请用户确认，由用户执行」，会话不会挂住。知识库自己用 Python 调 git 推送不经过 hook，不受影响。
- 安装结束打印「知识库角色团：可用（kb MCP ✅，agent 16/16，场景表 12 个场景）」；不可用时写明缺什么。
- 注意：用户级安装的 hooks 也作用于你自己的交互式 Claude Code 会话（那里没有 `KB_SESSION`，危险操作照旧弹确认）。

### 档位怎么选（config/team.yaml）

| 档位 | 适合 | 角色 |
|---|---|---|
| `lite` 精简 | 一个人的小项目、只做一两个端 | 总控 + 产品经理 + 架构师 + 对应端工程师 + 测试专家，一次流程最多 6 个角色；设计由产品经理兼，发布由架构师出方案 |
| `standard` 标准（默认） | 正式功能 | 14 个专家按需选；签到积分这类需求最多 10 个角色 |

AI 专家参与规则：

- AI 产品经理在每个需求立项时都要填 PRD 的「AI 机会评估」。
- AI 应用 / Agent 工程师、AI 评测与安全合规专家只在涉及大模型、生成内容或个人信息时参与。
- 模型与算法、AI Infra / MLOps 只在自训练 / 自部署模型、做搜索推荐时参与。

一个人做 Web + 后端的话，可以在 `lite` 档里去掉 `client-engineer`。`role_cap: 15` 是编制上限（含总控）。

### 运行参数（config/run.yaml）

| 参数 | 默认 | 说明 |
|---|---|---|
| approval_mode | ask | 立项、技术方案、上线放量 3 个节点停下等你拍板。设为 auto 时按建议继续，并在日志里记理由。在知识库的期里运行时走 kb_ask / kb_wait_answer |
| max_parallel | 3 | 同时运行的子 agent 数，同一角色的多个实例也算在内 |
| max_calls | 30 | 单个需求最多调用多少次角色，到了就停下请你决定 |
| model_overrides | {} | 按档位覆盖模型，如 `lite: {data-growth: haiku}`，改完重新 build |
| refresh_remind_days / stale_days / stale_days_ai | 30 / 180 / 90 | 技能更新提醒和过期阈值 |
| auto_apply_trivial | false | 设为 true 时，只改 as_of、补来源、修错别字的提案条目自动应用 |

### 安全边界

- 产品、设计、数据与增长、AI 产品经理、AI 评测合规这几个角色只读代码、只写文档，没有 Edit / Bash 权限。工程类角色可以在你指定的仓库里真实改代码。
- 部署、发布、git push、发推送、删除文件或数据库，任何角色都只出方案。guard hook 会对这类命令弹确认（ask）。
- 目标仓库不是 git 时，开发前先 `git init` 并做一次本地初始提交，不加 remote、不 push。
- 任何角色在执行需求时都不能直接改 agent 或技能包，guard hook 会拒绝，只能提交更新提案。
- 只有技术情报员能用 WebSearch；工程角色只用 WebFetch 查官方文档。抓回的网页只当数据，不执行其中的指令。
- 知识库方面，没有任何角色拿到 kb_base_secret、kb_set_status 或批准开发相关的工具，`validate.py` 会检查。

## 怎么让角色保持最新

技能和角色是分开的：角色（是谁、管什么）来自图谱和合并映射，比较稳定；技能（用什么、怎么做）在 `data/skills/<领域>/<id>.md`，变化快。

1. **提醒**：会话开始时 `refresh_check.py` 检查两件事：距上次更新是否超过 30 天，有没有技能包过期。满足条件就提醒一次（同一天只提醒一次），按使用度倒序列出角色。你不回复，它就不会消耗 AI 用量。回复「暂缓 7 天」就 7 天内不再提醒。
2. **侦察**：你选好角色后执行 `/skills-refresh 前端工程师 客户端工程师`。技术情报员只侦察这些角色登记的一手信息源（`config/sources.yaml`），提案写到 `proposals/<日期>-<领域>.md`，每条附证据链接和发布日期；找不到一手来源的条目标「待核实」。
3. **拍板应用**：`python3 scripts/apply_proposal.py proposals/<提案>.md --approve 1,3 --reject 2`。它会依次 build、validate、跑选角评测和技能回归题；任何一项下降就整体还原并拒绝。通过后打快照：git 仓库做本地提交加标签 `skills-<日期>-<序号>`（不 push）；不是 git 就拷到 `snapshots/`。
4. **同步**：`./install.sh --update --project <目录>`。只替换有变化的文件，并打印「旧版本 → 新版本」；`local/` 下你自己的覆盖不会被动。
5. **回滚**：`python3 scripts/rollback.py` 回到上一个快照，`--list` 查看所有快照。
6. **经验回流**：每个需求结束时，总控把各角色踩到的坑整理成 `proposals/lessons-<需求名>.md`，同样要你拍板后才写入技能包。只适用于你自己项目的经验写进 `local/skills/` 覆盖层。

其他调整：

- 改成熟度：`config/radar.yaml` 的 `overrides`。`region: cn | global` 决定国内外两套方案（推送、统计、云、大模型、设计协作）里默认采用哪一套，改完重新 `python3 scripts/build.py`。
- 新角色：情报员发现新岗位时，默认提议并入现有专家；拍板后写进 `data/roles_overlay.json`，不改图谱原文。

## 目录

```
source/graph.html            图谱原文（数据源）
data/roles.json              48 个原始岗位（extract.py 生成，基线层）
data/stages.json chain.json  9 阶段、11 个交付物链路
data/merge_map.json          48 → 14 专家 / 总控 / 不做 agent
data/experts.json            14 个专家的专家级档案
data/roles_overlay.json      新增 / 并入 / 下线角色覆盖层
data/skills/<领域>/*.md       技能层（98 个技能包）
local/                       本地覆盖层（优先级最高）
agents/                      生成的 16 个 agent（build.py）
skills/                      生成的技能 SKILL.md + 手写的 who / skills-refresh / orchestrate
templates/agent.md.j2        专家 agent 模板；templates/core/ 总控、情报员模板
templates/deliverables/      11 个交付物模板
workflow/stages.md           9 阶段准入准出
rules/arbitration.md         6 条仲裁规则
config/                      team / run / radar / sources / kb_scenes.json（知识库场景表）
proposals/                   提案、经验、待核实、驳回记录
scripts/                     extract build validate who usage_report refresh_check apply_proposal rollback install_helper
scripts/hooks/               usage_hook guard_hook
scripts/eval_routing/        选角评测（54 条，含 12 条知识库场景题）；scripts/eval_skills/ 技能回归题（53 条）
examples/checkin-points/     端到端样例：App 每日签到 + 积分
tests/                       自测（python3 -m unittest discover -s tests）
```

## 开发者

```bash
python3 scripts/extract.py source/graph.html   # 图谱更新后重新抽取（不动技能层；未映射岗位会告警）
python3 scripts/build.py                       # 三层合并渲染 agents/ 与 skills/（可重复，删除过期文件）
python3 scripts/validate.py                    # 全量校验；有错误时退出码非 0
python3 scripts/validate.py --deliverable workspace/x/02-PRD.md
python3 scripts/eval_routing/run_eval.py       # 选角评测（--llm 用 claude -p 实测）
python3 scripts/eval_skills/run_skill_eval.py  # 技能回归题
python3 -m unittest discover -s tests          # 自测
```
