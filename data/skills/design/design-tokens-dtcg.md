---
id: design-tokens-dtcg
name: 设计 Token（W3C DTCG 格式 2025.10）
aliases: [Design Tokens, DTCG, 设计令牌, Style Dictionary, tokens.json]
roles: [ux-designer, frontend-engineer]
maturity: 试用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://www.w3.org/community/reports/design-tokens/CG-FINAL-format-20251028/
  - https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/
  - https://www.designtokens.org/tr/2025.10/format/
  - https://styledictionary.com/info/dtcg/
region: both
replaces: []
replaced_by: []
from_graph: false
---

# 设计 Token（W3C DTCG 格式 2025.10）

当前版本：Design Tokens Format Module 2025.10（2025-10-28 发布，首个稳定版；同时发布 Resolver Module 2025.10）。注意它是 W3C 社区组最终报告，不是 W3C 标准轨道规范。
判断理由：核心格式已声明可用于生产，主流工具（Style Dictionary 等）已支持，但各设计工具的导入导出支持程度不一，定「试用」。

## 什么时候用
- 设计系统要同时供给 Web、Android、iOS、鸿蒙、小程序，需要一份与工具无关的 token 源文件。
- 多主题 / 多品牌，需要可追溯的别名关系。
- 替代图谱 D-02 的「设计 Token 插件」私有格式。

## 关键做法
- 文件用 JSON，token 以 `$value`、`$type`、`$description` 描述；组用嵌套对象；别名用 `{color.blue.500}` 引用。
- 三层结构：primitive（原始值）→ semantic（用途）→ component（组件级，可选）。
- token 文件放 Git 仓库，设计改动走 PR 评审；Figma Variables / MasterGo 只是编辑入口。
- 用 Style Dictionary 等工具按 DTCG 输入生成 CSS 变量、Android XML / Compose、Swift、ArkTS 常量。
- 主题与多模式用 Resolver Module 的思路组织（集合 + 修饰），不要每个主题复制一整份。

## 常见坑
- 旧插件导出的格式没有 `$` 前缀，和 DTCG 不兼容，需要转换脚本。
- 颜色、尺寸类型的值结构按规范写（如颜色带色彩空间），不要只写字符串习惯值。
- 只导出不回写：设计端改了变量但没同步仓库，两边漂移。

## 迁移
- 从 Tokens Studio 等旧格式迁移：用工具转换为 DTCG，跑一次全量生成并做视觉回归对比。
- 存量代码里硬编码色值：先建 semantic token 映射，再按页面逐步替换。

## 最佳做法
- CI 校验 token 文件：类型正确、别名可解析、无循环引用。
- 风险与回退：工具不支持 DTCG 时，保留转换脚本作为适配层，源文件不动。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
