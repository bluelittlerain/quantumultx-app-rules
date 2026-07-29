# Ether.fi Quantumult X Rules

## 用途与范围

本目录维护 Ether.fi 官方应用、网站及第一方服务的低误匹配 Quantumult X 规则。主规则覆盖登录、账户、钱包连接入口、Cash、Stake、Liquid、ETHFI、帮助内容、官方页面资源以及位于同一第一方根域下的服务接口。

Quantumult X 常规分流根据请求域名和 IP 地址匹配，不会真正识别 iOS App Bundle ID、Android 包名或进程名称。其他应用访问相同域名时也可能命中本规则；Ether.fi 新增尚未收录的独立域名时，请求可能落入其他策略。

## 当前规则

- 主规则：<!-- ETHERFI_MAIN_COUNTS_START -->1 条（HOST 0，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- ETHERFI_MAIN_COUNTS_END -->
- 更新时间：<!-- ETHERFI_MAIN_UPDATED_START -->2026-07-29 06:31:42 UTC<!-- ETHERFI_MAIN_UPDATED_END -->
- Raw：[EtherFi.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/EtherFi/EtherFi.list)

`HOST-SUFFIX,ether.fi,EtherFi` 覆盖 `www.ether.fi`、`help.ether.fi`、`governance.ether.fi` 及其他第一方子域，因此不重复加入精确 HOST。

## 数据来源

1. [Ether.fi 官方网站](https://www.ether.fi/)
2. [Ether.fi Help Center](https://help.ether.fi/en/)
3. [Ether.fi 技术文档](https://etherfi.gitbook.io/etherfi)
4. [Ether.fi App Store 页面](https://apps.apple.com/us/app/ether-fi-crypto-card-spend/id6670338367)
5. [Ether.fi Google Play 页面](https://play.google.com/store/apps/details?id=etherfi.app)
6. [Ether.fi 官方 GitHub](https://github.com/etherfi-protocol)
7. 官方网站及 Web App 公开静态代码中的主机引用

截至当前调研时间，v2fly/domain-list-community、MetaCubeX/meta-rules-dat 和 blackmatrix7/ios_rule_script 均没有可直接使用的 Ether.fi 专用规则文件。因此更新器以公开官方页面的实时可用性和身份标记作为上游安全检查，正式输出仍只来自人工批准文件。

## 分类结果

Cash、Stake、Liquid、ETHFI、账户和帮助页面均由 `ether.fi` 根域覆盖。调研没有确认独立于该根域、且主要由 Ether.fi 使用的核心 Web3 根域，因此没有创建内容重复或依赖共享服务的 `EtherFi-Web3.list`。

官方 Web App 公开代码引用 WalletConnect/Reown、Safe、Turnkey、公共链 RPC、区块浏览器、客户支持、身份核验、错误监控和应用深链服务。这些服务可能被大量其他应用共同使用，不进入正式规则。

## 排除原则

`data/etherfi_excluded_domains.txt` 明确排除：

- 公共 CDN 与大型云服务根域
- 第三方钱包和钱包连接平台
- 第三方区块链 RPC、浏览器与基础设施
- 广告、归因、分析、错误监控和客户支持平台
- 系统服务与公共身份平台
- GitBook、Medium、Notion 等共享发布平台

DNS、TLS、CNAME 和公开静态代码只能作为辅助证据，不能单独证明某个共享域名应当由 Ether.fi 规则接管。项目不收录临时解析得到的 CDN IP、公共 IP 段或大型网络范围。

## Quantumult X 导入

1. 打开 Quantumult X，进入 Filter Resources。
2. 添加远程资源。
3. 粘贴 `EtherFi.list` 的 Raw 链接。
4. 为资源设置便于识别的名称。
5. 根据自身网络环境和服务可用性，将远程资源绑定到适当的现有策略组。
6. 启用并更新资源。
7. 将 Ether.fi 专用规则放在 Web3、Proxy、Final 等更宽泛规则之前。
8. 重新启动目标应用，并在活动记录中确认第一方域名命中预期策略。

规则第三列中的 `EtherFi` 是通用策略占位名称。通过 Filter Resources 导入时可以选择已有策略组，无需创建同名节点或策略组。

## 验证与抓漏

依次检查应用启动、登录、账户、Cash、Stake、Liquid、资产展示、帮助页面和钱包连接入口。仅记录去除查询参数后的域名，不公开提交账户资料、交易内容、身份资料或其他敏感信息。

| 功能 | 请求域名 | 当前策略 | 是否第一方 | 公开证据 | 建议 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

只补充能由官方资料或多项可靠公开证据确认的第一方域名。不要为了扩大覆盖而加入共享钱包、公共 RPC、公共 CDN、广告、分析或系统服务。

## 更新与验证

```bash
python3 -m unittest discover -s tests -p "test_etherfi_rules.py" -v
python3 scripts/update_etherfi_quantumultx.py --check
python3 scripts/validate_etherfi_rules.py
```

更新脚本支持 `--check`、`--dry-run` 和 `--verbose`，具有网络超时、异常响应拒绝、数量下限、异常减少保护及原子写入。候选 TSV 只用于审查，不会自动进入正式规则。

`.github/workflows/update-etherfi-quantumultx.yml` 每周独立检查 Ether.fi 项目，也支持手动触发。只有测试、更新与验证全部成功且正式文件确有变化时才会提交。

## 隐私、安全与合规

本项目不收集用户数据，不记录节点信息、订阅来源、账户资料或私人 Quantumult X 配置。提交抓漏证据前应删除所有敏感内容，只保留域名和可公开核实的来源。

规则只改变请求的网络路径，不改变账户身份、服务资格、链上状态或平台合规要求，也不应用于规避身份验证、服务限制、风控或安全机制。链上交互与资产操作具有风险，使用者应独立核实交易内容和适用条件。
