#!/bin/bash
# REQ-020 e2e (review round 1): one unattended claude -p per kb session type, same flags kb uses
# (-p --permission-mode auto --output-format stream-json --verbose; read-only types add --disallowedTools).
# Each session runs the same typical command set in a scratch git repo and reports each result.
# 手动跑（会调用 claude，约 $0.35 / 类会话）：
#   bash tests/e2e/kb_sessions.sh dev end an-analysis an-fix stack launch scaffold px flow steward
#   python3 tests/e2e/kb_sessions_summary.py [输出目录]
# 需要先装好用户级 hooks（./install.sh --user）。结果记录见 docs/evidence/kb-hooks-e2e.md。
OUT=${KB_E2E_OUT:-/tmp/kbhook-e2e/sessions}
mkdir -p "$OUT"
P="pu""sh"
PROMPT="你在一个测试仓库里，按顺序逐条用 Bash 执行下面的命令（每条单独一次 Bash 调用，被拒绝就记下拒绝原因然后继续下一条，不要重试、不要换写法、不要调用 kb 工具）：
1) git status --short
2) grep -rn \"git $P\\|rm -rf\" README.md || true
3) echo '- 补充说明' >> NOTES.md && git add -A && git commit -q -m \"docs: 说明 rm -rf 与 git $P 的风险\" && git log --oneline -1
4) mkdir -p build && touch build/a.o && rm -rf build && echo removed-build
5) git $P origin main
6) git reset --hard HEAD
最后输出一张表：序号 | 结果（执行成功 / 被拒绝）| 一句话说明。"
RO="--disallowedTools Edit Write MultiEdit NotebookEdit"
run() {
  local kind="$1" env="$2" extra="$3"
  local R; R=$(mktemp -d $OUT/repo-XXXX)
  (cd "$R" && git init -q -b main && printf '# demo\nrm -rf 和 git %s 只出方案\n' "$P" > README.md && git add -A \
     && git -c user.name=t -c user.email=t@t commit -q -m init && git remote add origin "$R/../no-such-remote.git")
  local f="$OUT/${kind//[:\/]/_}.jsonl"
  local s=$(date +%s)
  (cd "$R" && KB_SESSION="$env" perl -e 'alarm 420; exec @ARGV' claude -p "$PROMPT" --permission-mode auto \
     --output-format stream-json --verbose $extra > "$f" 2> "$f.err")
  local rc=$?
  echo "== $kind (KB_SESSION=$env) rc=$rc secs=$(( $(date +%s) - s )) log=$f"
}
sel=" $* "
[[ "$sel" == *" dev "* ]] && run "dev" "dev" ""
[[ "$sel" == *" end "* ]] && run "end" "end:Android" ""
[[ "$sel" == *" an-analysis "* ]] && run "an-analysis" "an:demo" "$RO"
[[ "$sel" == *" an-fix "* ]] && run "an-fix" "an:demo" ""
[[ "$sel" == *" stack "* ]] && run "stack" "stack:demo" "$RO"
[[ "$sel" == *" launch "* ]] && run "launch" "launch:需求:demo" "$RO"
[[ "$sel" == *" scaffold "* ]] && run "scaffold" "scaffold:Web" ""
[[ "$sel" == *" px "* ]] && run "px" "px:demo" ""
[[ "$sel" == *" flow "* ]] && run "flow" "flow" ""
[[ "$sel" == *" steward "* ]] && run "steward" "steward" ""
