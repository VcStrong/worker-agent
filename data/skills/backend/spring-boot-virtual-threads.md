---
id: spring-boot-virtual-threads
name: Spring Boot 4 + Java 虚拟线程
aliases: [Spring Boot 4, Spring Boot 3, 虚拟线程, Virtual Threads, Project Loom, Java 21, Java 25]
roles: [backend-engineer, architect]
maturity: 采用
as_of: 2026-11-14
version: 1.0.0
sources:
  - https://spring.io/projects/spring-boot#support
  - https://spring.io/blog/2026/06/10/spring-boot-4/
  - https://github.com/spring-projects/spring-boot/releases
  - https://openjdk.org/projects/jdk/
  - https://openjdk.org/jeps/491
region: both
replaces: []
replaced_by: []
from_graph: true
---

# Spring Boot 4 + Java 虚拟线程

当前版本：Spring Boot 4.1.2（4.1 于 2026-06 GA，OSS 支持到 2027-07）；4.2.0-RC2 已发布（2026-11-05），计划 2026-11 下旬 GA。Spring Boot 3.5.x 的开源支持已于 2026-06-30 结束（仅商业支持）。JDK 25 为当前 LTS（2025-09 GA），JDK 27 于 2026-09 GA。图谱后端工具原有「Go / Java 工具链」。
判断理由：候选写的是「Spring Boot 3 + Java 21」，核实后 Spring Boot 已进入 4.x，3.x 开源支持已结束；新项目应直接用 Boot 4.1+ 搭配 JDK 25 LTS 的虚拟线程，判「采用」。

## 什么时候用
- 新 Java 服务：Spring Boot 4.1（或 4.2 GA 后）+ JDK 25 LTS（最低 JDK 17，虚拟线程需 21+）。
- 阻塞 I/O 为主（JDBC、HTTP 调用、消息消费）的业务服务，用虚拟线程替代大线程池 / 响应式改造。
- 已用 WebFlux 且团队熟练的，可保留，不必为虚拟线程回迁。

## 关键做法
- 打开 `spring.threads.virtual.enabled=true`，Tomcat / Jetty、`@Async`、调度器等自动切到虚拟线程。
- 用 JDK 24+（推荐 25 LTS）：JEP 491 解决了 `synchronized` 钉住载体线程的问题；JDK 21 下仍要把热点 `synchronized` 换成 `ReentrantLock`。
- 下游资源（数据库连接池、外部 API）要单独限流（信号量 / 连接池上限），虚拟线程不会帮你保护下游。
- Boot 4.1 起内置 gRPC 自动配置、读取 OpenTelemetry 标准环境变量、HTTP 客户端 SSRF 防护（`InetAddressFilter`），优先用官方能力。

## 常见坑
- 把 ThreadLocal 当缓存大量使用：百万级虚拟线程会放大内存，改用 ScopedValue 或请求上下文。
- 以为虚拟线程能提升 CPU 密集任务性能：不能，CPU 密集仍用固定大小线程池。
- 连接池（HikariCP）大小不变而并发暴涨，导致排队超时。
- 直接从 Boot 2.x / 3.0 跳到 4.x：Jakarta EE 11、Jackson 3、模块化 starter 改动多，要分步升。

## 迁移
- 2.7 → 3.5 → 4.0 → 4.1 逐级升级，每级先清掉 deprecation 告警（4.1 已删除 4.0 中标废弃的 API，如 layertools）。
- 用 OpenRewrite 的 Spring Boot 升级配方批量改依赖与配置；`spring-boot-properties-migrator` 检查改名属性。
- JDK 先升到 21/25 并跑满回归，再开虚拟线程，二者分开发布便于回滚。

## 最佳做法
- 开虚拟线程前后各压测一次，对比吞吐、P99、连接池等待时间，用 JFR 的 `jdk.VirtualThreadPinned` 事件排查钉住。
- 版本选择以 spring.io 支持表为准：避免新项目落在 OSS 支持剩余不足 6 个月的版本线上。

## CHANGELOG
- 2026-11-14 v1.0.0 首版；情报员自动核实（来源见 sources）
