---
name: skills-refresh
description: 让技术情报员侦察选中角色或领域的技术变化并更新技能（如 /skills-refresh 前端工程师 客户端工程师）。默认（run.yaml skills_refresh_mode=auto）技能会按周期自动学习、自动应用；这个命令用于立即手动跑一次。
allowed-tools: Agent, Bash(python3 *refresh_check.py* --mark-refreshed), Bash(python3 *apply_proposal.py* --check), Bash(python3 *apply_proposal.py* --auto*), Bash(python3 *usage_report.py*), Bash(python3 *auto_refresh.py*)
---

# /skills-refresh [角色或领域…]

默认模式 auto（`__HOME__/config/run.yaml` 的 `skills_refresh_mode`）：worker-agent 每 `skills_refresh_interval_days` 天（默认 7）自动侦察全部角色、核实后自动应用，事后在 `__HOME__/proposals/summaries/` 出摘要，不弹确认。状态：`python3 "__HOME__/scripts/auto_refresh.py" --status`；立即全量跑一次：`python3 "__HOME__/scripts/auto_refresh.py" --run --force`。

手动执行 /skills-refresh 时：

1. 范围 = `$ARGUMENTS` 里的角色（中文名或 slug）/ 领域。为空时 auto 模式覆盖全部角色；ask 模式运行 `python3 "__HOME__/scripts/usage_report.py"` 把排行给用户看，请用户选。
2. 用 Agent 工具调用子 agent `tech-scout`，输入：选中的角色列表（slug）、今天日期、`__HOME__/config/sources.yaml` 路径。情报员只侦察这些角色相关的信息源，输出 `__HOME__/proposals/<日期>-<领域>.md`。
3. 情报员返回后运行：
   - `python3 "__HOME__/scripts/refresh_check.py" --mark-refreshed`：记录本次侦察时间；
   - `python3 "__HOME__/scripts/apply_proposal.py" <提案> --check`：格式、来源、重复驳回自检，有错误就退回情报员修正一次。
4. 应用：
   - auto 模式（默认）：直接运行 `python3 "__HOME__/scripts/apply_proposal.py" <提案> --auto`。核实过的条目全部应用（版本、成熟度、新增技能、废弃、新增 / 下线角色），待核实、可疑来源、重复驳回的跳过；回归退化的条目自动剔除；最后打快照。把结果简短告诉用户：改了哪些技能、来源链接、大改动、回滚命令（`python3 "__HOME__/scripts/rollback.py"`），不用等确认。
   - ask 模式：把提案摘要给用户，等用户拍板（有知识库时可用 kb_ask），再运行 `python3 "__HOME__/scripts/apply_proposal.py" <提案> --approve <编号,…> --reject <编号,…>`。
5. 运行 `__HOME__/install.sh --update --project <目录>` 同步到项目（auto 模式下定期自动更新会自己同步已安装的项目）。
