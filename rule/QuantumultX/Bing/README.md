# Microsoft Bing Quantumult X Rules

## 规则用途与目标服务

本目录维护 Microsoft Bing Search App 与 Bing 搜索服务的低误匹配 Quantumult X 规则。主规则覆盖搜索首页、文字、图片、视频、新闻、建议、结果资源、Bing API 和视觉搜索。

Quantumult X 常规分流按照请求的目标域名和 IP 匹配，并不是真正按照 iOS App 进程或 Bundle ID 匹配。如果其他 App 请求相同域名，也可能命中该规则。如果 Bing 使用尚未收录的新域名，请求可能进入其他策略。

## 主规则与可选范围

- `Bing.list`：Bing 搜索 App 与搜索服务的核心低误伤域名。
- `Bing-AI.list`：可选的 Copilot Search 与独立 AI 服务域名。

当前 iOS 和 Android 商店仍提供独立的 Microsoft Bing Search App，并在 2026 年版本说明中包含 Copilot Search。独立 Copilot 服务域名仍放入可选文件，避免把 AI 与传统搜索强制合并。

## 数据来源

1. [Bing 官方网站](https://www.bing.com/)
2. [Microsoft Bing Search App Store](https://apps.apple.com/us/app/microsoft-bing-search/id345323231)
3. [Microsoft Bing Visual Search](https://support.microsoft.com/en-US/bing/using-bing-visual-search)
4. [v2fly/domain-list-community Bing](https://github.com/v2fly/domain-list-community/blob/master/data/bing)
5. [MetaCubeX Bing geosite](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/bing.yaml)
6. [blackmatrix7 Bing Quantumult X](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/QuantumultX/Bing)

## 域名确认标准

正式主规则优先使用 Bing 专用根域。Microsoft 大型共享根域只允许在有明确证据时使用精确 HOST；广告、遥测、活动网站、Office、Azure、身份与公共 CDN 根域默认排除。候选 TSV 不会自动进入正式规则。

## 当前更新时间与数量

- 主规则：<!-- BING_MAIN_COUNTS_START -->5 条（HOST 0，HOST-SUFFIX 5，IP-CIDR 0，IP6-CIDR 0）<!-- BING_MAIN_COUNTS_END -->；<!-- BING_MAIN_UPDATED_START -->2026-07-29 04:59:16 UTC<!-- BING_MAIN_UPDATED_END -->
- AI：<!-- BING_AI_COUNTS_START -->3 条（HOST 1，HOST-SUFFIX 2，IP-CIDR 0，IP6-CIDR 0）<!-- BING_AI_COUNTS_END -->；<!-- BING_AI_UPDATED_START -->2026-07-29 04:59:16 UTC<!-- BING_AI_UPDATED_END -->

## 已确认域名摘要

主规则包含 `bing.com`、`bing.com.cn`、`bing.net`、`bingapis.com` 与 `bingvisualsearch.com`。`cn.bing.com`、`r.bing.com`、`th.bing.com` 等当前上游主机已被父域覆盖，不重复添加。

可选 AI 文件包含 `copilot.com`、`copilot.cloud.microsoft` 与精确主机 `copilot.microsoft.com`。不会整体加入 `microsoft.com`、`live.com`、`office.com`、`microsoftonline.com`、`azure.com` 或 `azureedge.net`。

## 候选、广告与排除说明

`bingads.com` 为广告服务，`bingapistatistics.com` 为统计或遥测候选，均不进入核心规则。`bingagencyawards.com`、`bingworld.com`、`bingsandbox.com` 等活动或历史域名也被排除。

`location.microsoft.com` 和 `dictate.ms` 可能被多个 Microsoft 产品共用；在没有 Bing App 专用证据时不收录。公共 Microsoft 登录、支付、云、CDN 和系统服务也保持在规则之外。

## Quantumult X 导入步骤

1. 打开 Quantumult X。
2. 进入 Filter Resources。
3. 添加远程资源。
4. 粘贴相应 `.list` 文件的 Raw 链接。
5. 为资源设置易于识别的名称。
6. 根据自身网络环境和服务可用性，将该远程资源绑定到适当的现有策略组。
7. 启用该资源。
8. 将专用 App 规则放在更宽泛的规则和 Final 之前。
9. 更新所有资源。
10. 完全关闭并重新打开 Microsoft Bing Search。
11. 在 Quantumult X 活动记录中确认目标域名命中预期策略。

## Raw 链接

- [Bing.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bing/Bing.list)
- [Bing-AI.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bing/Bing-AI.list)

## 规则优先级

把 Bing 主规则放在 Microsoft 综合规则、Proxy 和 Final 等宽泛规则之前。AI 文件仅在需要 Copilot Search 或相关功能时独立导入。

## 验证方法

```bash
python3 -m unittest discover -s tests -p "test_bing_rules.py" -v
python3 scripts/update_bing_quantumultx.py --check
python3 scripts/validate_bing_rules.py
```

## 抓漏域名方法

更新资源并清理活动记录后，重新启动 App，测试首页、文字搜索、图片、视频、新闻、建议、视觉搜索、语音入口和可选 AI 功能。只记录域名，删除 query 与 fragment，并隐藏 Token、Cookie、账号和搜索内容。

| App 功能 | 请求域名 | 当前策略 | 所属机构 | 是否专用 | 证据 | 建议 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## 已知限制与误匹配风险

其他 Microsoft 产品也可能请求 Bing 或 Copilot 域名，因此无法保证只影响 Bing App。地区功能、登录状态和产品整合变化也会改变请求集合。

本项目刻意避免收录公共 CDN、共享 SDK、广告、统计和系统推送根域名。

## 更新脚本与 GitHub Actions

`scripts/update_bing_quantumultx.py` 检查三个公开上游，拒绝 HTML、空文件与异常数量下降，只从人工批准数据生成正式规则。支持 `--check`、`--dry-run` 和 `--verbose`。

`.github/workflows/update-bing-quantumultx.yml` 每周独立测试、更新和验证 Bing 文件，只在真实变化时提交。

## 隐私与合规

本项目不预设、记录或推荐用户使用的节点国家、代理服务商或订阅来源。本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅地址或账户资料。

规则只改变网络出口，不改变 Microsoft 账户地区、服务资格、身份或合规要求，不得用于规避地区限制、身份验证、风控或平台安全机制。
