# Kraken Pro Quantumult X Rules

## 用途与支持范围

本目录维护 Kraken Pro 官方 App、网站和交易服务的低误匹配 Quantumult X 域名规则。主规则覆盖 App 启动、登录、账户、余额、资产、行情、K 线、订单簿、下单与撤单、充值提现、Staking、官方帮助、官方静态资源、Spot REST、公开与私有 WebSocket，以及 Kraken Pro 内的 Futures 功能。

Quantumult X 常规分流根据目标域名和 IP 匹配，不是真正按照 iOS App Bundle ID 匹配，也不按 Android 包名或进程识别应用。如果其他 App 请求相同域名，也可能命中该规则；如果 Kraken Pro 新增尚未收录的根域，请求可能进入其他策略。

## 规则范围

- `KrakenPro.list`：Kraken Pro 核心交易、账户、资产、API、WebSocket、Futures、帮助与第一方静态资源。
- 未创建 `KrakenPro-Web3.list`：Kraken Wallet 是官方明确区分的独立 App；链上 RPC、WalletConnect、区块浏览器和 dApp 多为共享服务，不适合并入 Kraken Pro 规则。
- 未创建 `KrakenPro-Regional.list`：本次没有确认到 Kraken Pro 全球主流程之外、需要独立根域处理的地区服务。

## 数据来源与判断方法

1. [Kraken 官方网站](https://www.kraken.com/)
2. [Kraken Developers](https://docs.kraken.com/)
3. [Kraken 支持中心](https://support.kraken.com/)
4. [Kraken 官方移动 App 列表](https://support.kraken.com/articles/360001332083-kraken-s-official-mobile-apps)
5. [Kraken Pro App 说明](https://support.kraken.com/articles/360049788312-kraken-pro-mobile-app-frequently-asked-questions-)
6. [Kraken WebSocket FAQ](https://support.kraken.com/articles/360022326871-kraken-websocket-api-frequently-asked-questions)
7. [Kraken Pro App Store](https://apps.apple.com/us/app/kraken-pro-advanced-trading/id1473024338)
8. [Kraken Pro Google Play](https://play.google.com/store/apps/details?id=com.kraken.trade)
9. [v2fly Kraken 数据](https://github.com/v2fly/domain-list-community/blob/master/data/kraken)
10. [MetaCubeX Kraken geosite](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/kraken.yaml)
11. [blackmatrix7 Cryptocurrency Quantumult X](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/QuantumultX/Cryptocurrency)

blackmatrix7 当前没有独立的 Kraken 或 KrakenPro Quantumult X 目录，其综合 Cryptocurrency 规则仅以 `kraken.com` 覆盖 Kraken。v2fly 与 MetaCubeX 当前 Kraken 分类均包含 `kraken.com` 和 `kraken.onl`。正式规则不会直接复制上游；候选项必须通过官方资料、多个活跃上游或明确的第一方专用证据审查。

DNS、TLS、CNAME、HTTP 可达性或相同 IP 只作为辅助证据。Cloudflare、AWS、Akamai 等基础设施归属不能证明其根域属于 Kraken。

## 当前更新时间与数量

- 主规则：<!-- KRAKENPRO_MAIN_COUNTS_START -->3 条（HOST 0，HOST-SUFFIX 3，IP-CIDR 0，IP6-CIDR 0）<!-- KRAKENPRO_MAIN_COUNTS_END -->；<!-- KRAKENPRO_MAIN_UPDATED_START -->2026-07-31 15:48:14 UTC<!-- KRAKENPRO_MAIN_UPDATED_END -->

## 已确认域名摘要

- `kraken.com`：官方主域，父域规则覆盖 `api.kraken.com`、`id.kraken.com`、`pro.kraken.com`、`futures.kraken.com`、`ws.kraken.com`、`ws-auth.kraken.com`、`ws-l3.kraken.com`、`assets.kraken.com`、`docs.kraken.com`、`status.kraken.com` 和 `support.kraken.com` 等已确认服务。
- `kraken.onl`：v2fly 与 MetaCubeX 当前共同维护的 Kraken 专用深链根域。
- `krakenpro.onl`：Kraken 官方移动 App 页面当前使用的 Kraken Pro 深链根域。

已被 `HOST-SUFFIX,kraken.com,KrakenPro` 覆盖的精确主机不会重复写入正式规则。

## 可选生态与地区说明

Kraken Wallet、Krak、Ink、xStocks 和 Breakout 是可独立识别的产品或生态范围，并非 Kraken Pro 核心交易规则的必要根域。本项目当前不发布 Web3 或地区附加文件；将来只有在确认独立第一方根域、真实客户端用途和低共享风险后才会新增。

不同地区、账户类型和网络环境的功能可用性可能不同。是否提供 Futures、Margin、Staking、股票或其他产品由 Kraken 的服务资格与适用要求决定，而不是由分流规则决定。

## 排除项与共享服务风险

`data/krakenpro_excluded_domains.txt` 明确排除公共 CDN、云平台、系统服务、统计与支持平台，包括 Cloudflare、CloudFront、AWS、Akamai、Google、Apple、AppsFlyer、Sentry、Zendesk 和 WalletConnect 根域。即使 Kraken 使用这些服务，也不能把共享根域整体绑定到 Kraken Pro。

`kraken.io` 是无关的图像优化服务，`kraken.tech` 是无关的能源技术平台，`kraken.pro` 缺少 Kraken 官方确认，`kraken.zone` 缺少当前直接证据；这些名称不会因包含品牌词而自动加入。`krak.app`、`inkonchain.com`、`xstocks.fi` 与 `breakoutprop.com` 也不属于本规则的核心范围。

不收录 DNS 查询得到的 CDN IP、公共 ASN 或大范围 IP-CIDR。CNAME 指向 CDN 并不意味着客户端直接请求该 CNAME 目标。

## Quantumult X 导入方式

1. 打开 Quantumult X。
2. 进入 Filter Resources。
3. 添加远程资源。
4. 粘贴 `KrakenPro.list` 的 Raw 链接。
5. 为资源设置名称，例如 `Kraken Pro`。
6. 根据自身网络环境和服务可用性，将远程资源绑定到适当的现有策略组。
7. 启用该资源。
8. 将 Kraken Pro 规则放在 Cryptocurrency、Proxy、Final 等更宽泛规则之前。
9. 更新资源并完全关闭、重新启动 Kraken Pro。
10. 在活动记录中确认请求命中预期策略。

规则第三列中的 `KrakenPro` 是规则文件内的通用策略占位名称。通过 Quantumult X 添加远程 Filter Resource 时，可以为该资源选择已有策略；具体行为以当前 Quantumult X 版本和配置为准。

## Raw 链接

- [KrakenPro.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/KrakenPro/KrakenPro.list)

## 规则优先级

推荐顺序为 Kraken Pro 专用规则、Cryptocurrency 综合规则、其他细分规则、Proxy、Final。不要为导入本项目而改变已有 Final 策略。

## 验证方法

```bash
python3 -m unittest discover -s tests -p "test_krakenpro_rules.py" -v
python3 scripts/update_krakenpro_quantumultx.py --check
python3 scripts/validate_krakenpro_rules.py
```

`--check` 仅检查是否需要更新，存在差异时返回非零；`--dry-run` 打印差异而不写文件；`--verbose` 输出上游与统计详情。

## 抓漏域名方法

更新全部资源并清理活动记录后，完全关闭 Kraken Pro，再依次测试启动、登录、账户、行情、K 线、订单簿、现货、Futures、下单、撤单、余额、资产、充值、提现、Staking、公告与客服，并观察公开和私有 WebSocket 是否持续连接。

| 时间 | Kraken Pro 功能 | 请求域名/IP | 当前策略 | 是否确认属于 Kraken | 来源 | 建议处理 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

只记录主机名，移除路径、query 和 fragment，不提交认证凭据、账户资料、订单详情或其他敏感内容。对落入其他策略的可疑域名，必须先找到官方页面或多个可靠公开来源；不要补充公共 CDN、广告、统计、系统推送、共享 SDK、公共 RPC 或区块浏览器根域。最后检查浏览器和其他 App 没有因规则扩大而被误分流。

## 已知限制与误匹配风险

域名规则不能识别请求来自哪个 App。浏览器或其他 App 访问 Kraken 官方域名时也会命中；新域名、加密 DNS、连接复用和缓存可能使活动日志不完整。3 个父域规则在低误匹配与核心覆盖之间取平衡，但不能保证覆盖未来尚未公开的新根域。

## 更新脚本与 GitHub Actions

`scripts/update_krakenpro_quantumultx.py` 获取两个 Kraken 专用公开上游，验证网络响应、内容类型和数量，再以人工批准文件生成正式规则。上游新增域名只进入审查流程，不会自动进入正式规则；网络失败、HTML、空响应或数量异常下降时不会覆盖现有文件。写入采用原子替换，只有规则正文变化才更新时间。

`.github/workflows/update-krakenpro-quantumultx.yml` 每周以 UTC 定时运行，也支持手动触发。只有 Kraken Pro 测试、更新与验证全部成功且生成文件真实变化时才提交，并且工作流只暂存 Kraken Pro 生成文件和根 README 的统计标记。

## 如何提交新域名

提交 Issue 或 Pull Request 时请提供域名、触发的 Kraken Pro 功能、可公开访问的官方证据或多个活跃上游，以及共享服务风险判断。不要提交完整 URL 的查询参数、活动日志原文、账户信息、认证资料或钱包信息。候选项先写入 `data/krakenpro_candidates.tsv`；确认后再进入 `data/krakenpro_manual_domains.txt`。

## 隐私、安全与合规

本项目不收集或记录个人网络配置、资源地址或账户资料，也不推荐特定网络出口。文档中的策略名称均为通用示例。

规则只改变请求的网络出口，不改变账户实名地区、KYC、居住地、服务资格、产品可用性、风控判断或平台合规要求，不得用于规避地区限制、身份验证、风控或安全机制。
