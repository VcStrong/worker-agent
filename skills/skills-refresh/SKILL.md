---
name: skills-refresh
description: 让技术情报员侦察选中角色或领域的技术变化并出技能更新提案（如 /skills-refresh 前端工程师 客户端工程师）。只在用户明确要求或在更新提醒里批准后使用；应用到技能层还需要用户拍板。
allowed-tools: Agent, Bash(python3 *refresh_check.py* --mark-refreshed), Bash(python3 *apply_proposal.py* --check), Bash(python3 *usage_report.py*)
---

# /skills-refresh [角色或领域…]

1. 范围 = `$ARGUMENTS` 里的角色（中文名或 slug）/ 领域。为空时运行 `python3 "__HOME__/scripts/usage_report.py"`，把排行给用户看，**请用户选**要更新的角色，用户回复前不要继续（不回复不消耗 AI 用量）。
2. 用 Agent 工具调用子 agent `tech-scout`，输入：选中的角色列表（slug）、今天日期、`__HOME__/config/sources.yaml` 路径。情报员只侦察这些角色相关的信息源，输出 `__HOME__/proposals/<日期>-<领域>.md`。
3. 情报员返回后，**先运行**（主会话有 Bash，情报员没有）：
   - `python3 "__HOME__/scripts/refresh_check.py" --mark-refreshed`：记录本次侦察时间，不论提案之后通过还是驳回，30 天内不再提醒；
   - `python3 "__HOME__/scripts/apply_proposal.py" <提案> --check`：格式、来源、重复驳回自检，有错误就退回情报员修正一次。
   然后把提案摘要给用户：一共几条、每条的变化 / 建议成熟度 / 证据、待核实条目、失败的信息源。
4. **等用户拍板**（`--approve` 不在免确认范围里，执行时 Claude Code 会再请用户确认）（有知识库时总控可用 kb_ask），然后运行：
   `python3 "__HOME__/scripts/apply_proposal.py" <提案> --approve <编号,…> --reject <编号,…>`
   它会应用通过的条目、build、validate、跑回归评测；退化时自动拒绝并还原。
5. 通过后提示用户运行 `__HOME__/install.sh --update --project <目录>` 同步到项目。

不要在后台定时运行，也不要装 launchd / cron。
