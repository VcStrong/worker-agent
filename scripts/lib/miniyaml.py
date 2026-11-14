"""零依赖的 YAML 子集解析器（够本套件的配置和技能包 frontmatter 用）。

支持：
- 块状映射 key: value、嵌套缩进
- 块状列表 - item（item 可以是标量或 key: value 映射）
- 行内列表 [a, b, "c"]、行内映射 {a: 1, b: x}
- 标量：带引号字符串、整数、浮点、true/false、null/~、其余按字符串
- 注释 #（引号外）
不支持：多行字符串（| >）、锚点、多文档。
"""
import re

__all__ = ["load", "loads", "dumps", "YAMLError"]


class YAMLError(ValueError):
    pass


def _strip_comment(line):
    out, q = [], None
    for i, ch in enumerate(line):
        if q:
            out.append(ch)
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
            out.append(ch)
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _split_flow(s):
    """按顶层逗号切分行内集合内容。"""
    parts, depth, q, cur = [], 0, None, []
    for ch in s:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        parts.append(tail)
    return parts


def _find_colon(s):
    """返回顶层（引号、括号外）第一个 'key: ' 冒号位置，没有返回 -1。"""
    q, depth = None, 0
    for i, ch in enumerate(s):
        if q:
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == ":" and depth == 0 and (i + 1 == len(s) or s[i + 1] in " \t"):
            return i
    return -1


def _scalar(s):
    s = s.strip()
    if s == "":
        return None
    if s[0] == "[" and s[-1] == "]":
        return [_scalar(x) for x in _split_flow(s[1:-1])]
    if s[0] == "{" and s[-1] == "}":
        d = {}
        for part in _split_flow(s[1:-1]):
            c = _find_colon(part + " ") if not part.endswith(":") else len(part) - 1
            if c < 0:
                raise YAMLError("行内映射缺少冒号：%s" % part)
            d[_key(part[:c])] = _scalar(part[c + 1:])
        return d
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        body = s[1:-1]
        if s[0] == '"':
            body = body.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")
        else:
            body = body.replace("''", "'")
        return body
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _key(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def loads(text):
    lines = []
    for raw in text.splitlines():
        if raw.strip() in ("---", "...") and not raw.startswith(" "):
            continue
        line = _strip_comment(raw.replace("\t", "  "))
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        lines.append((indent, line.strip()))
    if not lines:
        return {}
    val, idx = _parse_block(lines, 0, lines[0][0])
    if idx != len(lines):
        raise YAMLError("无法解析第 %d 行附近：%s" % (idx + 1, lines[idx][1]))
    return val


def _parse_block(lines, i, indent):
    if lines[i][1].startswith("- ") or lines[i][1] == "-":
        return _parse_list(lines, i, indent)
    return _parse_map(lines, i, indent)


def _parse_list(lines, i, indent):
    out = []
    while i < len(lines) and lines[i][0] == indent and (lines[i][1].startswith("- ") or lines[i][1] == "-"):
        content = lines[i][1][1:].strip()
        if content == "":
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                v, i = _parse_block(lines, i, lines[i][0])
                out.append(v)
            else:
                out.append(None)
            continue
        c = _find_colon(content)
        if c >= 0 and not content.startswith(("[", "{", '"', "'")):
            # 列表项是映射：把 "- k: v" 视为缩进 indent+2 的映射首行
            sub = [(indent + 2, content)]
            j = i + 1
            while j < len(lines) and lines[j][0] > indent:
                sub.append(lines[j])
                j += 1
            v, k = _parse_map(sub, 0, indent + 2)
            if k != len(sub):
                raise YAMLError("列表项缩进不一致：%s" % sub[k][1])
            out.append(v)
            i = j
        else:
            out.append(_scalar(content))
            i += 1
    return out, i


def _parse_map(lines, i, indent):
    out = {}
    while i < len(lines) and lines[i][0] == indent:
        content = lines[i][1]
        if content.startswith("- "):
            break
        c = _find_colon(content)
        if c < 0:
            raise YAMLError("缺少冒号：%s" % content)
        key = _key(content[:c])
        rest = content[c + 1:].strip()
        i += 1
        if rest == "":
            if i < len(lines) and lines[i][0] > indent:
                v, i = _parse_block(lines, i, lines[i][0])
            elif i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
                v, i = _parse_list(lines, i, indent)
            else:
                v = None
            out[key] = v
        else:
            out[key] = _scalar(rest)
    return out, i


def load(path):
    with open(path, encoding="utf-8") as f:
        return loads(f.read())


def _dump_scalar(v):
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_dump_scalar(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join("%s: %s" % (k, _dump_scalar(x)) for k, x in v.items()) + "}"
    s = str(v)
    if s == "" or re.search(r"[:#\[\]{},&*!|>'\"%@`]", s) or s.strip() != s or s.lower() in (
            "true", "false", "yes", "no", "null", "~") or re.fullmatch(r"-?\d+(\.\d+)?", s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def dumps(data, indent=0):
    """把 dict 写成块状 YAML（列表里的标量写成 - 项，嵌套 dict 递归）。"""
    pad = " " * indent
    lines = []
    for k, v in data.items():
        if isinstance(v, dict) and v:
            lines.append("%s%s:" % (pad, k))
            lines.append(dumps(v, indent + 2))
        elif isinstance(v, list) and v and any(isinstance(x, (dict, list)) for x in v):
            lines.append("%s%s:" % (pad, k))
            for x in v:
                if isinstance(x, dict):
                    sub = dumps(x, indent + 4).splitlines()
                    sub[0] = pad + "  - " + sub[0].lstrip()
                    lines.extend(sub)
                else:
                    lines.append("%s  - %s" % (pad, _dump_scalar(x)))
        elif isinstance(v, list) and v:
            lines.append("%s%s:" % (pad, k))
            for x in v:
                lines.append("%s  - %s" % (pad, _dump_scalar(x)))
        else:
            lines.append("%s%s: %s" % (pad, k, _dump_scalar(v)))
    return "\n".join(lines)
