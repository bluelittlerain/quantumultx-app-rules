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

## Usage

1. 打开 Quantumult X，进入 Filter Resources。
2. 添加远程资源并粘贴所需规则的 Raw 链接。
3. 为资源设置便于识别的名称。
4. 根据自身网络环境和服务可用性，将远程资源绑定到适当的现有策略组。
5. 启用并更新资源，将专用规则放在 Proxy、Final 等更宽泛规则之前。
6. 重新启动目标 App，在 Quantumult X 活动记录中确认请求命中预期策略。

规则第三列中的 `Bybit` 或 `ClubSim` 是规则文件内的策略占位名称。添加远程 Filter Resource 时可以为资源选择已有策略；具体行为以当前 Quantumult X 版本和用户配置为准。

## Scope and Limitations

Quantumult X 常规分流基于目标域名和 IP，不是真正按 iOS App 进程、Bundle ID 或 Android 包名匹配。如果其他 App 请求相同域名，也可能命中对应规则；服务新增尚未收录的域名时，请求可能落入其他策略。

本项目避免收录公共 CDN、共享 SDK、广告、统计、崩溃报告和系统推送根域名。规则只改变请求的网络出口，不改变账户身份、实名地区、服务资格、SIM 卡注册状态、付款资格或平台合规要求，也不得用于规避身份验证、付款验证、地区限制、KYC、风控或安全机制。

本地验证命令：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_bybit_rules.py
python3 scripts/validate_clubsim_rules.py
```

## Privacy

本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅链接或账户资料。文档中的策略名称均为通用示例，仓库不记录用户的私人网络配置。

## License

本项目采用 [MIT License](LICENSE)。
