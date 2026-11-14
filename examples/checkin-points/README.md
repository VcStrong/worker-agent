# 端到端样例：App 每日签到 + 积分（REQ-016 验收基线）

**真实运行产物**，不是手写的示例。生成方式：

1. 在临时项目 DemoApp（说明见 `DemoApp-README.md`；Android 客户端 + Go 后端，空仓库）里运行 `./install.sh --project <DemoApp> --mcp none`。这次运行不接知识库，避免写进真实的知识库。
2. 把安装位置的 `.claude/role-agents/config/run.yaml` 改成 `approval_mode: auto`。
3. 运行 `claude -p --agent orchestrator --permission-mode acceptEdits --allowedTools …`。需求原文见 `总控最终汇报.md` 开头的说明：从 02 需求立项跑到 08 发布上线，只出上线方案、不部署；为控制成本，Android 端只出实现说明和自测记录。
4. 运行时间：2026-11-14 23:31 到 2026-11-15 00:08，退出码 0。

## 验收对照

| 验收标准 | 结果 |
|---|---|
| 至少 5 份产物（PRD 含 AI 机会评估、交互说明、技术方案 / 接口契约、测试报告、上线单），且都通过模板校验 | ✅ `workspace/checkin-points/` 下共 9 份产物：02-PRD、04-交互说明、04-视觉标注、05-技术方案、06-自测记录-后端 / Android、07-测试报告、08-上线单、08-监控告警。`python3 scripts/validate.py --deliverable …` 结果 0 错误 |
| log.md 里有 5~10 个不同角色参与，含 AI 产品经理 | ✅ 共 9 个角色：总控、产品经理、AI 产品经理、体验设计师、架构师、后端工程师、客户端工程师、测试专家、SRE 与安全工程师；角色调用 11 次 |
| 3 个拍板节点都触发过（auto 模式下有记录） | ✅ log.md 里 02 立项、05 技术方案、08 上线放量各有一条「自动按建议执行」及理由 |
| 生成经验条目和使用度记录 | ✅ `proposals/lessons-checkin-points.md`（8 条，`apply_proposal.py --check` 通过）；`usage/usage.jsonl` 由真实 hook 采集，包括角色调用、SubagentStop 和 1 次 SKILL.md 读取 |
| AI 产品经理参与、AI 应用 / AI 合规不参与（普通需求只多 1 个角色） | ✅ AI 机会评估结论为「不用 AI」 |
| 最少角色、并发、重试 | ✅ 05 的数据模型由架构师兼；06 后端和 Android 并发；Code Review 打回一次（跨零点乱序导致少发奖励），用掉唯一一次重试 |
| 部署 / 删除只出方案 | ✅ 没有部署；体验设计师误建的临时文件，总控请用户确认后再删，没有擅自删除 |

## 没验证的部分

- 运行机器上没有 Go 工具链，`server/` 代码只做了静态自查，没有编译和测试；`07-测试报告` 结论是「有条件通过」。总控因此在 08 冻结放量，把补测列为上线单的阻断项。
- 这是 approval_mode=auto 的运行。ask 模式下会在 3 个节点停下，见 `agents/orchestrator.md`。
