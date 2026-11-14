# ask 模式样例：立项拍板停下 → 用户打回 → 退回产品经理修改（REQ-010 / REQ-016）

真实运行产物。DemoApp 用 `install.sh --mcp none` 安装，`approval_mode: ask`（默认值）。共运行两次：

1. `claude -p --agent orchestrator "需求：…签到 + 积分…"`
   - 结果：总控调用产品经理写 PRD，再调用 AI 产品经理填「AI 机会评估」（结论：不用 AI）。validate 通过后，在 🟥 立项节点**停下**，输出待拍板摘要（结论、10 个决策点、建议、影响、怎么回复），没有进入 03。
   - 记录：`第1次运行-停在立项.md`；打回前的 PRD 存为 `02-PRD-打回前.md`。
2. `claude -p --continue --agent orchestrator "打回：D1 改为第 5 天 +20…，D3 本期做补签…"`
   - 结果：log.md 先记一条 `approval` 记录（`"mode":"ask","result":"打回"`），然后**只退回主导角色产品经理**修改 PRD（v0.1 → v0.2，补签新增 US-08~10、R11~R14），没有从头再来。
   - 改完重新 validate，再次停在立项节点等拍板。
   - 记录：`第2次运行-打回后.md`。

流转日志见 `workspace/checkin-points/log.md`。auto 模式的完整流程样例见 `../checkin-points/`。
