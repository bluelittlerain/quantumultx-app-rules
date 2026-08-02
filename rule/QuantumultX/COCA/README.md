# COCA Quantumult X Rules

## 规则用途与目标 App

本目录为 **COCA: Crypto Card & Wallet** 提供独立、低误匹配的 Quantumult X 域名规则。目标身份如下：

| 项目 | 当前公开信息 |
|---|---|
| 显示名称 | COCA |
| iOS App Store ID | `1594165139` |
| iOS Bundle ID | `com.wirex.wallet` |
| Android 包名 | `com.wirex.wallet` |
| 开发者 | CCA LABS / CCA LABS - FZCO |
| 官方网站 | [coca.xyz](https://www.coca.xyz/) |

主规则：[COCA.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/COCA/COCA.list)（<!-- COCA_MAIN_COUNTS_START -->2 条（HOST 1，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- COCA_MAIN_COUNTS_END -->）

当前更新时间：<!-- COCA_MAIN_UPDATED_START -->2026-08-02 03:04:04 UTC<!-- COCA_MAIN_UPDATED_END -->。

## 产品边界

COCA 与 Coca-Cola 饮料品牌、会员应用、商城以及其他同名产品无关。`coca-cola.com`、`coca-colacompany.com` 和无关的 `coca.com` 不会进入本规则。

COCA 的 Android 包名保留了 `wirex` 字样，官方资料也说明卡片服务与 Wirex 存在合作关系；这并不表示 COCA、Wirex One 与 Classic Wirex 是同一应用。COCA 使用本目录，Wirex One 继续使用独立的 [Wirex One 规则](../WirexOne/README.md)。`wirexapp.com` 属于多产品和合作方共享基础设施，不能整体分给 COCA。

## 主规则覆盖范围

- `HOST-SUFFIX,coca.xyz,COCA`：COCA 第一方根域，覆盖官网、文档、帮助中心、状态页以及同根下经官方维护的服务。
- `HOST,wwallet.app.link,COCA`：与 `com.wirex.wallet` 公开关联文件绑定的精确 Branch 深链租户；只收录精确主机，不收录共享的 `app.link` 根域。

`www.coca.xyz`、`docs.coca.xyz`、`help.coca.xyz`、`status.coca.xyz` 等已被父域覆盖，因此不重复输出。官方公开资料目前没有给出可安全确认的独立 API 或 WebSocket 根域；规则不会依据名称猜测 `api`、`auth` 或 `ws` 主机。

未发现需要单独维护的 COCA 专用 Web3 根域或官方地区根域，因此不创建 `COCA-Web3.list` 或 `COCA-Regional.list`。Privy、WalletConnect、公共 RPC、区块浏览器和 dApp 均保持在主规则之外。

## 数据来源与确认方法

主要证据来自：

- [COCA 官方网站](https://www.coca.xyz/)、[条款](https://www.coca.xyz/terms)、[隐私说明](https://www.coca.xyz/privacy)、[卡片页面](https://www.coca.xyz/cards)与[博客](https://www.coca.xyz/blog)
- [COCA 文档](https://docs.coca.xyz/)与[帮助中心](https://help.coca.xyz/)
- [COCA 状态页](https://status.coca.xyz/)及其公开服务状态
- [Apple App Store](https://apps.apple.com/us/app/coca-crypto-card-wallet/id1594165139)与[Google Play](https://play.google.com/store/apps/details?id=com.wirex.wallet)
- `coca.xyz` 的 [Apple App 关联文件](https://www.coca.xyz/.well-known/apple-app-site-association)与 [Android Asset Links](https://www.coca.xyz/.well-known/assetlinks.json)
- `wwallet.app.link` 的 [Apple App 关联文件](https://wwallet.app.link/apple-app-site-association)与 [Android Asset Links](https://wwallet.app.link/.well-known/assetlinks.json)
- [Wirex 与 COCA 的公开 BaaS 案例](https://www.wirexapp.com/post/from-wallet-to-full-onchain-banking-in-just-weeks-wirex-x-coca-case-study)；它用于确认合作边界，不用于把 Wirex 共享根域加入 COCA
- v2fly/domain-list-community、MetaCubeX/meta-rules-dat 与 blackmatrix7/ios_rule_script 的当前公开数据；调研时未发现可直接复用的 COCA 专用规则

域名采用“官方直接引用、公开 App 关联、低误伤”三项原则审查。DNS、TLS、CNAME 与公开搜索仅作辅助，不能单独证明归属。未找到 COCA 官方直接提供的 APK 下载，第三方镜像未被下载或作为正式证据，因此本次没有 APK 文件版本或 SHA-256 记录。

候选分类和证据记录在 [coca_candidates.tsv](../../../data/coca_candidates.tsv)，人工批准项位于 [coca_manual_domains.txt](../../../data/coca_manual_domains.txt)，排除理由位于 [coca_excluded_domains.txt](../../../data/coca_excluded_domains.txt)。候选项不会自动进入正式规则。

## 第三方依赖与排除原则

下列服务可能被官网、帮助、卡片或钱包功能提及，但它们是共享依赖，不会因此整体加入 COCA：

| 类别 | 处理方式 |
|---|---|
| Wirex BaaS、Wirex One、Classic Wirex | 共享或其他产品域名默认排除；只有可证明为 COCA 专用的精确主机才可评审 |
| Visa、Mastercard、银行与 KYC | 卡组织、金融机构和身份平台根域均为共享服务，排除 |
| Privy、WalletConnect、公共 RPC 与区块浏览器 | 可能被钱包功能使用，但会影响大量其他 App，排除 |
| Wix、GitBook、Freshworks、Atlassian、AWS、CloudFront | 共享网站、文档、客服、状态及云平台根域，排除 |
| Apple、Google、推送、分析、广告与崩溃报告 | 系统或跨应用共享服务，排除 |
| Coca-Cola 与其他同名站点 | 产品无关，排除 |

本项目不会加入公共 CDN IP、动态云 IP、大范围 IP-CIDR、ASN，也不会使用 `HOST-KEYWORD,coca,COCA`。精确第三方租户仍可能由服务商复用或调整，因此存在有限误匹配与失效风险。

## Quantumult X 导入

1. 打开 Quantumult X。
2. 进入 Filter Resources。
3. 添加远程资源。
4. 粘贴 `COCA.list` 的 [Raw 链接](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/COCA/COCA.list)。
5. 资源名称可以填写 `COCA`。
6. 根据自身网络环境和服务可用性，将该远程资源绑定到适当的现有策略组。
7. 启用该资源并更新全部资源。
8. 将 COCA 专用规则放在 Proxy、Final 等更宽泛规则之前。
9. 完全关闭并重新打开 COCA。
10. 在 Quantumult X 活动记录中确认 COCA 自有域名命中预期策略。

规则第三列中的 `COCA` 是规则文件内的通用策略占位名称。添加远程 Filter Resource 时可以为资源选择已有策略；具体行为以当前 Quantumult X 版本和配置为准。

## 验证与抓漏

公开仓库可运行：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/update_coca_quantumultx.py --check
python3 scripts/update_coca_quantumultx.py --dry-run
python3 scripts/validate_coca_rules.py
```

抓漏时先更新资源并清理活动记录，再重启 COCA，依次检查启动、登录入口、钱包、资产、转账、兑换、卡片、银行账户、奖励、帮助、状态与 Web3 入口。只记录不含查询参数和片段的主机名，并移除任何账户、Cookie、认证字段、钱包、卡片、银行或恢复资料。

| 时间 | COCA 功能页面 | 请求主机名 | 当前命中策略 | 是否确认属于 COCA | 公开来源 | 建议处理 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

可疑主机必须先区分 COCA 自有、COCA 专用租户、Wirex 共享、Wirex One、Classic Wirex、公共第三方或未知。不得为追求表面覆盖率加入公共 CDN、KYC、卡组织、银行、Privy、WalletConnect、RPC、广告、统计或系统推送根域，并应复查 Wirex One 及其他 App 是否出现误匹配。

## 更新与提交新域名

[update_coca_quantumultx.py](../../../scripts/update_coca_quantumultx.py) 读取公开官方页面作为健康观测，正式正文只由人工批准数据生成；网络失败、空结果、HTML 错误、低于安全下限或异常数量下降都会中止写入。写入采用原子替换，正文不变时保留原更新时间。`wwallet.app.link` 是人工批准的精确租户，维护时应定期复核其 Apple 与 Android 公开关联文件，再决定保留、变更或移除。

[GitHub Actions 工作流](../../../.github/workflows/update-coca-quantumultx.yml) 每周运行测试、更新和验证，仅在批准数据导致真实文件变化时提交。提交新域名时应提供不含私人参数的公开 URL、功能范围、归属证据、误匹配评估，以及为何不能由现有父域覆盖。

## 已知限制、隐私与合规

Quantumult X 常规分流按照请求的目标域名和 IP 匹配，并不是真正按照 iOS App 进程或 Bundle ID 匹配。

如果其他 App 访问相同域名，也可能命中 COCA 规则。

如果 COCA 使用尚未收录的新域名，请求可能进入其他策略。

本项目刻意避免收录公共 CDN、共享身份平台、KYC 平台、卡组织、银行、Wirex 共享后端、Privy、WalletConnect、公共 RPC、广告、统计和系统推送根域名。

本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅地址或账户资料。

本项目不预设、记录或推荐用户使用的节点国家、代理服务商或订阅来源。

本规则只表达公开证据支持的域名归属与分流范围，不构成对网站、App、交易或资产安全的背书；应用和链接仍应从官方渠道独立核实。

规则只改变请求的网络出口，不改变账户身份、居住地、服务资格、KYC 状态、钱包控制权、卡片资格或监管要求。不同地区、账户类型和网络环境的可用性可能不同；本项目不得用于规避地区限制、身份验证、风控、监管要求或平台安全机制。
