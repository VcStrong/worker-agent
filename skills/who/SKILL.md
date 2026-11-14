---
name: who
description: 按岗位名、专家名、术语或技术名反查负责的角色（如 /who 灰度、/who DBA、/who ArkTS、/who --usage）。查原始岗位名返回合并到的专家，查技术名返回挂载角色、成熟度和 as_of，--usage 看角色和技能的使用度排行。
model: haiku
allowed-tools: Bash(python3 *who.py*), Bash(python3 *usage_report.py*)
---

# /who — 按岗位或活儿查角色

运行（参数原样传入，`$ARGUMENTS` 为空时提示用法）：

```bash
python3 "__HOME__/scripts/who.py" $ARGUMENTS
```

- 把脚本输出原样给用户看，不要改写或补充脚本里没有的角色。
- 输出「未找到」时，把给出的 3 个最接近的词列给用户，问他要查哪个。
- `--usage`：使用度排行（次数、最近使用、最旧 as_of、是否过期），用于决定先更新哪些角色的技能。
