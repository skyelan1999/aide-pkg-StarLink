# Verification

日期：2026-10-19。当前插件：StarLink 0.1.1。目标宿主：Aide 7774f424 / 0.1.17.1 RC1。

## v0.1.1 无界面版

- PASS：11 项 Node 回归，涵盖查询、证据方向、索引范围、工作区和锁屏代际、凭据/TLS限制、五个工具注册及无 workbench 清单。
- PASS：Node 语法检查与真实 Aide `plugin_host.js validate`。ZIP 清单版本一致、入口小于 256 KiB、CRC 正常、没有 HTML/CSS/工作台资源。
- PASS：通过 Aide 正常升级接口部署 v0.1.1；`GET /api/plugins` 确认 enabled=true、version=0.1.1、workbench=null。
- PASS：工具入口 `index.js` 与已验收的 0.1.0 字节完全一致，只有界面、清单、打包和说明变更。
- PASS：Aide 会话 #12，deepseek-flash 在未打开插件工作台的情况下实际调用 `starlink_status`、`starlink_search`，任务 completed。真实命中 `F3024cf75d8f9` / `docs/plugins/web-research-workflow.md`；搜索 totalMatches=268、partial=true、stale=true。文件和命令提案均为 0。
- 证据：[无界面版 AI 实测](reviews/2026-10-19-tools-only-acceptance.json)。原始会话仅存本机 `.agent-state/ai-no-ui-session.json`。

## v0.1.0 的已有工具验收

- PASS：Aide 会话 #11，deepseek-flash 实际调用全部五个 StarLink 工具，任务 completed；持久化结果和 Safari 最终页面一致，无工具错误。
- 摘要为 3385 节点 / 5944 关系；workflow 搜索 249 匹配取 3 项；节点详情及真实逆向 contains 路径成功。
- 证据：[五个工具 AI 实测](reviews/2026-10-19-ai-acceptance.json)。这部分工具实现沿用至 0.1.1。历史独立工作台已在 0.1.1 移除。
- 纯资料模式曾返回 23498 节点 / 27484 关系；约 80 MB 响应位于 96 MiB 上限内。超限会明确报错，不静默丢弃节点。

## 解释与限制

- 状态检查只确认连接、身份和解锁状态，不加载全图。`snapshotLoaded:false / revision:identity:1` 描述轻量调用，不表示宿主没有快照；它与内容 revision 是不同维度。
- 快照数值随渐进扫描变化；partial/stale/warnings 必须保留。静态关系不是运行轨迹，未收录不代表不存在。
- NOT_RUN：完整资料库索引覆盖验收。
- UNSUPPORTED：SSH 工作区、`~/` 和 Windows 盘符路径映射。Docker 默认工作区及可确认的 POSIX 映射沿用现有支持。
- 原始运行日志及索引正文仅留本机 `.agent-state/`，不随公开仓库或 ZIP 分发。
