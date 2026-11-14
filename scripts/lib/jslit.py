"""把 JS 对象 / 数组字面量（不带函数、表达式）解析成 Python 对象。

支持：{key: v} 未加引号 / 带引号的键、[...]、"..." '...' `...`（不含 ${}）字符串、数字、true/false/null、
// 和 /* */ 注释、尾逗号。
"""


class JSParseError(ValueError):
    pass


class _P:
    def __init__(self, s, i=0):
        self.s, self.i = s, i

    def ws(self):
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c in " \t\r\n":
                self.i += 1
            elif s.startswith("//", self.i):
                j = s.find("\n", self.i)
                self.i = len(s) if j < 0 else j + 1
            elif s.startswith("/*", self.i):
                j = s.find("*/", self.i + 2)
                if j < 0:
                    raise JSParseError("注释未闭合")
                self.i = j + 2
            else:
                break

    def err(self, msg):
        line = self.s.count("\n", 0, self.i) + 1
        raise JSParseError("%s（第 %d 行附近）" % (msg, line))

    def value(self):
        self.ws()
        c = self.s[self.i]
        if c == "{":
            return self.obj()
        if c == "[":
            return self.arr()
        if c in "\"'`":
            return self.string()
        if c == "-" or c.isdigit():
            return self.number()
        for word, v in (("true", True), ("false", False), ("null", None), ("undefined", None)):
            if self.s.startswith(word, self.i):
                self.i += len(word)
                return v
        self.err("无法识别的值：%r" % self.s[self.i:self.i + 20])

    def obj(self):
        self.i += 1
        out = {}
        while True:
            self.ws()
            if self.s[self.i] == "}":
                self.i += 1
                return out
            if self.s[self.i] in "\"'":
                key = self.string()
            else:
                j = self.i
                while self.s[j].isalnum() or self.s[j] in "_$":
                    j += 1
                if j == self.i:
                    self.err("缺少键名")
                key = self.s[self.i:j]
                self.i = j
            self.ws()
            if self.s[self.i] != ":":
                self.err("键 %s 后缺少冒号" % key)
            self.i += 1
            out[key] = self.value()
            self.ws()
            if self.s[self.i] == ",":
                self.i += 1
            elif self.s[self.i] != "}":
                self.err("对象里缺少逗号")

    def arr(self):
        self.i += 1
        out = []
        while True:
            self.ws()
            if self.s[self.i] == "]":
                self.i += 1
                return out
            out.append(self.value())
            self.ws()
            if self.s[self.i] == ",":
                self.i += 1
            elif self.s[self.i] != "]":
                self.err("数组里缺少逗号")

    def string(self):
        q = self.s[self.i]
        self.i += 1
        buf = []
        esc = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", "'": "'", '"': '"', "`": "`", "/": "/"}
        while True:
            if self.i >= len(self.s):
                self.err("字符串未闭合")
            c = self.s[self.i]
            if c == "\\":
                n = self.s[self.i + 1]
                if n == "u":
                    buf.append(chr(int(self.s[self.i + 2:self.i + 6], 16)))
                    self.i += 6
                    continue
                buf.append(esc.get(n, n))
                self.i += 2
                continue
            if c == q:
                self.i += 1
                return "".join(buf)
            buf.append(c)
            self.i += 1

    def number(self):
        j = self.i
        if self.s[j] == "-":
            j += 1
        while j < len(self.s) and (self.s[j].isdigit() or self.s[j] in ".eE+-"):
            j += 1
        txt = self.s[self.i:j]
        self.i = j
        return float(txt) if any(ch in txt for ch in ".eE") else int(txt)


def parse_at(s, i):
    """从 s[i] 开始解析一个字面量，返回 (值, 结束位置)。"""
    p = _P(s, i)
    v = p.value()
    return v, p.i
