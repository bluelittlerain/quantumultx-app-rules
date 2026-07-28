# Quantumult X Rules

一个可自动维护、尽量降低误匹配范围的 Quantumult X 规则项目。当前提供 Bybit 与 Club Sim 专用规则；所有规则都与具体节点国家、地区和代理服务商无关。

## Club Sim

目标是 Club Sim 储值卡 App（iOS App Store ID `1286595675`、Android 包名 `com.pccw.clubsim`）。主规则当前为 <!-- CLUBSIM_MAIN_COUNTS_START -->2 条（HOST 1，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- CLUBSIM_MAIN_COUNTS_END -->；可选网络规则为 <!-- CLUBSIM_NETWORK_COUNTS_START -->5 条（HOST 5，HOST-SUFFIX 0，IP-CIDR 0，IP6-CIDR 0）<!-- CLUBSIM_NETWORK_COUNTS_END -->。

- 主规则：[ClubSim.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-bybit-rules/main/rule/QuantumultX/ClubSim/ClubSim.list)
- 可选网络规则：[ClubSim-Network.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-bybit-rules/main/rule/QuantumultX/ClubSim/ClubSim-Network.list)
- 完整说明：[rule/QuantumultX/ClubSim/README.md](rule/QuantumultX/ClubSim/README.md)

在 Quantumult X 的 Filter Resources 中添加主规则 Raw 链接，并根据自身网络环境和服务可用性，将该远程资源绑定到适当的现有策略组。Network 文件只涉及可选的 eSIM、ePDG 与运营商网络服务，应按实际需要独立导入。

## Bybit

一个可自动维护、尽量降低误匹配范围的 Bybit 专用 Quantumult X 域名分流规则。项目与具体节点国家、地区和代理服务商无关，用户可以在 Quantumult X 中自行将规则绑定到任意适当的现有策略。

主规则当前为 <!-- BYBIT_COUNTS_START -->17 条（HOST 2，HOST-SUFFIX 15，IP-CIDR 0，IP6-CIDR 0）<!-- BYBIT_COUNTS_END -->。

- 主规则：[Bybit.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-bybit-rules/main/rule/QuantumultX/Bybit/Bybit.list)
- 可选地区规则：[Bybit-Regional.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-bybit-rules/main/rule/QuantumultX/Bybit/Bybit-Regional.list)
- 完整说明：[rule/QuantumultX/Bybit/README.md](rule/QuantumultX/Bybit/README.md)

## Quantumult X 导入方法

1. 打开 Quantumult X，进入 Filter Resources。
2. 添加远程资源并粘贴所需规则的 Raw 链接。
3. 为资源设置便于识别的名称。
4. 根据自身网络环境和服务可用性，将该资源绑定到适当的现有策略组。
5. 启用并更新资源，将专用规则放在 Proxy、Final 等更宽泛规则之前。
6. 重新启动目标 App，在 Quantumult X 活动记录中确认请求命中预期策略。

规则第三列中的 `Bybit` 或 `ClubSim` 是规则文件内的策略占位名称。通过 Quantumult X 添加远程 Filter Resource 时，可以为该资源选择已有策略；具体行为以用户当前版本和配置为准。

## 隐私和通用性说明

本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅地址或账户资料。文档中的策略名称均为通用示例，也不记录维护者的个人网络配置。

## 已知限制

Quantumult X 常规分流按目标域名和 IP 匹配，不是真正按 iOS App 进程、Bundle ID 或 Android 包名匹配。如果其他 App 请求相同域名，也可能命中相应规则；如果目标服务新增尚未收录的域名，请求可能落入其他策略。

项目刻意不收录公共 CDN、共享身份平台、公共支付平台、广告、统计、崩溃报告或系统推送根域名。规则只改变请求的网络出口，不改变账户身份、实名地区、服务资格、SIM 卡注册状态、付款资格或平台合规要求。

## 本地检查

```bash
python3 -m unittest discover -s tests -v
python3 scripts/update_bybit_quantumultx.py --check
python3 scripts/validate_bybit_rules.py
python3 scripts/discover_clubsim_domains.py --check --no-apk
python3 scripts/update_clubsim_quantumultx.py --check
python3 scripts/validate_clubsim_rules.py
```

本项目采用 [MIT License](LICENSE)。不得使用本项目规避任何服务的身份验证、付款验证、地区限制、KYC、风控或安全机制。
