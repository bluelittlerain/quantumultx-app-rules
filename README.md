# Quantumult X App Rules

一个可自动维护、尽量降低误匹配范围的 Quantumult X 应用与服务分流规则集合。

当前提供 Bybit、Club Sim、Binance、OKX、Bing 和 Ether.fi 独立规则，未来可继续扩展其他应用或服务。每个项目均使用独立目录、独立 Raw 链接和独立自动更新流程，可以单独导入并绑定策略，不共享任何个人配置。同一个 GitHub 仓库不代表不同 App 的规则被合并。

## Available Rules

### Bybit

- 目录：[rule/QuantumultX/Bybit/](rule/QuantumultX/Bybit/)
- 用途：Bybit 官方服务相关域名分流。
- 主规则：[Bybit.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bybit/Bybit.list)，<!-- BYBIT_COUNTS_START -->17 条（HOST 2，HOST-SUFFIX 15，IP-CIDR 0，IP6-CIDR 0）<!-- BYBIT_COUNTS_END -->
- 可选规则：[Bybit-Regional.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bybit/Bybit-Regional.list)
- 说明：[Bybit README](rule/QuantumultX/Bybit/README.md)

### Club Sim

- 目录：[rule/QuantumultX/ClubSim/](rule/QuantumultX/ClubSim/)
- 用途：Club Sim 应用及相关网络服务域名分流。
- 主规则：[ClubSim.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/ClubSim/ClubSim.list)，<!-- CLUBSIM_MAIN_COUNTS_START -->2 条（HOST 1，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- CLUBSIM_MAIN_COUNTS_END -->
- 可选规则：[ClubSim-Network.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/ClubSim/ClubSim-Network.list)，<!-- CLUBSIM_NETWORK_COUNTS_START -->5 条（HOST 5，HOST-SUFFIX 0，IP-CIDR 0，IP6-CIDR 0）<!-- CLUBSIM_NETWORK_COUNTS_END -->
- 说明：[Club Sim README](rule/QuantumultX/ClubSim/README.md)

### Binance

- 目录：[rule/QuantumultX/Binance/](rule/QuantumultX/Binance/)
- 用途：Binance 核心交易、账户、行情与官方应用服务域名分流。
- 主规则：[Binance.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Binance/Binance.list)，<!-- BINANCE_MAIN_COUNTS_START -->13 条（HOST 2，HOST-SUFFIX 11，IP-CIDR 0，IP6-CIDR 0）<!-- BINANCE_MAIN_COUNTS_END -->；<!-- BINANCE_MAIN_UPDATED_START -->2026-07-29 04:58:19 UTC<!-- BINANCE_MAIN_UPDATED_END -->
- 可选生态规则：[Binance-Ecosystem.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Binance/Binance-Ecosystem.list)，<!-- BINANCE_ECOSYSTEM_COUNTS_START -->4 条（HOST 0，HOST-SUFFIX 4，IP-CIDR 0，IP6-CIDR 0）<!-- BINANCE_ECOSYSTEM_COUNTS_END -->；<!-- BINANCE_ECOSYSTEM_UPDATED_START -->2026-07-29 04:58:19 UTC<!-- BINANCE_ECOSYSTEM_UPDATED_END -->
- 可选区域服务规则：[Binance-Regional.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Binance/Binance-Regional.list)，<!-- BINANCE_REGIONAL_COUNTS_START -->1 条（HOST 0，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- BINANCE_REGIONAL_COUNTS_END -->；<!-- BINANCE_REGIONAL_UPDATED_START -->2026-07-29 04:58:19 UTC<!-- BINANCE_REGIONAL_UPDATED_END -->
- 说明：[Binance README](rule/QuantumultX/Binance/README.md)

### OKX

- 目录：[rule/QuantumultX/OKX/](rule/QuantumultX/OKX/)
- 用途：OKX 核心交易、账户、行情与官方应用服务域名分流。
- 主规则：[OKX.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/OKX/OKX.list)，<!-- OKX_MAIN_COUNTS_START -->7 条（HOST 0，HOST-SUFFIX 7，IP-CIDR 0，IP6-CIDR 0）<!-- OKX_MAIN_COUNTS_END -->；<!-- OKX_MAIN_UPDATED_START -->2026-07-29 04:58:21 UTC<!-- OKX_MAIN_UPDATED_END -->
- 可选 Web3 规则：[OKX-Web3.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/OKX/OKX-Web3.list)，<!-- OKX_WEB3_COUNTS_START -->2 条（HOST 0，HOST-SUFFIX 2，IP-CIDR 0，IP6-CIDR 0）<!-- OKX_WEB3_COUNTS_END -->；<!-- OKX_WEB3_UPDATED_START -->2026-07-29 04:58:21 UTC<!-- OKX_WEB3_UPDATED_END -->
- 说明：[OKX README](rule/QuantumultX/OKX/README.md)

### Bing

- 目录：[rule/QuantumultX/Bing/](rule/QuantumultX/Bing/)
- 用途：Microsoft Bing 搜索应用与相关服务域名分流。
- 主规则：[Bing.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bing/Bing.list)，<!-- BING_MAIN_COUNTS_START -->5 条（HOST 0，HOST-SUFFIX 5，IP-CIDR 0，IP6-CIDR 0）<!-- BING_MAIN_COUNTS_END -->；<!-- BING_MAIN_UPDATED_START -->2026-07-29 04:59:16 UTC<!-- BING_MAIN_UPDATED_END -->
- 可选 AI 规则：[Bing-AI.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bing/Bing-AI.list)，<!-- BING_AI_COUNTS_START -->3 条（HOST 1，HOST-SUFFIX 2，IP-CIDR 0，IP6-CIDR 0）<!-- BING_AI_COUNTS_END -->；<!-- BING_AI_UPDATED_START -->2026-07-29 04:59:16 UTC<!-- BING_AI_UPDATED_END -->
- 说明：[Bing README](rule/QuantumultX/Bing/README.md)

### Ether.fi

- 目录：[rule/QuantumultX/EtherFi/](rule/QuantumultX/EtherFi/)
- 用途：Ether.fi 官方应用、网站、账户、Cash、Stake、Liquid 与相关第一方服务域名分流。
- 主规则：[EtherFi.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/EtherFi/EtherFi.list)，<!-- ETHERFI_MAIN_COUNTS_START -->1 条（HOST 0，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- ETHERFI_MAIN_COUNTS_END -->；<!-- ETHERFI_MAIN_UPDATED_START -->2026-07-29 06:31:42 UTC<!-- ETHERFI_MAIN_UPDATED_END -->
- 说明：[Ether.fi README](rule/QuantumultX/EtherFi/README.md)

## Usage

1. 打开 Quantumult X，进入 Filter Resources。
2. 添加远程资源。
3. 输入对应规则文件的 Raw 链接。
4. 根据自身网络环境和服务可用性，将远程资源绑定到适当的现有策略组。
5. 启用并更新资源，将专用规则放在 Proxy、Final 等更宽泛规则之前。

规则文件第三列是资源内的通用策略占位名称。添加远程 Filter Resource 时可以选择已有策略组；具体行为以当前 Quantumult X 版本和配置为准。

## Scope and Limitations

Quantumult X 常规分流基于：

- 请求域名
- IP 地址

它不是真正按照以下信息匹配：

- iOS App Bundle ID
- Android 包名
- 进程名称

如果多个 App 使用相同第三方服务域名，可能出现共享匹配；服务新增尚未收录的域名时，请求也可能落入其他策略。本项目避免为追求表面覆盖率而收录公共 CDN、广告、统计、通用 SDK、系统推送或大型云服务根域名。

规则只改变请求的网络路径，不改变账户身份、服务资格、支付资格或平台合规要求，也不应用于规避身份验证、服务限制、风控或安全机制。

## Maintenance and Validation

每个项目拥有独立数据、更新脚本、验证脚本、测试和 GitHub Actions。候选域名不会自动进入正式规则，必须先取得可靠公开证据并写入人工批准文件。

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_bybit_rules.py
python3 scripts/validate_clubsim_rules.py
python3 scripts/validate_binance_rules.py
python3 scripts/validate_okx_rules.py
python3 scripts/validate_bing_rules.py
python3 scripts/validate_etherfi_rules.py
```

## Privacy

本项目不收集用户数据，不记录节点信息、订阅来源或账户资料，也不包含用户的私人 Quantumult X 配置。公开文档中的策略名称均为通用示例。

## License

本项目采用 [MIT License](LICENSE)。
