# Quantumult X App Rules

一个可自动维护、尽量降低误匹配范围的 Quantumult X 应用与服务分流规则集合。

当前提供 Binance、Bing、Bybit、Club Sim、Ether.fi、Kraken Pro、OKX 和 Wirex One 等独立规则。

每项规则均使用独立目录、独立 Raw 链接和独立更新流程，可以分别导入并绑定策略。同一个 GitHub 仓库不代表不同 App 的规则被合并。

## Available Rules

### Binance

- 目录：[rule/QuantumultX/Binance/](rule/QuantumultX/Binance/)
- 用途：Binance 核心交易、账户、行情与官方应用服务域名分流。
- 主规则：[Binance.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Binance/Binance.list)（<!-- BINANCE_MAIN_COUNTS_START -->13 条（HOST 2，HOST-SUFFIX 11，IP-CIDR 0，IP6-CIDR 0）<!-- BINANCE_MAIN_COUNTS_END -->，<!-- BINANCE_MAIN_UPDATED_START -->2026-07-29 04:58:19 UTC<!-- BINANCE_MAIN_UPDATED_END -->）
- 可选生态规则：[Binance-Ecosystem.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Binance/Binance-Ecosystem.list)（<!-- BINANCE_ECOSYSTEM_COUNTS_START -->4 条（HOST 0，HOST-SUFFIX 4，IP-CIDR 0，IP6-CIDR 0）<!-- BINANCE_ECOSYSTEM_COUNTS_END -->，<!-- BINANCE_ECOSYSTEM_UPDATED_START -->2026-07-29 04:58:19 UTC<!-- BINANCE_ECOSYSTEM_UPDATED_END -->）
- 可选地区服务规则：[Binance-Regional.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Binance/Binance-Regional.list)（<!-- BINANCE_REGIONAL_COUNTS_START -->1 条（HOST 0，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- BINANCE_REGIONAL_COUNTS_END -->，<!-- BINANCE_REGIONAL_UPDATED_START -->2026-07-29 04:58:19 UTC<!-- BINANCE_REGIONAL_UPDATED_END -->）
- 说明：[Binance README](rule/QuantumultX/Binance/README.md)

### Bing

- 目录：[rule/QuantumultX/Bing/](rule/QuantumultX/Bing/)
- 用途：Microsoft Bing 搜索应用与相关服务域名分流。
- 主规则：[Bing.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bing/Bing.list)（<!-- BING_MAIN_COUNTS_START -->5 条（HOST 0，HOST-SUFFIX 5，IP-CIDR 0，IP6-CIDR 0）<!-- BING_MAIN_COUNTS_END -->，<!-- BING_MAIN_UPDATED_START -->2026-07-29 04:59:16 UTC<!-- BING_MAIN_UPDATED_END -->）
- 可选 AI 规则：[Bing-AI.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bing/Bing-AI.list)（<!-- BING_AI_COUNTS_START -->3 条（HOST 1，HOST-SUFFIX 2，IP-CIDR 0，IP6-CIDR 0）<!-- BING_AI_COUNTS_END -->，<!-- BING_AI_UPDATED_START -->2026-07-29 04:59:16 UTC<!-- BING_AI_UPDATED_END -->）
- 说明：[Bing README](rule/QuantumultX/Bing/README.md)

### Bybit

- 目录：[rule/QuantumultX/Bybit/](rule/QuantumultX/Bybit/)
- 用途：Bybit 官方服务相关域名分流。
- 主规则：[Bybit.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bybit/Bybit.list)（<!-- BYBIT_COUNTS_START -->17 条（HOST 2，HOST-SUFFIX 15，IP-CIDR 0，IP6-CIDR 0）<!-- BYBIT_COUNTS_END -->）
- 可选地区规则：[Bybit-Regional.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/Bybit/Bybit-Regional.list)
- 说明：[Bybit README](rule/QuantumultX/Bybit/README.md)

### Club Sim

- 目录：[rule/QuantumultX/ClubSim/](rule/QuantumultX/ClubSim/)
- 用途：Club Sim 应用及相关网络服务域名分流。
- 主规则：[ClubSim.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/ClubSim/ClubSim.list)（<!-- CLUBSIM_MAIN_COUNTS_START -->2 条（HOST 1，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- CLUBSIM_MAIN_COUNTS_END -->）
- 可选网络规则：[ClubSim-Network.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/ClubSim/ClubSim-Network.list)（<!-- CLUBSIM_NETWORK_COUNTS_START -->5 条（HOST 5，HOST-SUFFIX 0，IP-CIDR 0，IP6-CIDR 0）<!-- CLUBSIM_NETWORK_COUNTS_END -->）
- 说明：[Club Sim README](rule/QuantumultX/ClubSim/README.md)

### Ether.fi

- 目录：[rule/QuantumultX/EtherFi/](rule/QuantumultX/EtherFi/)
- 用途：Ether.fi 官方应用、网站与第一方核心服务域名分流。
- 主规则：[EtherFi.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/EtherFi/EtherFi.list)（<!-- ETHERFI_MAIN_COUNTS_START -->1 条（HOST 0，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- ETHERFI_MAIN_COUNTS_END -->，<!-- ETHERFI_MAIN_UPDATED_START -->2026-07-29 06:31:42 UTC<!-- ETHERFI_MAIN_UPDATED_END -->）
- 说明：[Ether.fi README](rule/QuantumultX/EtherFi/README.md)

### Kraken Pro

- 目录：[rule/QuantumultX/KrakenPro/](rule/QuantumultX/KrakenPro/)
- 用途：Kraken Pro 交易、登录、账户、行情、API、WebSocket、帮助与第一方静态资源域名分流。
- 主规则：[KrakenPro.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/KrakenPro/KrakenPro.list)（<!-- KRAKENPRO_MAIN_COUNTS_START -->3 条（HOST 0，HOST-SUFFIX 3，IP-CIDR 0，IP6-CIDR 0）<!-- KRAKENPRO_MAIN_COUNTS_END -->，<!-- KRAKENPRO_MAIN_UPDATED_START -->2026-07-31 15:48:14 UTC<!-- KRAKENPRO_MAIN_UPDATED_END -->）
- 说明：[Kraken Pro README](rule/QuantumultX/KrakenPro/README.md)

### OKX

- 目录：[rule/QuantumultX/OKX/](rule/QuantumultX/OKX/)
- 用途：OKX 核心交易、账户、行情与官方应用服务域名分流。
- 主规则：[OKX.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/OKX/OKX.list)（<!-- OKX_MAIN_COUNTS_START -->7 条（HOST 0，HOST-SUFFIX 7，IP-CIDR 0，IP6-CIDR 0）<!-- OKX_MAIN_COUNTS_END -->，<!-- OKX_MAIN_UPDATED_START -->2026-07-29 04:58:21 UTC<!-- OKX_MAIN_UPDATED_END -->）
- 可选 Web3 规则：[OKX-Web3.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/OKX/OKX-Web3.list)（<!-- OKX_WEB3_COUNTS_START -->2 条（HOST 0，HOST-SUFFIX 2，IP-CIDR 0，IP6-CIDR 0）<!-- OKX_WEB3_COUNTS_END -->，<!-- OKX_WEB3_UPDATED_START -->2026-07-29 04:58:21 UTC<!-- OKX_WEB3_UPDATED_END -->）
- 说明：[OKX README](rule/QuantumultX/OKX/README.md)

### Wirex One

- 目录：[rule/QuantumultX/WirexOne/](rule/QuantumultX/WirexOne/)
- 用途：Wirex One 官方应用、账户、卡片、转账、钱包、帮助、状态及第一方静态资源域名分流。
- 主规则：[WirexOne.list](https://raw.githubusercontent.com/bluelittlerain/quantumultx-app-rules/main/rule/QuantumultX/WirexOne/WirexOne.list)（<!-- WIREXONE_MAIN_COUNTS_START -->2 条（HOST 1，HOST-SUFFIX 1，IP-CIDR 0，IP6-CIDR 0）<!-- WIREXONE_MAIN_COUNTS_END -->，<!-- WIREXONE_MAIN_UPDATED_START -->2026-08-02 00:24:14 UTC<!-- WIREXONE_MAIN_UPDATED_END -->）
- 说明：[Wirex One README](rule/QuantumultX/WirexOne/README.md)

## Usage

1. 打开 Quantumult X，进入 Filter Resources。
2. 添加远程资源并粘贴所需主规则的 Raw 链接。
3. 根据自身网络环境和服务可用性，将该远程资源绑定到适当的现有策略组。
4. 启用并更新资源，将应用专用规则放在 Proxy、Final 等更宽泛规则之前。
5. 重新启动目标 App，并在活动记录中确认请求命中预期策略。

规则文件第三列是资源内的通用策略占位名称。添加远程 Filter Resource 时可以选择已有策略组；具体行为以当前 Quantumult X 版本和配置为准。

## Scope and Limitations

Quantumult X 常规分流按照请求的目标域名和 IP 匹配，并不是真正按照 iOS App 进程、Bundle ID、Android 包名或进程名称匹配。如果多个 App 访问相同域名，也可能命中同一规则；如果服务新增尚未收录的域名，请求可能进入其他策略。

本项目刻意避免为了表面覆盖率而收录公共 CDN、共享身份或 KYC 平台、卡组织、银行、公共 RPC、广告、统计、系统推送及大型云服务根域名。规则只改变请求的网络出口，不改变账户身份、居住地、服务资格、KYC 状态、支付或银行卡资格及平台合规要求，也不应用于规避服务限制、风控或安全机制。

## Privacy

本项目不预设、记录或推荐用户使用的节点国家、代理服务商或订阅来源。

公开规则和文档不包含用户账户、私人查询参数、订阅地址、节点口令或完整 Quantumult X 配置。文档中的策略名称均为通用示例。

## Automated Maintenance

每个应用拥有独立的数据、更新脚本、验证脚本、测试和 GitHub Actions。候选域名不会自动进入正式规则，必须先取得可靠公开证据并写入人工批准文件；更新失败或数量异常下降时不会覆盖现有规则。

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_binance_rules.py
python3 scripts/validate_bing_rules.py
python3 scripts/validate_bybit_rules.py
python3 scripts/validate_clubsim_rules.py
python3 scripts/validate_etherfi_rules.py
python3 scripts/validate_krakenpro_rules.py
python3 scripts/validate_okx_rules.py
python3 scripts/validate_wirexone_rules.py
```

## License

本项目采用 [MIT License](LICENSE)。
