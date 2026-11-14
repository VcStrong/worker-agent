---
name: go-modern
description: "Go 1.27（新版本特性与升级）（成熟度 采用，as_of 2026-11-14）：新建 Go 服务：go.mod 写 `go 1.27`（或团队统一的 1.26），CI 用最新补丁版。 适用角色：后端工程师。"
---
<!-- generated-by: scripts/build.py；源文件 data/skills/backend/go-modern.md，请勿手改 -->

> 成熟度：**采用**（region=cn）｜版本 1.0.0｜as_of 2026-11-14｜来源：https://go.dev/doc/devel/release https://go.dev/doc/go1.27 https://go.dev/doc/go1.26

# Go 1.27（新版本特性与升级）

当前版本：Go 1.27（2026-08-19 发布，最新补丁 go1.27.4）；Go 1.26 于 2026-02-10 发布。Go 官方只维护最近两个大版本（1.27、1.26）。图谱后端工具原有「Go / Java 工具链」。
判断理由：Go 一年两版、兼容承诺稳定，官方发布说明明确；新特性（泛型方法、encoding/json v2 默认、goroutine 泄漏分析 GA）可直接用于生产，判「采用」。

## 什么时候用
- 新建 Go 服务：go.mod 写 `go 1.27`（或团队统一的 1.26），CI 用最新补丁版。
- 存量服务：低于 1.26 的已不在官方支持范围，排期升级。
- 高并发网关、中间件、CLI、云原生组件（K8s Operator 等）首选 Go。

## 关键做法
- 升级用 `go get go@1.27.4` + `toolchain` 指令统一工具链；升级后跑 `go fix ./...`（1.26 起 go fix 承载 modernizers，自动改成新写法）。
- 1.27 起 `encoding/json` 底层换成 json/v2：默认拒绝非法 UTF-8 和重复键，反序列化更快；有兼容问题先用 `GOEXPERIMENT=nojsonv2` 回退再改代码。
- 线上排查用 `/debug/pprof/goroutineleak`（1.27 GA）找永远阻塞的 goroutine。
- 1.26 起 Green Tea GC 默认开启，升级后对比 GC CPU 与 P99 延迟。
- 新标准库：`uuid` 包（1.27）可替代第三方 UUID 库；`crypto/mldsa`、TLS `MLKEM1024` 为后量子密码做准备。

## 常见坑
- 1.27 移除 `asynctimerchan`，time 通道恒为无缓冲；依赖旧行为的代码会编译失败或行为变化。
- json/v2 默认更严格，对接老客户端（重复键、非 UTF-8）时要回归测试。
- Darwin 构建要求 macOS 13+；交叉编译机器老旧时注意。
- `vet` 新增 `%w` 包装 `*E` 指针的告警，修正后 `errors.Is` / 类型断言才可靠。

## 迁移
- 一次只跨一个大版本：1.25 → 1.26 → 1.27，每步跑全量测试 + 压测。
- 先在 go.mod 升 `go` 指令，再跑 `go fix`、`go vet`，最后清理 GODEBUG 兼容开关。
- 第三方 UUID / JSON 库替换为标准库属可选优化，单独提交。

## 最佳做法
- CI 里固定 Go 补丁版本，并用 Renovate / Dependabot 自动提补丁升级 PR。
- 发布说明里的 GOEXPERIMENT 回退开关只作临时手段，下个大版本前必须去掉。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
