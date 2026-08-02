# Wirex One Quantumult X Rules

## 规则用途与目标 App

这是一份面向 Wirex One 的独立 Quantumult X 域名分流资源，重点覆盖公开证据能够确认的 Wirex 第一方核心服务和 Wirex One 专用帮助入口，同时尽量降低对其他 App 的误匹配。

- 显示名称：Wirex One
- iOS App Store ID：`6762381032`
- iOS Bundle ID：`com.wirexapp.one`
- Android 包名：`com.wirexapp.one`
- 开发者：Wirex Limited / Wirex
- 主规则：[WirexOne.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/WirexOne/WirexOne.list)

规则第三列统一使用 `WirexOne`，它是规则文件内的策略占位名称。通过 Quantumult X 添加远程 Filter Resource 时，可以为该资源选择已有策略；具体行为以当前版本和配置为准。

## Wirex One 与 Classic Wirex

Wirex One 是新应用，Classic Wirex 是单独的旧版应用：

| 应用 | iOS 标识 | Android 包名 |
|---|---|---|
| Wirex One | App Store `6762381032`；Bundle ID `com.wirexapp.one` | `com.wirexapp.one` |
| Classic Wirex | App Store `1090004654`；Bundle ID `com.wirex` | `com.wirex` |

`wirexapp.com` 是 Wirex 自有的共享核心根域，同时承载 Wirex One、Classic Wirex、Wirex Business 和其他同品牌服务。本规则以 Wirex One 为目标，但该父域规则可能同时命中这些 Wirex 自有服务；这不表示项目完整支持 Classic Wirex，也不表示能够按 App 进程隔离。

`wirex.app.link` 等旧品牌深链没有足够证据证明是 Wirex One 核心运行依赖，因此仅记录为待复核候选，不进入主规则。未发现能够可靠归为 Classic Wirex 专用且需要加入 Wirex One 的独立根域。

## 覆盖范围与规则数量

当前主规则为 <!-- WIREXONE_MAIN_COUNTS_START -->2 条（HOST 1，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- WIREXONE_MAIN_COUNTS_END -->，更新时间为 <!-- WIREXONE_MAIN_UPDATED_START -->2026-08-02 00:24:14 UTC<!-- WIREXONE_MAIN_UPDATED_END -->。

| 正式规则 | 分类 | 依据与范围 |
|---|---|---|
| `HOST,wirexone.freshdesk.com,WirexOne` | support | Wirex 官网和状态页直接链接的 Wirex One 专用帮助中心租户；只加入精确主机，不加入共享 Freshdesk 根域。 |
| `HOST-SUFFIX,wirexapp.com,WirexOne` | wirex-shared-core | Wirex One 条款将其标识为官方 Web 根域，公开 Wirex One Web 应用也使用其第一方 API、配置、卡片和静态资源子域。 |

父域规则已覆盖以下经官方公开页面或 Wirex One 公开脚本确认的主机，因此不重复写入精确 HOST：

- `one.wirexapp.com`：Wirex One Web 入口
- `api-baas.wirexapp.com`：公开 Wirex One 脚本引用的 API
- `resourses.wirexapp.com`：公开脚本引用的远程配置主机；保留上游实际拼写
- `cdn.wirexapp.com`：第一方静态资源
- `wx-acquiring-card-manager.wirexapp.com`：第一方卡片管理服务
- `help.wirexapp.com`：官方帮助中心和迁移说明
- `status.wirexapp.com`：官方状态页
- `img.wirexapp.com`：官方帮助资源

覆盖目标包括 App 启动、公开远程配置、账户与安全入口、余额和资产界面、兑换、卡片、Cashback、银行转账、Earn、Borrow、自托管钱包界面、通知、帮助、状态和第一方静态资源。这里的“覆盖”仅指已确认的低误伤域名，不代表所有功能必然只访问这些主机。

## 可选规则

没有创建 `WirexOne-Web3.list` 或 `WirexOne-Regional.list`：

- 当前公开脚本中的 Privy、WalletConnect、公共 RPC、区块浏览器、桥接和支付服务均属于共享第三方，不能安全地整体绑定到 Wirex One。
- 官方资料说明功能和服务实体可能随司法辖区变化，但未发现独立、官方确认且必须由地区规则承载的根域。

## 数据来源

主要一手来源：

- [Wirex 官方网站](https://www.wirexapp.com/)
- [Wirex One Web](https://one.wirexapp.com/)
- [Wirex One Terms](https://www.wirexapp.com/legal/one/terms)
- [Wirex One Privacy](https://www.wirexapp.com/legal/one/privacy)
- [Wirex One 迁移 FAQ](https://help.wirexapp.com/article/wirex-one-upgrade-faq-1685)
- [Wirex 状态页](https://status.wirexapp.com/)
- [Wirex One 帮助中心](https://wirexone.freshdesk.com/support/solutions/76000005022)
- [Apple App Store](https://apps.apple.com/us/app/wirex-one/id6762381032)
- [Google Play](https://play.google.com/store/apps/details?id=com.wirexapp.one)

还检查了 v2fly/domain-list-community、MetaCubeX/meta-rules-dat 和 blackmatrix7/ios_rule_script 的当前默认分支。三者均没有 Wirex 专用业务规则；blackmatrix7 Privacy 中出现的 Wirex 邮件跟踪主机属于隐私过滤数据，不是 App 核心分流证据。其他综合规则仅作为交叉检查，不会自动进入正式规则。

未分析 APK。Google Play 是可信官方分发页，但本次没有找到可直接下载、校验包名并计算 SHA-256 的官方 APK 文件；项目没有采用第三方 APK 镜像。

## 域名确认方法

1. 优先检查 Wirex One 条款、隐私说明、官方帮助、状态页和应用商店身份。
2. 只读检查无需登录的 Wirex One Web HTML 和公开 JavaScript，提取去除 query 与 fragment 的主机名。
3. 将公开规则仓库、HTTP、DNS、TLS 与 CNAME 仅作为辅助，不能单独证明归属或必要性。
4. 对每个候选记录范围、状态、来源、证据和误匹配风险。
5. 只有 Wirex 自有核心根域或能够证明为 Wirex One 专用的精确租户主机才可进入人工批准文件。

审核记录位于：

- [wirexone_manual_domains.txt](../../../data/wirexone_manual_domains.txt)
- [wirexone_excluded_domains.txt](../../../data/wirexone_excluded_domains.txt)
- [wirexone_candidates.tsv](../../../data/wirexone_candidates.tsv)

## 第三方依赖与排除原则

本项目刻意避免收录公共 CDN、共享身份平台、KYC 平台、卡组织、银行、公共 RPC、广告、统计和系统推送根域名。

典型排除项包括：

| 类别 | 示例 | 原因 |
|---|---|---|
| 身份、KYC 与密钥管理 | `privy.io`、`sumsub.com` | 多客户共享平台，不能因 Wirex 集成而整体分流。 |
| 卡组织与支付 | `visa.com`、`mastercard.com`、`stripe.com`、`paypal.com` | 会影响大量无关支付和金融应用。 |
| Wallet 与公共链 | `walletconnect.com`、公共 RPC 与区块浏览器 | 公开脚本常含默认链注册表，字符串存在不等于实际请求，更不等于 Wirex 专用。 |
| CDN 与云平台 | `amazonaws.com`、`cloudfront.net`、`cloudflare.net`、`static.wixstatic.com` | 共享基础设施，不能按一次解析结果加入根域或 IP。 |
| App 商店与系统服务 | `apple.com`、`mzstatic.com`、`google.com`、`googleapis.com` | 会误匹配大量其他 App 和系统流量。 |
| 统计与跟踪 | `appsflyer.com`、`sentry.io`、Wirex 邮件跟踪子域 | 不是核心业务分流依据；Wirex 邮件子域可能因父级自有根域而被一并匹配，但不会作为独立规则增加。 |
| 未确认品牌相似域 | `wirex.com`、`wirexapp.tech`、`wirexpaychain.com` | 分别存在归属冲突、沙盒/合作伙伴用途或独立生态证据，不能证明为 Wirex One 核心。 |

不加入公共 CDN IP、动态云地址、大范围 IP-CIDR、ASN、`HOST-KEYWORD` 或公共第三方根域。

## Quantumult X 导入步骤

1. 打开 Quantumult X。
2. 进入 Filter Resources。
3. 添加远程资源。
4. 粘贴 `WirexOne.list` 的 [Raw 链接](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/WirexOne/WirexOne.list)。
5. 资源名称可以填写 `Wirex One`。
6. 根据自身网络环境和服务可用性，将该远程资源绑定到适当的现有策略组。
7. 启用该资源。
8. 将 Wirex One 专用规则放在更宽泛的规则及 Final 之前。
9. 更新所有资源。
10. 完全关闭并重新打开 Wirex One。
11. 在 Quantumult X 活动记录中确认 Wirex 自有域名命中预期策略。

推荐顺序是：Wirex One 专用规则、其他细分规则、宽泛 Proxy 规则、Final。无需修改现有 Final 策略。

## 验证与隐私安全的抓漏方法

本地维护者可运行：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_wirexone_rules.py
python3 tests/test_root_readme_app_order.py
```

抓漏时：

1. 更新 Filter Resources，清空或记录活动日志，并完全关闭后重新打开 Wirex One。
2. 只测试无需提交真实交易、付款或 KYC 的公开功能入口。
3. 找出未命中专用规则的可疑主机名，仅记录 hostname，并删除 query 和 fragment。
4. 隐藏账户、邮箱、手机号、Token、Cookie、钱包、卡片和银行资料；不要公开请求正文或认证标头。
5. 只补充能够确认属于 Wirex 的域名；公共 KYC、支付、银行卡、RPC、分析、广告和 CDN 不加入。
6. 检查其他 App 是否受到误匹配。

可用以下表格保存脱敏调查结果：

| 时间 | Wirex One 功能入口 | 请求主机名 | 当前命中策略 | 是否确认属于 Wirex | 公开来源 | 建议处理 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## 已知限制与误匹配风险

Quantumult X 常规分流按照请求的目标域名和 IP 匹配，并不是真正按照 iOS App 进程或 Bundle ID 匹配。

如果其他 App 访问相同域名，也可能命中 Wirex One 规则。

如果 Wirex One 使用尚未收录的新域名，请求可能进入其他策略。

`HOST-SUFFIX,wirexapp.com` 会匹配同一 Wirex 根域下的 Classic、Business、营销网站和其他第一方子域。这是以同品牌匹配范围换取移动后端变更耐受性的明确取舍。精确 Freshdesk 租户虽然误伤较低，但仍由第三方平台承载；若租户结构改变，需要重新审核。

不同地区、账户类型和网络环境的可用性可能不同。规则只改变请求的网络出口，不改变账户身份、居住地、服务资格、KYC 状态、银行卡资格或监管要求。

## 更新脚本与 GitHub Actions

[update_wirexone_quantumultx.py](../../../scripts/update_wirexone_quantumultx.py) 使用 Python 标准库审查无需登录的官方公开页面，并将观察结果与人工批准项分离。候选项不会自动进入正式规则。脚本支持：

```bash
python3 scripts/update_wirexone_quantumultx.py --check
python3 scripts/update_wirexone_quantumultx.py --dry-run
python3 scripts/update_wirexone_quantumultx.py --verbose
```

它设置超时和 User-Agent，拒绝 HTML 错误页、空响应、错误身份页面、外部重定向、异常数量下降，并采用原子写入。只有规则正文变化才更新时间；网络失败不会清空当前规则。

[update-wirexone-quantumultx.yml](../../../.github/workflows/update-wirexone-quantumultx.yml) 每周四 05:43 UTC 运行，也支持手动触发。工作流先测试、更新和验证，仅在批准的 Wirex One 生成文件或根索引确有变化时提交 `chore: update Wirex One QuantumultX rules`，不使用私人 Secret。

## 提交新域名

提交候选时只提供去参数化的主机名、功能入口、公开来源和归属理由。不要提交登录日志、账户信息、私人 URL、Cookie、Token、邮箱、手机号、卡片、银行、钱包或 KYC 数据。候选先进入 TSV 审核；只有证据充分且误匹配风险可接受时才进入人工批准文件。

## 隐私与合规

本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅地址或账户资料。

本项目不预设、记录或推荐用户使用的节点国家、代理服务商或订阅来源。

规则只改变请求的网络出口，不改变账户身份、居住地、服务资格、KYC 状态、银行卡资格或监管要求。不得使用本项目绕过地区限制、身份验证、风控、支付要求或平台安全机制。
