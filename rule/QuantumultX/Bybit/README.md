# Bybit Quantumult X 规则

## 1. 规则用途

本规则用于在 Quantumult X 的规则分流模式中匹配 Bybit 自有或主要由 Bybit 使用的业务域名。主规则当前为 <!-- BYBIT_COUNTS_START -->17 条（HOST 2，HOST-SUFFIX 15，IP-CIDR 0，IP6-CIDR 0）<!-- BYBIT_COUNTS_END -->，当前更新时间为 <!-- BYBIT_UPDATED_START -->2026-07-27 21:17:48 UTC<!-- BYBIT_UPDATED_END -->。

## 2. 支持范围

主规则覆盖主站、App/API、行情和交易、公共与私有 WebSocket、登录账户、资产钱包、充值提现、活动公告、帮助客服、静态图片、远程配置、Web3 与已维护的 Bybit 备用根域。根域 `bybit.com` 已自然覆盖 `api.bybit.com`、`stream.bybit.com`、`api-testnet.bybit.com`、`stream-testnet.bybit.com`、`www.bybit.com` 和 `testnet.bybit.com`，因此不重复写精确 HOST。

核实时，blackmatrix7 的 Cryptocurrency 综合规则仅以 `HOST-SUFFIX,bybit.com,Cryptocurrency` 覆盖 Bybit；本项目补充独立 API、客服、文档和备用根域，同时保持公共基础设施在规则之外。

## 3. 数据来源

- [Bybit V5 Integration Guidance](https://bybit-exchange.github.io/docs/v5/guide)
- [Bybit V5 WebSocket Connect](https://bybit-exchange.github.io/docs/v5/ws/connect)
- [Bybit 官方网站](https://www.bybit.com/)
- [MetaCubeX 当前 Bybit geosite](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/bybit.yaml)
- [v2fly domain-list-community 当前 Bybit 数据](https://github.com/v2fly/domain-list-community/blob/master/data/bybit)
- [Quantumult X 官方配置示例](https://github.com/crossutility/Quantumult-X)
- [blackmatrix7 Quantumult X 规则格式](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/QuantumultX)

更新器会依次探测 MetaCubeX 的 geosite/classical 候选路径；截至本次核实，实际有效来源是 `meta` 分支的 `geo/geosite/bybit.yaml`。

## 4. 当前更新时间与数量

时间：<!-- BYBIT_UPDATED_START -->2026-07-27 21:17:48 UTC<!-- BYBIT_UPDATED_END -->

数量：<!-- BYBIT_COUNTS_START -->17 条（HOST 2，HOST-SUFFIX 15，IP-CIDR 0，IP6-CIDR 0）<!-- BYBIT_COUNTS_END -->

可选地区规则另有 12 条（HOST 4，HOST-SUFFIX 8）。

## 5. 已确认的全球版域名

官方文档直接支持 `bybit.com`、`bytick.com`、`bybick.com` 与精确文档主机 `bybit-exchange.github.io`。MetaCubeX 和 v2fly 两个当前维护源一致收录以下集合：

- 精确主机：`bybit-exchange.github.io`、`bybit.ada.support`
- Bybit/备用根域：`byabcde.com`、`byapis.com`、`byapps.net`、`bybdc6.com`、`bybit-global.com`、`bybit.biz`、`bybit.cloud`、`bybit.com`、`bybitglobal.com`、`bycbe.com`、`bycsi.com`、`byd3c3.com`、`bymj.io`、`bytick.com`
- 人工补充：`bybick.com`，来自 Bybit 官方 V5 Rate Limit 文档

备用根域以两个活跃维护源的一致数据为依据；它们不等于对域名注册主体或永久用途的法律保证。新增或用途变化仍需复核。

## 6. 可选地区域名

`Bybit-Regional.list` 包含官方文档当前列出的荷兰、土耳其、哈萨克斯坦、阿联酋、EEA、印尼、格鲁吉亚和日本端点：

- 地区根域：`bybit.nl`、`bybit.tr`、`bybit-tr.com`、`bybit.kz`、`bybit.ae`、`bybit.eu`、`bybit.id`、`bybitgeorgia.ge`
- 日本精确主机：`api.manepa.jp`、`api-testnet.manepa.jp`、`stream.manepa.jp`、`www.manepa.jp`

这些端点服务独立地区账户，不默认加入全球主规则。`manepa.jp` 可能包含 Money Partners 的其他业务，所以绝不添加整个根域，只添加 Bybit 官方文档明确列出的精确主机。

地区 Raw 链接：

```text
https://raw.githubusercontent.com/bluelittlerain/quantumultx-bybit-rules/main/rule/QuantumultX/Bybit/Bybit-Regional.list
```

## 7. 被排除的共享服务

明确排除 `amazon.com`、`amazonaws.com`、`cloudfront.net`、`cloudflare.com`、`google.com`、`googleapis.com`、`gstatic.com`、`app-measurement.com`、`appsflyer.com`、`firebaseio.com`、`sentry.io`、`akamai.net`、`akamaiedge.net`、`apple.com` 与 `icloud.com` 等共享根域。

公共 CDN、统计 SDK、广告 SDK、归因 SDK、错误监控和 Apple 推送会被很多 App 共用。把这些根域整体导向 Bybit 策略会产生明显误匹配；一次 DNS 查询得到的 Cloudflare、CloudFront、Akamai 或 AWS 地址也不能证明 IP 为 Bybit 独占，因此不收录公共 CDN IP、宽泛 IP-CIDR 或 ASN。

## 8. Quantumult X 导入步骤

1. 打开 Quantumult X。
2. 进入 Filter Resources。
3. 添加远程资源。
4. 粘贴主规则 Raw 链接：

   ```text
   https://raw.githubusercontent.com/bluelittlerain/quantumultx-bybit-rules/main/rule/QuantumultX/Bybit/Bybit.list
   ```

5. 为资源设置名称，例如 `Bybit`。
6. 根据自身网络环境选择适当的现有策略组。
7. 启用该资源。
8. 将 Bybit 规则放在 Cryptocurrency、Proxy、Final 等更宽泛规则之前。
9. 更新资源并完全关闭后重新启动 Bybit。
10. 在 Quantumult X 活动记录中确认请求命中预期策略。

规则第三列中的 `Bybit` 是规则文件内的策略占位名称。通过 Quantumult X 添加远程 Filter Resource 时，可以为该资源选择已有策略；具体行为以用户当前版本和配置为准。无需修改已有 Final 策略。

## 9. Raw 链接

主规则：

```text
https://raw.githubusercontent.com/bluelittlerain/quantumultx-bybit-rules/main/rule/QuantumultX/Bybit/Bybit.list
```

可选地区规则：

```text
https://raw.githubusercontent.com/bluelittlerain/quantumultx-bybit-rules/main/rule/QuantumultX/Bybit/Bybit-Regional.list
```

## 10. 规则优先级

建议顺序：

```text
Bybit
Cryptocurrency
其他细分规则
Proxy
Final
```

Quantumult X 按规则顺序匹配；把 Bybit 放在综合规则和宽泛规则之前，才能让已收录请求优先命中资源所选策略。

## 11. 验证方法

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_bybit_rules.py
```

验证器检查 UTF-8、三列格式、类型、域名/IP、排序、重复、父域覆盖、禁止根域、文件头统计、README 数量、占位符和疑似凭据。

## 12. 抓漏域名方法

1. 更新 Quantumult X 所有资源。
2. 清理或记录当前活动日志。
3. 完全关闭 Bybit。
4. 重新启动 Bybit。
5. 依次测试 App 启动、登录、首页、行情、K 线、订单簿、现货、合约、期权、订单提交、资产、钱包、充值、提现、公告、活动、客服和 Web3。
6. 确认公共和私有 WebSocket 持续连接。
7. 查找落入 Cryptocurrency、Proxy、Direct 或 Final 的可疑 Bybit 域名。
8. 只补充能通过官方资源或多个可靠来源确认属于 Bybit 的域名。
9. 不补充共享 CDN、公共 SDK、广告、统计或推送服务。
10. 检查 Safari 和其他 App 没有因规则扩大而被错误分流。

记录模板：

| 时间 | Bybit 功能页面 | 请求域名/IP | 当前命中策略 | 是否确认属于 Bybit | 来源 | 建议处理 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## 13. 已知限制

Quantumult X 常规分流按目标域名和 IP 匹配，不是真正按 iOS App 进程或 Bundle ID 匹配。如果其他 App 请求同一域名，也可能命中 Bybit 规则；如果 Bybit 新增未收录域名，请求可能落入其他策略。加密 DNS、ECH、系统缓存和 App 内部连接复用也会影响日志可见性。

## 14. 误匹配风险

主规则只使用精确主机和较窄的 Bybit/备用根域，仍无法保证零误匹配。备用根域的用途可能改变，精确客服或文档主机也可能被浏览器访问。项目不会为追求表面“全覆盖”而加入公共 CDN、统计 SDK、广告 SDK 或 Apple 推送根域。

## 15. 更新脚本

```bash
# 正常联网更新
python3 scripts/update_bybit_quantumultx.py

# 只检查；需要更新时退出码为 1，无变化为 0，错误为 2
python3 scripts/update_bybit_quantumultx.py --check

# 打印差异但不写文件
python3 scripts/update_bybit_quantumultx.py --dry-run --verbose
```

脚本使用超时和 User-Agent，合并 `data/bybit_manual_domains.txt`，应用排除表，转换 Quantumult X 语法，去重、排序并消除父域冗余。空响应、HTML、异常少量或相对现有规则骤降会失败；所有检查通过后才原子替换规则文件。只有正文变化才更新时间。

## 16. GitHub Actions 更新方式

`.github/workflows/update-bybit-quantumultx.yml` 每周一 03:17 UTC 运行，也支持手动触发。工作流先测试，再更新和验证；只有生成文件确有变化才以 `github-actions[bot]` 提交 `chore: update Bybit QuantumultX rules`。它只使用 GitHub 自动提供的仓库权限，不保存私人 Token、订阅或 API Key。

## 17. 如何提交新域名

请提供域名、触发它的 Bybit 功能页面、Quantumult X 活动日志、官方页面/文档或至少两个可信维护源。官方确认但上游暂缺的条目加入 `data/bybit_manual_domains.txt`；共享服务或地区专用根域分别进入排除表或 Regional 规则。提交前运行单元测试和验证器。

## 18. 安全及合规说明

本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅地址或账户信息。文档中的策略名称均为通用示例。项目不读取或处理代理订阅地址、节点口令、API Key、助记词、私钥或 Bybit 凭据。

不同地区、账户类型和网络环境的可用性可能不同。规则只改变请求的网络出口，不改变账户的实名地区、居住地、KYC、服务资格、风控判断或合规要求。不得使用本项目绕过 Bybit 地区限制、KYC、平台安全机制或适用法律。

## 19. 设计边界

规则文件不包含具体节点名称，不创建代理节点或完整 Quantumult X 主配置，也不使用 `HOST-KEYWORD`、进程名、Bundle ID、公共 CDN IP 或大范围 ASN。地区规则是可选补充，不代表切换代理节点即可获得相应地区的服务资格。
