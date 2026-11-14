---
id: grpc-connect
name: gRPC / Connect RPC
aliases: [gRPC, Connect, ConnectRPC, connect-go, Protobuf, buf]
roles: [backend-engineer, architect]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://grpc.io/
  - https://github.com/grpc/grpc-go/releases
  - https://connectrpc.com/docs/introduction
  - https://github.com/connectrpc/connect-go/releases
region: both
replaces: []
replaced_by: []
from_graph: false
---

# gRPC / Connect RPC

当前版本：grpc-go v1.85.0（2026-10-27）；connect-go v2.0.2（2026-10-21，v1.21.x 仍维护）。Connect 为 CNCF 沙箱项目，Go / TypeScript / Swift / Dart 实现稳定，Kotlin / Python 为 Beta。
判断理由：gRPC 是服务间 RPC 的事实标准，判「采用」；Connect 同时兼容 gRPC / gRPC-Web / 自有 HTTP 协议，浏览器可直连无需 Envoy 转换，作为对外 / 前端调用的方案，Go 与 TS 场景可直接用，其它语言按「试用」对待。

## 什么时候用
- 内部微服务之间：gRPC（强类型、流式、跨语言）。
- Web / App 前端要直接调后端、又想共用 Protobuf 契约：Connect（HTTP/1.1 即可，JSON 可读、便于调试）。
- 对外开放平台、第三方集成：仍优先 REST / OpenAPI，gRPC 作为可选。

## 关键做法
- Protobuf 契约单独建仓或目录，用 buf 做 lint、breaking change 检查和代码生成。
- 字段只增不改号；删除字段用 `reserved`；新增字段默认可选。
- 设置 deadline / timeout 并向下游传播；重试只对幂等方法开启。
- Java 服务可用 Spring Boot 4.1 内置 gRPC 自动配置；Go 服务新项目可直接用 connect-go，一套 handler 同时服务 gRPC 和 Connect 客户端。
- 接入 OpenTelemetry 拦截器，trace 贯穿 RPC 链路。

## 常见坑
- 经过不支持 HTTP/2 trailer 的 LB / CDN 时 gRPC 失败；对外入口需确认网关支持，或换 Connect 协议。
- 大消息（> 4MB 默认上限）直接报错，大文件改走对象存储 + 传 URL。
- 长连接 + K8s Service 导致负载不均：用客户端负载均衡（xDS / headless service）或网关层 L7 均衡。
- Kotlin / Python 的 Connect 实现仍是 Beta，生产要有回退到标准 gRPC 客户端的方案。

## 迁移
- REST → gRPC：先为新接口定义 proto，旧 REST 通过 gRPC-Gateway 或 Connect 的 JSON 能力兼容。
- 已有 gRPC-Web + Envoy：服务端换 Connect 后可去掉转换代理，客户端逐步换 Connect-ES。

## 最佳做法
- 在 CI 里强制 `buf breaking`，契约破坏性变更必须走评审。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
