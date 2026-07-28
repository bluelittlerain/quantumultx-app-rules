# Club Sim Quantumult X Rules

## 项目用途与目标 App

本目录维护 Club Sim 储值卡 App 的低误匹配 Quantumult X 域名规则，目标为：

- iOS App Store ID：`1286595675`
- Android 包名：`com.pccw.clubsim`
- 官方开发者：CSL Mobile Limited

主规则覆盖官方同源的启动、登录、账户、余额、用量、SIM/eSIM 管理、套餐、增值、订单、活动和支持入口。Quantumult X 常规分流按照请求的目标域名和 IP 匹配，并不是真正按照 iOS App 进程、Bundle ID 或 Android 包名匹配。

Club Sim 月费服务使用独立 App（公开商店资料显示 Android 包名为 `com.hkt.clubsim.postpaid`）。目前没有足够证据证明存在应独立收录的月费 App 专用域名，因此未创建 `ClubSim-Monthly.list`，也不声称主规则完整支持月费 App。

## 规则文件与数量

- 主 App 规则：<!-- CLUBSIM_MAIN_COUNTS_START -->2 条（HOST 1，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- CLUBSIM_MAIN_COUNTS_END -->
- 可选网络规则：<!-- CLUBSIM_NETWORK_COUNTS_START -->5 条（HOST 5，HOST-SUFFIX 0，IP-CIDR 0，IP6-CIDR 0）<!-- CLUBSIM_NETWORK_COUNTS_END -->
- 主规则更新时间：<!-- CLUBSIM_MAIN_UPDATED_START -->2026-07-28 14:36:07 UTC<!-- CLUBSIM_MAIN_UPDATED_END -->
- Network 更新时间：<!-- CLUBSIM_NETWORK_UPDATED_START -->2026-07-28 14:36:07 UTC<!-- CLUBSIM_NETWORK_UPDATED_END -->

Raw 链接：

- [ClubSim.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/ClubSim/ClubSim.list)
- [ClubSim-Network.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/ClubSim/ClubSim-Network.list)

## 已确认的主规则域名

| 规则 | 主要证据 | 用途与风险判断 |
|---|---|---|
| `HOST-SUFFIX,clubsim.com.hk,ClubSim` | [官方站点](https://www.clubsim.com.hk/)、登录、支持与购买页面；官方脚本将业务请求配置为同源 `/api`、`/ecommfe` 与 `/clsmw` 路径 | Club Sim 自有根域，覆盖账户、套餐、增值、订单和公开 WebView；低误匹配 |
| `HOST,clubsim.page.link,ClubSim` | 当前官方公开脚本中的 Club Sim 专用动态链接 | 只收录专用精确主机，不收录共享的 `page.link` 根域 |

`HOST-SUFFIX,clubsim.com.hk` 已覆盖 `www.clubsim.com.hk` 以及同根 API，因此不重复添加精确 HOST。候选项必须有官方来源或多项可靠证据，并经过人工批准后才能进入 [clubsim_manual_domains.txt](../../../data/clubsim_manual_domains.txt)。

## 可选 Network 规则

`ClubSim-Network.list` 将现有公开 ClubSim 网络规则中的 5 个精确主机与 App 业务规则分开：

- `csl.prod.ondemandconnectivity.com`
- `hhk.prod.ondemandconnectivity.com`
- `epdg.epc.mnc000.mcc454.pub.3gppnetwork.org`
- `ss.epdg.epc.geo.mnc000.mcc454.pub.3gppnetwork.org`
- `ss.epdg.epc.mnc000.mcc454.pub.3gppnetwork.org`

这些域名主要涉及 eSIM Profile Provisioning、GSMA On-Demand Connectivity、ePDG、Wi-Fi Calling 或运营商网络服务；它们不等同于 App 登录、增值和套餐购买。iOS 系统的 Wi-Fi Calling 或 IPsec 流量不一定能由普通应用层代理完整接管。Network 文件是可选资源，应根据实际需要独立导入。

## 数据来源与确认方法

优先使用不需要登录的公开资料：

1. [Club Sim 官方网站](https://www.clubsim.com.hk/)、[登录页面](https://www.clubsim.com.hk/en/login)、[支持中心](https://www.clubsim.com.hk/en/support)和公开购买页面。
2. 官方页面直接加载的 JavaScript、静态资源、同源 API 路径和 App 链接。
3. [iOS App Store](https://apps.apple.com/hk/app/id1286595675)与 [Google Play](https://play.google.com/store/apps/details?id=com.pccw.clubsim)公开资料。
4. 官方网站公开的 APK 下载入口；APK 只允许静态检查，不执行、不登录、不绕过代码保护。
5. [ClearLuv 当前 ClubSim 网络规则](https://raw.githubusercontent.com/ClearLuv/iOS_collecton/main/Rule/ClubSim.list)，只作为 Network 候选来源。
6. DNS、TLS 和证书资料只能作为辅助证据，不能单独证明归属。

域名发现结果保存在 [clubsim_candidates.tsv](../../../data/clubsim_candidates.tsv)。发现脚本会移除 URL 的 query 和 fragment，并把共享平台或证据不足的域名标记为 excluded 或 needs-review；候选数据不会自动进入正式规则。

官方站点当前提供公开 APK 入口，下载文件名标示版本 `2.3.9`、版本代码 `200167`。仓库不保存 APK；定时工作流使用 `--no-apk`，避免每周下载大型二进制文件。只有完整下载、验证包名 `com.pccw.clubsim` 并完成静态检查后得到的候选，才可进入人工复核流程。

## 被排除的共享服务

项目不会为了表面上的“全覆盖”加入以下类别：

- Apple、Google、Facebook、The Club 等共享身份平台；
- WhatsApp、YouTube、Instagram 等共享通信或内容平台；
- 公共 CDN、云平台、分析、广告、崩溃报告和系统推送根域；
- Mastercard、Visa、PayPal、Stripe、Tap & Go 等公共支付或金融平台；
- `hkt.com`、`pccw.com`、`hkcsl.com`、`theclub.com.hk` 等大型集团或共享根域。

官方脚本中的 `rnr.hkcsl.com/clubsim` 和 `sdeweb.hkcsl.com/cs/...` 只在路径层面体现 Club Sim 用途，而 Quantumult X 只能匹配主机，因此未把这些共享主机加入主规则。社交登录、客服、分析和付款仍可由现有更宽泛策略处理。完整理由见 [clubsim_excluded_domains.txt](../../../data/clubsim_excluded_domains.txt)。

## Quantumult X 导入步骤

1. 打开 Quantumult X。
2. 进入 Filter Resources。
3. 添加远程资源。
4. 粘贴 `ClubSim.list` 的 Raw 链接。
5. 资源名称可以填写 `ClubSim`。
6. 根据自身网络环境和服务可用性，将该远程资源绑定到适当的现有策略组。
7. 启用该资源。
8. 将 ClubSim 专用规则放在 Proxy、Final 等更宽泛规则之前。
9. 更新所有资源并完全关闭、重新打开 Club Sim App。
10. 在活动记录中确认 Club Sim 自有请求命中预期策略。

如确实需要网络相关规则，可另外导入 `ClubSim-Network.list`。Network 规则不等同于 App 业务规则，用户应根据实际需求决定是否导入。

建议的通用顺序：

```text
ClubSim
其他细分规则
Proxy
Final
```

不需要修改现有 Final 策略。规则第三列的 `ClubSim` 是文件内占位名称；为远程 Filter Resource 选择现有策略时，具体行为以当前 Quantumult X 版本和配置为准。

## 验证与抓漏

1. 更新 Quantumult X 的全部资源并清理或记录当前活动日志。
2. 完全关闭并重新打开 Club Sim。
3. 依次检查登录、账户首页、余额、用量、SIM 管理、eSIM、本地套餐、漫游套餐、增值、订单、活动和支持中心。
4. 找出没有命中 ClubSim 规则的可疑域名，只记录主机名，不记录完整 URL 查询参数。
5. 隐藏手机号、Token、Cookie、Session、订单号、付款资料和账户资料。
6. 只补充能够确认由 Club Sim 专用或主要使用的域名；公共登录、支付、分析、广告、推送和 CDN 域名不要加入。
7. 检查其他 App 是否因候选范围扩大而发生误匹配。

| App 功能 | 请求域名 | 当前策略 | 所属机构 | 是否 Club Sim 专用 | 证据 | 建议 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

提交候选时只提供去参数化域名、功能页面和公开证据，不提交账户、号码、Cookie、Token、付款或实名资料。

## 已知限制与误匹配风险

- 如果其他 App 访问相同域名，也可能命中 ClubSim 规则。
- 如果 Club Sim 使用尚未收录的新域名，请求可能进入其他策略。
- 共享身份、付款和集团主机无法按 URL 路径细分；为降低误匹配，它们被有意排除。
- 未使用账户、验证码、付款或实名流程进行调研，因此无法声称覆盖所有登录后接口。
- App 可能随版本更新切换域名；公开网页与官方 APK 的发布时间也可能不同。
- Network 文件不能保证接管系统级 Wi-Fi Calling、IMS、ePDG 或 IPsec 流量。

## 更新、验证与自动维护

公开页面发现：

```bash
python3 scripts/discover_clubsim_domains.py --check --no-apk --verbose
python3 scripts/discover_clubsim_domains.py --output data/clubsim_candidates.tsv --no-apk
```

省略 `--no-apk` 时，脚本会尝试从官方 Club Sim 域名下载公开 APK，计算 SHA-256、验证包名标记并静态提取候选域名。APK 和临时文件不会写入仓库。

规则生成：

```bash
python3 scripts/update_clubsim_quantumultx.py --check
python3 scripts/update_clubsim_quantumultx.py --dry-run --verbose
python3 scripts/update_clubsim_quantumultx.py --verbose
```

验证：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_clubsim_rules.py
python3 scripts/validate_bybit_rules.py
```

更新脚本只读取已批准的 manual/network 数据，并以当前公开 Network 上游进行安全核对。空响应、HTML 错误页、网络异常或异常数量下降都会失败且不会清空现有规则；规则正文不变时保留 `UPDATED` 时间。

[GitHub Actions 工作流](../../../.github/workflows/update-clubsim-quantumultx.yml)每周使用 UTC 定时，也支持手动运行。它依次运行完整单元测试、发现检查、规则生成、ClubSim 验证和现有 Bybit 验证，只在生成文件真实变化时提交 `chore: update ClubSim QuantumultX rules`。

## 隐私与合规

本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅地址或账户资料，也不记录维护者的个人网络配置。不同服务状态和网络环境的可用性可能不同。

规则只改变请求的网络出口，不改变账户身份、服务资格、SIM 卡注册状态、付款资格或运营商合规要求。不得使用本项目规避登录认证、验证码、TLS 校验、证书固定、付款验证、实名登记、KYC、地区限制、风控或其他平台安全机制。
