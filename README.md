# Quantumult X App Rules

一个可自动维护、尽量降低误匹配范围的 Quantumult X 应用与服务分流规则集合。目前提供 Bybit 与 Club Sim 相关规则，并可在未来扩展其他独立规则。所有规则均不预设或推荐特定节点国家、地区或代理服务商。

每项规则使用独立目录和独立 Raw 链接，可分别导入、启用并绑定不同策略。同处一个 GitHub 仓库不表示不同 App 的规则被合并。

## Available Rules

### Bybit

主规则当前为 <!-- BYBIT_COUNTS_START -->17 条（HOST 2，HOST-SUFFIX 15，IP-CIDR 0，IP6-CIDR 0）<!-- BYBIT_COUNTS_END -->。

- 主规则：[Bybit.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bybit/Bybit.list)
- 可选地区规则：[Bybit-Regional.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bybit/Bybit-Regional.list)
- 详细文档：[rule/QuantumultX/Bybit/README.md](rule/QuantumultX/Bybit/README.md)

主规则面向通用 Bybit 业务域名；可选地区规则仅列出官方文档中的独立地区端点，两者应按实际账户与服务范围分别导入。

### Club Sim

主规则当前为 <!-- CLUBSIM_MAIN_COUNTS_START -->2 条（HOST 1，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- CLUBSIM_MAIN_COUNTS_END -->；可选网络规则为 <!-- CLUBSIM_NETWORK_COUNTS_START -->5 条（HOST 5，HOST-SUFFIX 0，IP-CIDR 0，IP6-CIDR 0）<!-- CLUBSIM_NETWORK_COUNTS_END -->。

- 主规则：[ClubSim.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/ClubSim/ClubSim.list)
- 可选网络规则：[ClubSim-Network.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/ClubSim/ClubSim-Network.list)
- 详细文档：[rule/QuantumultX/ClubSim/README.md](rule/QuantumultX/ClubSim/README.md)

主规则面向 Club Sim App 业务域名；Network 文件仅包含经确认的 eSIM、ePDG 与运营商网络服务精确主机，应按实际需要独立导入。

### Binance

主规则当前为 <!-- BINANCE_MAIN_COUNTS_START -->13 条（HOST 2，HOST-SUFFIX 11，IP-CIDR 0，IP6-CIDR 0）<!-- BINANCE_MAIN_COUNTS_END -->，更新时间为 <!-- BINANCE_MAIN_UPDATED_START -->2026-07-29 04:58:19 UTC<!-- BINANCE_MAIN_UPDATED_END -->。

- 主规则：[Binance.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Binance/Binance.list)
- 可选生态规则：[Binance-Ecosystem.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Binance/Binance-Ecosystem.list)，<!-- BINANCE_ECOSYSTEM_COUNTS_START -->4 条（HOST 0，HOST-SUFFIX 4，IP-CIDR 0，IP6-CIDR 0）<!-- BINANCE_ECOSYSTEM_COUNTS_END -->，更新时间 <!-- BINANCE_ECOSYSTEM_UPDATED_START -->2026-07-29 04:58:19 UTC<!-- BINANCE_ECOSYSTEM_UPDATED_END -->
- 可选地区规则：[Binance-Regional.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Binance/Binance-Regional.list)，<!-- BINANCE_REGIONAL_COUNTS_START -->1 条（HOST 0，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- BINANCE_REGIONAL_COUNTS_END -->，更新时间 <!-- BINANCE_REGIONAL_UPDATED_START -->2026-07-29 04:58:19 UTC<!-- BINANCE_REGIONAL_UPDATED_END -->
- 详细文档：[rule/QuantumultX/Binance/README.md](rule/QuantumultX/Binance/README.md)

主规则面向全球版核心交易服务；生态与独立地区服务分别保存在可选文件中，不默认合并。

### OKX

主规则当前为 <!-- OKX_MAIN_COUNTS_START -->7 条（HOST 0，HOST-SUFFIX 7，IP-CIDR 0，IP6-CIDR 0）<!-- OKX_MAIN_COUNTS_END -->，更新时间为 <!-- OKX_MAIN_UPDATED_START -->2026-07-29 04:58:21 UTC<!-- OKX_MAIN_UPDATED_END -->。

- 主规则：[OKX.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/OKX/OKX.list)
- 可选 Web3 规则：[OKX-Web3.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/OKX/OKX-Web3.list)，<!-- OKX_WEB3_COUNTS_START -->2 条（HOST 0，HOST-SUFFIX 2，IP-CIDR 0，IP6-CIDR 0）<!-- OKX_WEB3_COUNTS_END -->，更新时间 <!-- OKX_WEB3_UPDATED_START -->2026-07-29 04:58:21 UTC<!-- OKX_WEB3_UPDATED_END -->
- 详细文档：[rule/QuantumultX/OKX/README.md](rule/QuantumultX/OKX/README.md)

主规则面向交易、账户、资产和行情服务；X Layer 与 OKLink 仅在可选 Web3 文件中提供。

### Bing

主规则当前为 <!-- BING_MAIN_COUNTS_START -->5 条（HOST 0，HOST-SUFFIX 5，IP-CIDR 0，IP6-CIDR 0）<!-- BING_MAIN_COUNTS_END -->，更新时间为 <!-- BING_MAIN_UPDATED_START -->2026-07-29 04:59:16 UTC<!-- BING_MAIN_UPDATED_END -->。

- 主规则：[Bing.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bing/Bing.list)
- 可选 AI 规则：[Bing-AI.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bing/Bing-AI.list)，<!-- BING_AI_COUNTS_START -->3 条（HOST 1，HOST-SUFFIX 2，IP-CIDR 0，IP6-CIDR 0）<!-- BING_AI_COUNTS_END -->，更新时间 <!-- BING_AI_UPDATED_START -->2026-07-29 04:59:16 UTC<!-- BING_AI_UPDATED_END -->
- 详细文档：[rule/QuantumultX/Bing/README.md](rule/QuantumultX/Bing/README.md)

主规则仅覆盖 Bing 搜索相关根域；Copilot Search 与独立 AI 服务放在可选文件中。

## Usage

1. 打开 Quantumult X，进入 Filter Resources。
2. 添加远程资源并粘贴所需规则的 Raw 链接。
3. 为资源设置便于识别的名称。
4. 根据自身网络环境和服务可用性，将远程资源绑定到适当的现有策略组。
5. 启用并更新资源，将专用规则放在 Proxy、Final 等更宽泛规则之前。
6. 重新启动目标 App，在 Quantumult X 活动记录中确认请求命中预期策略。

规则第三列中的 `Bybit`、`ClubSim`、`Binance`、`OKX` 或 `Bing` 是规则文件内的策略占位名称。添加远程 Filter Resource 时可以为资源选择已有策略；具体行为以当前 Quantumult X 版本和用户配置为准。

## Scope and Limitations

Quantumult X 常规分流基于目标域名和 IP，不是真正按 iOS App 进程、Bundle ID 或 Android 包名匹配。如果其他 App 请求相同域名，也可能命中对应规则；服务新增尚未收录的域名时，请求可能落入其他策略。

本项目避免收录公共 CDN、共享 SDK、广告、统计、崩溃报告和系统推送根域名。规则只改变请求的网络出口，不改变账户身份、实名地区、服务资格、SIM 卡注册状态、付款资格或平台合规要求，也不得用于规避身份验证、付款验证、地区限制、KYC、风控或安全机制。

本地验证命令：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_bybit_rules.py
python3 scripts/validate_clubsim_rules.py
python3 scripts/validate_binance_rules.py
python3 scripts/validate_okx_rules.py
python3 scripts/validate_bing_rules.py
```

## Privacy

本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅链接或账户资料。文档中的策略名称均为通用示例，仓库不记录用户的私人网络配置。

## License

本项目采用 [MIT License](LICENSE)。
