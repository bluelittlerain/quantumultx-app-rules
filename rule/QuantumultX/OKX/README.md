# OKX Quantumult X Rules

## 规则用途与目标服务

本目录维护 OKX 官方交易 App、网站与公开 API 的低误匹配 Quantumult X 规则。主规则覆盖启动、登录、账户、行情、订单簿、现货、杠杆、合约、期权、订单、公共与私有 WebSocket、资产、钱包、充值提现、Convert、Earn、公告和帮助。

Quantumult X 常规分流按照请求的目标域名和 IP 匹配，并不是真正按照 iOS App 进程或 Bundle ID 匹配。如果其他 App 请求相同域名，也可能命中该规则。如果 OKX 使用尚未收录的新域名，请求可能进入其他策略。

## 主规则与可选范围

- `OKX.list`：核心交易、账户、资产、REST、WebSocket 与专用连接调度域名。
- `OKX-Web3.list`：可选的 OKLink 与 X Layer 服务，不属于核心交易必需范围。

官方文档列出的 `openapi.okx.com`、`ws.okx.com`、`wspap.okx.com` 以及地区 API 子域均由 `okx.com` 父域覆盖。另建 Regional 文件会与主规则重复，因此本次未创建无实际增益的地区文件。

## 数据来源

1. [OKX 官方网站](https://www.okx.com/)
2. [OKX V5 API](https://www.okx.com/docs-v5/)
3. [v2fly/domain-list-community OKX](https://github.com/v2fly/domain-list-community/blob/master/data/okx)
4. [MetaCubeX OKX geosite](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/okx.yaml)
5. [blackmatrix7 OKX Quantumult X](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/QuantumultX/OKX)

## 域名确认标准

官方 API 文档优先。备用连接域名需要当前 v2fly 与 MetaCubeX 同时维护，并且根域具有明显 OKX 专用性。候选数据不会自动进入正式规则；共享 CDN CNAME 不被视为客户端请求域名。

## 当前更新时间与数量

- 主规则：<!-- OKX_MAIN_COUNTS_START -->7 条（HOST 0，HOST-SUFFIX 7，IP-CIDR 0，IP6-CIDR 0）<!-- OKX_MAIN_COUNTS_END -->；<!-- OKX_MAIN_UPDATED_START -->2026-07-29 04:58:21 UTC<!-- OKX_MAIN_UPDATED_END -->
- Web3：<!-- OKX_WEB3_COUNTS_START -->2 条（HOST 0，HOST-SUFFIX 2，IP-CIDR 0，IP6-CIDR 0）<!-- OKX_WEB3_COUNTS_END -->；<!-- OKX_WEB3_UPDATED_START -->2026-07-29 04:58:21 UTC<!-- OKX_WEB3_UPDATED_END -->

## 已确认域名摘要

主规则包含 `okx.com`、`okex.com`、`okx-dns.com`、`okx-dns1.com`、`okx-dns2.com`、`okx.ac` 与 `okx.cab`。前三个 DNS 根域由当前两个活跃上游共同维护，名称和范围均为 OKX 专用，作为 App 连接与备用调度域名保留。

`oklink.com` 和 `xlayer.tech` 与 OKX Web3 生态有关，但不是核心交易必需域名，仅进入可选文件。

## 候选和排除说明

`okx.com.cdn.cloudflare.net` 是共享 Cloudflare CNAME 目标。Quantumult X 通常匹配客户端原始请求主机名，未发现客户端直接请求该目标的充分证据，因此排除。不会加入整个 `cloudflare.net`、公共 CDN IP 或 ASN。

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
10. 完全关闭并重新打开 OKX。
11. 在 Quantumult X 活动记录中确认目标域名命中预期策略。

## Raw 链接

- [OKX.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/OKX/OKX.list)
- [OKX-Web3.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/OKX/OKX-Web3.list)

## 规则优先级

把 OKX 主规则放在 Cryptocurrency、Proxy 和 Final 等宽泛规则之前。Web3 文件应按功能需要单独导入。

## 验证方法

```bash
python3 -m unittest discover -s tests -p "test_okx_rules.py" -v
python3 scripts/update_okx_quantumultx.py --check
python3 scripts/validate_okx_rules.py
```

## 抓漏域名方法

更新资源并清理活动记录后，重新启动 App，测试登录、行情、K 线、订单簿、交易、WebSocket、资产、钱包、充值提现和帮助。只记录去除 query 与 fragment 的域名，不记录凭据、订单或账户信息。

| App 功能 | 请求域名 | 当前策略 | 所属机构 | 是否专用 | 证据 | 建议 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## 已知限制与误匹配风险

`HOST-SUFFIX,okx.com` 会同时覆盖官方地区子域；规则无法区分账户类型或服务资格。备用根域用途可能变化，未收录的新域名也可能落入其他策略。

本项目刻意避免收录公共 CDN、共享 SDK、广告、统计和系统推送根域名。

## 更新脚本与 GitHub Actions

`scripts/update_okx_quantumultx.py` 实时检查 OKX 三个公开上游，但正式输出只来自人工批准数据。脚本支持 `--check`、`--dry-run` 和 `--verbose`，并具有超时、HTML/空响应拒绝、数量下降保护与原子写入。

`.github/workflows/update-okx-quantumultx.yml` 独立测试、更新和验证 OKX 文件，只在真实变化时提交。

## 隐私与合规

本项目不预设、记录或推荐用户使用的节点国家、代理服务商或订阅来源。本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅地址或账户资料。

规则只改变网络出口，不改变账户地区、KYC、服务资格、风控判断或合规要求，不得用于规避地区限制、身份验证或平台安全机制。
