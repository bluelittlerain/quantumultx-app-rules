# Quantumult X Bybit Rules

## 项目简介

一个可自动维护、尽量降低误匹配范围的 Bybit 专用 Quantumult X 域名分流规则项目。项目与具体节点国家、地区和代理服务商无关，用户可以在 Quantumult X 中自行将规则绑定到任意适当的现有策略。

主规则当前为 <!-- BYBIT_COUNTS_START -->17 条（HOST 2，HOST-SUFFIX 15，IP-CIDR 0，IP6-CIDR 0）<!-- BYBIT_COUNTS_END -->。

## 规则链接

- 主规则：[Bybit.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-bybit-rules/main/rule/QuantumultX/Bybit/Bybit.list)
- 可选地区规则：[Bybit-Regional.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-bybit-rules/main/rule/QuantumultX/Bybit/Bybit-Regional.list)
- 完整说明：[rule/QuantumultX/Bybit/README.md](rule/QuantumultX/Bybit/README.md)

## Quantumult X 导入方法

1. 打开 Quantumult X，进入 Filter Resources。
2. 添加远程资源并粘贴主规则 Raw 链接。
3. 为资源设置名称，例如 `Bybit`。
4. 根据自身网络环境和服务可用性，将该资源绑定到适当的现有策略组。
5. 启用并更新资源，将 Bybit 规则放在 Cryptocurrency、Proxy、Final 等更宽泛规则之前。
6. 重新启动 Bybit，在 Quantumult X 活动记录中确认请求命中预期策略。

规则第三列中的 `Bybit` 是规则文件内的策略占位名称。通过 Quantumult X 添加远程 Filter Resource 时，可以为该资源选择已有策略；具体行为以用户当前版本和配置为准。

## 隐私和通用性说明

本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅地址或账户信息。文档中的策略名称均为通用示例。

## 已知限制

Quantumult X 常规分流按目标域名和 IP 匹配，不是真正按 iOS App 进程或 Bundle ID 匹配。项目刻意不收录公共 CDN、共享 SDK、广告、统计或 Apple 推送根域。

如果其他 App 请求相同域名，也可能命中 Bybit 规则；如果 Bybit 新增尚未收录的域名，请求可能落入其他策略。不同地区、账户类型和网络环境的可用性可能不同。规则只改变请求的网络出口，不改变账户的实名地区、服务资格或平台合规要求。

## 本地检查

```bash
python3 -m unittest discover -s tests -v
python3 scripts/update_bybit_quantumultx.py --check
python3 scripts/validate_bybit_rules.py
```

本项目采用 [MIT License](LICENSE)。不得使用本项目绕过 Bybit 的地区限制、KYC、风控或平台安全机制。
