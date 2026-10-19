# Verification

日期：2026-10-19。目标宿主：Aide 7774f424 / 0.1.17.1 RC1。

## 已验证

- PASS：10 项 Node 回归，覆盖摘要、搜索/ID、方向过滤、路径/逆向证据、深度上限、索引不完整、工作区/锁屏代际变化、缺失凭据、固定回环 HTTPS/CA 校验/路由限制及工具注册。
- PASS：Node 语法检查；ZIP 入口大小、清单版本一致性及 CRC 检查；实际 Aide `plugin_host.js validate` 接受自包含入口。
- PASS：通过本地 `POST /api/plugins/bundle` 安装，实际插件卡片显示已启用 StarLink v0.1.0。
- PASS：通过 Aide 原生工作台工具桥调用全部五个工具；另验证纯资料模式摘要，共 6 次工具调用。没有直接绕开宿主执行工具 handler 来冒充集成测试。
- PASS：一次真实代码模式快照为 2340 节点 / 4209 关系；一次纯资料快照为 23498 节点 / 27484 关系。两者均报告 partial，数值随宿主渐进扫描变化，不是全库统计。
- PASS：Safari 从插件卡片打开工作台，显示真实摘要；搜索 workflow 返回 171 个匹配（展示前 30 项）；选择节点可见来源、摘要、关系和设置起终点按钮；真实文件到父目录的逆向 contains 路径返回成功且保留原始箭头方向。折叠索引说明，避免长 warnings 挤占查询入口。
- PASS：纯资料响应约 80 MB 的实例能在 96 MiB 上限内读取；轻量状态检查不读取全图。超限明确失败，不默默丢弃节点。

## 未验证与限制

- PASS：按用户明确要求，在 Aide 新会话 #11 中以 deepseek-flash 实际执行只读任务。模型调用全部五个 StarLink 工具，任务 completed；原始持久化工具记录均为有效 JSON，无工具错误。摘要 3385 节点 / 5944 关系；workflow 搜索 249 匹配取 3 项；真实节点详情和逆向 contains 路径均成功。Safari 最终页面显示“工具调用 5”及逐项结果。文件与命令提案均为 0。
- 证据：[AI 实测记录](reviews/2026-10-19-ai-acceptance.json)。原始会话保留本机 `.agent-state/ai-session.json`，未公开正文。
- 解释纠正：AI 将 status 的 `snapshotLoaded:false / identity:1` 误读为宿主快照滞后。该工具设计上不读取快照，`identity` 与内容 `revision` 是不同维度；这不是工具失败。覆盖范围仍以 summary/search/node/path 的 partial、stale、warnings 为准。
- NOT_RUN：完整资料库索引覆盖验收；宿主报告仍有未发现/待读取/未解析材料。
- NOT_RUN：窄屏与所有配色矩阵。Safari 已检查当前桌面宿主主题。
- UNSUPPORTED：SSH 工作区、`~/` 和 Windows 盘符路径映射，首版明确拒绝。
- 状态工具只确认连接、身份和解锁状态，覆盖范围为未知；其他工具返回索引修订和范围限制。

本轮已覆盖真实模型调用及 Safari 最终结果，仍不能替代完整索引覆盖验收。原始运行日志与索引返回仅留本机 `.agent-state/`，不随公开仓库或 ZIP 分发。
