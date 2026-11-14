"""检测 Claude Code 里配置了哪些 MCP：kb（知识库）、Context7（文档类）。

读取：~/.claude.json 的 mcpServers 和 projects[<目录>].mcpServers、<项目>/.mcp.json、
<项目>/.claude/settings*.json、~/.claude/settings.json。只看服务器名，不读其它内容。
"""
import json
import os

KB_NAMES = ("kb",)
DOCS_NAMES = ("context7",)


def _servers_from(path, project=None):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return set()
    names = set((data.get("mcpServers") or {}).keys())
    if project and isinstance(data.get("projects"), dict):
        proj = data["projects"].get(os.path.abspath(project)) or {}
        names |= set((proj.get("mcpServers") or {}).keys())
    return names


def mcp_servers(project=None):
    home = os.path.expanduser("~")
    names = set()
    names |= _servers_from(os.path.join(home, ".claude.json"), project)
    names |= _servers_from(os.path.join(home, ".claude", "settings.json"))
    if project:
        for rel in (".mcp.json", ".claude/settings.json", ".claude/settings.local.json"):
            names |= _servers_from(os.path.join(project, rel))
    return names


def detect(project=None):
    names = {n.lower(): n for n in mcp_servers(project)}
    kb = next((names[n] for n in names if n in KB_NAMES), None)
    docs = next((names[n] for n in names if any(d in n for d in DOCS_NAMES)), None)
    return {"kb": kb, "context7": docs}
