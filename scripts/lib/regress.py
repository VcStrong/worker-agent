"""REQ-024：回归比较（选角评测 + 技能回归题）。

按用例逐条比：上次通过、这次失败 = 退化；另外新加的用例没通过也算（列出来）。
只按逐条结果判定，不拿比率比较：成绩相同（同样的用例失败）不算退化，四舍五入的旧基线也不会误判。
"""
EPS = 1e-9


def _key(r, kind):
    return r["task"] if kind == "routing" else r["id"]


def compare(prev_results, cur_results, prev_rate, cur_rate, kind):
    """返回退化说明列表（空 = 没有退化）。"""
    prev = {_key(r, kind): r for r in prev_results or []}
    out = []
    for r in cur_results:
        k = _key(r, kind)
        if r["ok"]:
            continue
        if k in prev and prev[k]["ok"]:
            out.append(_fmt(r, kind, "退化"))
        elif k not in prev:
            out.append(_fmt(r, kind, "新用例未通过"))
    if out:
        label = "选角命中率" if kind == "routing" else "技能题通过率"
        out.insert(0, "%s %s → %.1f%%" % (label, "—" if prev_rate is None else "%.1f%%" % (prev_rate * 100), cur_rate * 100))
    return out


def _fmt(r, kind, tag):
    if kind == "routing":
        return "  %s：%s（期望 %s，得到 %s）" % (tag, r["task"], r["expect"], r["got"])
    return "  %s：%s %s（%s）" % (tag, r["id"], r["scenario"], r["why"])
