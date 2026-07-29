# Binance Quantumult X Rules

## 规则用途与目标服务

本目录维护 Binance 官方 App、网站与公开交易接口的低误匹配 Quantumult X 规则。主规则覆盖核心交易、行情、账户、资产、钱包、充值提现、公告、帮助、REST API、WebSocket、公开市场数据和经确认的 App 专用后端。

Quantumult X 常规分流按照请求的目标域名和 IP 匹配，并不是真正按照 iOS App 进程或 Bundle ID 匹配。如果其他 App 请求相同域名，也可能命中该规则。如果 Binance 使用尚未收录的新域名，请求可能进入其他策略。

## 主规则与可选范围

- `Binance.list`：全球版核心 App、网站、API、WebSocket、专用静态资源和低误伤备用连接域名。
- `Binance-Ecosystem.list`：可选的 BNB Chain、Binance Charity、旧生态入口与 Binance NFT 静态资源，不属于核心交易必需范围。
- `Binance-Regional.list`：可选的 Binance.US 独立地区服务，不与全球版主规则合并。

三个文件应按实际服务范围分别导入。导入主规则不代表需要导入所有可选文件。

## 数据来源

1. [Binance 官方网站](https://www.binance.com/)
2. [Binance Spot REST API](https://developers.binance.com/en/docs/products/spot/rest-api)
3. [Binance Spot WebSocket Streams](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-streams/~)
4. [v2fly/domain-list-community Binance](https://github.com/v2fly/domain-list-community/blob/master/data/binance)
5. [MetaCubeX Binance geosite](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/binance.yaml)
6. [blackmatrix7 Binance Quantumult X](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/QuantumultX/Binance)

官方文档当前列出 `api.binance.com`、`api-gcp.binance.com`、`api1` 至 `api4.binance.com`、`stream.binance.com` 和 `data-api.binance.vision`；这些主机分别被 `binance.com` 或 `binance.vision` 父域规则覆盖，无需重复精确 HOST。

## 域名确认标准

正式规则只能来自官方公开资料，或由当前活跃上游共同支持且具有 Binance 专用、低共享风险特征的域名。上游新增项只进入候选审查，不会自动进入正式规则。DNS、TLS、CNAME 或相同 IP 只能作为辅助证据。

## 当前更新时间与数量

- 主规则：<!-- BINANCE_MAIN_COUNTS_START -->13 条（HOST 2，HOST-SUFFIX 11，IP-CIDR 0，IP6-CIDR 0）<!-- BINANCE_MAIN_COUNTS_END -->；<!-- BINANCE_MAIN_UPDATED_START -->2026-07-29 04:58:19 UTC<!-- BINANCE_MAIN_UPDATED_END -->
- Ecosystem：<!-- BINANCE_ECOSYSTEM_COUNTS_START -->4 条（HOST 0，HOST-SUFFIX 4，IP-CIDR 0，IP6-CIDR 0）<!-- BINANCE_ECOSYSTEM_COUNTS_END -->；<!-- BINANCE_ECOSYSTEM_UPDATED_START -->2026-07-29 04:58:19 UTC<!-- BINANCE_ECOSYSTEM_UPDATED_END -->
- Regional：<!-- BINANCE_REGIONAL_COUNTS_START -->1 条（HOST 0，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- BINANCE_REGIONAL_COUNTS_END -->；<!-- BINANCE_REGIONAL_UPDATED_START -->2026-07-29 04:58:19 UTC<!-- BINANCE_REGIONAL_UPDATED_END -->

## 已确认域名摘要

主规则包含 `binance.com`、`binance.cloud`、`binance.me`、`binance.vision`、`binanceapi.com`、`binancecnt.com`、`bnbstatic.com`、`bntrace.com`、`bsappapi.com`、`bsappapi.cc` 与 `bscdnweb.com`。

AppsFlyer 只收录当前 v2fly 与 MetaCubeX 同时维护的两个 Binance 专用精确主机。不会整体加入 `appsflyer.com` 或 `appsflyersdk.com`。

## 候选、历史与排除说明

`data/binance_candidates.tsv` 记录当前上游候选及证据等级。`binancezh.*`、`bnappzh.co`、`bnbzh.ac` 等入口缺少充分的当前官方证据，标记为 historical；`appsflayer.com` 疑似历史拼写异常，明确排除。

`saasexch.*` 可能属于交换平台 SaaS 基础设施，不能证明仅由 Binance 使用；`bmwweb.solutions` 与 `bnappweb.black` 也因证据不足未进入正式规则。公共 CDN、云平台、分析 SDK 和公共 IP 均不收录。

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
10. 完全关闭并重新打开 Binance。
11. 在 Quantumult X 活动记录中确认目标域名命中预期策略。

## Raw 链接

- [Binance.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Binance/Binance.list)
- [Binance-Ecosystem.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Binance/Binance-Ecosystem.list)
- [Binance-Regional.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Binance/Binance-Regional.list)

## 规则优先级

把 Binance 专用资源放在 Cryptocurrency、Proxy 和 Final 等更宽泛规则之前。可选资源可以紧随主规则，但不应替代主规则。

## 验证方法

```bash
python3 -m unittest discover -s tests -p "test_binance_rules.py" -v
python3 scripts/update_binance_quantumultx.py --check
python3 scripts/validate_binance_rules.py
```

## 抓漏域名方法

更新资源并清理活动记录后，重新启动 App，依次测试启动、登录、行情、K 线、订单簿、现货、杠杆、合约、期权、订单、资产、钱包、充值、提现、Convert、Earn、公告和帮助。只记录域名，删除 query 与 fragment，并隐藏 Token、Cookie、账号和订单信息。

| App 功能 | 请求域名 | 当前策略 | 所属机构 | 是否专用 | 证据 | 建议 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

公共 CDN、登录平台、广告和分析域名不要加入；同时检查其他 App 是否受到误匹配。

## 已知限制与误匹配风险

域名规则不能保证识别发起请求的 App。备用根域用途可能变化，精确归因主机也可能被浏览器访问。加密 DNS、连接复用、缓存和新域名会影响日志可见性与覆盖率。

本项目刻意避免收录公共 CDN、共享 SDK、广告、统计和系统推送根域名。

## 更新脚本与 GitHub Actions

`scripts/update_binance_quantumultx.py` 下载三个当前公开上游，验证响应与数量，只用人工批准文件生成正式规则。支持 `--check`、`--dry-run` 和 `--verbose`；网络失败、HTML、空响应或数量异常时不会覆盖文件。

`.github/workflows/update-binance-quantumultx.yml` 每周运行，也支持手动触发。测试、更新和验证全部成功且文件真实变化时才提交。

## 隐私与合规

本项目不预设、记录或推荐用户使用的节点国家、代理服务商或订阅来源。本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅地址或账户资料。

规则只改变请求的网络出口，不改变账户地区、KYC、身份、服务资格、风控判断或合规要求，不得用于规避地区限制、身份验证、平台安全机制或适用规则。
