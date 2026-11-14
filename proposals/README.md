# 提案目录（REQ-021 / 023 / 025）

- `<YYYY-MM-DD>-<领域或角色>.md`：技术情报员的技能更新提案
- `lessons-<需求名>.md`：需求结束时总控收集的经验条目
- `unverified.md`：核实不到一手来源的候选（不写入技能层）
- `rejected.jsonl`：被驳回的条目（以后不重复提出，除非有新证据）
- `apply.log`：应用记录

**所有条目都要用户拍板后才由 `scripts/apply_proposal.py` 应用**（例外：`config/run.yaml` 的 `auto_apply_trivial: true` 时，标 `trivial: true` 的 update_as_of / add_source / fix_typo 可自动应用并记日志）。

## 条目格式

每条一个三级标题 + 一个 yaml 代码块（YAML 子集：不要多行字符串）。新增技能（add_skill）再紧跟一个 markdown 代码块放完整技能包（格式见 docs/skill-pack-format.md）。

````markdown
### P20261201-fe-01 Vite 升级到 9
```yaml
action: update_version        # 见下表
skill: vite                   # 技能 id
fields: {version: 1.1.0}      # update_version / update_fields 要改的元数据
note: "- Vite 9 默认 xxx"     # 可选：追加到 section 节
section: 关键做法
evidence: [https://vite.dev/blog/announcing-vite9]
published: 2026-11-20
roles: [frontend-engineer]
suggested_maturity: 采用
reason: 官方 GA，主流框架已适配
trivial: false
status: 待拍板                # 待拍板 / 待核实 / 已应用 / 驳回（apply_proposal 回写）
suspicious_sources: []        # 网页里出现可疑指令的来源
```
````

| action | 用途 | 关键字段 |
|---|---|---|
| add_skill | 新增技能 | domain + 后面紧跟 ```markdown 完整技能包 |
| update_maturity | 成熟度升降 | skill, suggested_maturity, evidence |
| deprecate | 废弃（改为暂缓） | skill, replaced_by, replacement_note |
| update_version / update_fields | 版本更新、改元数据 | skill, fields, note, section |
| update_as_of | 只更新核实日期（小改动） | skill, as_of, trivial: true |
| add_source | 补来源链接（小改动） | skill, evidence, trivial: true |
| fix_typo | 修错别字（小改动） | skill, from, to, trivial: true |
| append_lesson | 经验回流（复盘） | skill, section（常见坑 / 最佳做法）, text, source_need, role, scope（public / local） |
| merge_role | 新岗位并入现有专家 | role, role_def, target |
| new_role | 新增专家（超 role_cap 时必须带 retire_or_merge） | slug, name, kind, model, profile, role_def |
| retire_role | 下线专家 | slug, replacement, reason |

## 经验条目（lessons-<需求名>.md）

每条写明：来源需求（source_need）、角色（role）、现象和建议（text）、建议改哪个技能包（skill）、范围（scope：通用 → public；只适用于用户某个项目 → local，写进 `local/skills/` 覆盖层）。和已有技能包内容重复的会自动合并、不重复写入。
