# Lab3 工作交接

用户因额度不足要求立即收尾，交给其他 AI 继续。**实验实测与主要截图已完成；最终 Word 报告尚未生成。** 请勿把参考报告或工作文件当成已完成的交付。

## 用户要求

仔细完成《计算机网络实验手册》的 Lab3 IPv4，使用当前文件夹里的学校模板，可参考用户自己的 Lab2；质量要超过学长报告；必须实际操控 Wireshark 并截图。

学生：刘小凡，学号 10244602411，年级按 Lab2 为 2024 级。实际实验日期 2026-10-13，实验编号 Lab3，名称 IPv4，模板实验时间 2 学时。教师与成绩没有资料，留空。

## 文件位置

工作目录：`C:\University Courses\计算机网络lab\_lab3_work`

原始手册：`C:\University Courses\计算机网络lab\计算机网络实验手册.doc`

原始模板：`C:\University Courses\计算机网络lab\计算机网络实验报告 Lab XXX.doc`

用户 Lab2：`C:\University Courses\计算机网络lab\10244602411_刘小凡_Ethernet.docx`

学长参考：`C:\Users\18963\.zcode\workspace\default\大二上A\大二上A\02_计算机网络\实验\实验报告及源码\Lab3\10245101445-张荣昊-Lab3.pdf`

上述原始文件均未修改。

工作目录中：

- `manual.txt`：通过 Word 只读提取的本次手册全文。Lab3 从 IPV4 开始，到 ARP 前结束。
- `reference.txt`、`reference-1.png` 至 `reference-9.png`：学长 PDF 全文和逐页渲染。
- `lab2.txt`：用户 Lab2 内容与表格提取。
- `template.docx`：由学校 .doc 转换的工作参考，**从它的副本填充报告**。
- `template_word.pdf`：Word 原生渲染的模板；`template-1.png` 为学校模板外观参考。
- `artifact.md`：模板结构、页边距、字体角色、槽位、保留项与检查要求。
- `template_parts.json`、`template_style.json`：模板 OOXML 包清单及样式检查。
- `facts.json`：已完成的独立数据分析结果，含 HTTP 各帧字段、首部字节、校验和求和过程、路径统计。

## 手册提交要求

1. Step 1：成功获取同一远端服务器的 HTTP 网页，捕获 tcp port 80 流量；记录 traceroute/tracert。
2. Step 2：检查 IPv4 首部全部字段及字节。
3. Step 3：绘制 IPv4 包结构图，标明字段字节偏移和长度，合并共享字节的字段；回答六题：本机/服务器 IP、Total Length 范围、Identification 规律、发送初始 TTL、未分片判断、IHL 编码。
4. Step 4：绘制按跳数编号的路径图，显示本机和服务器 IP、路由器 IP、未知跳；解释组织标注来源，保留真实输出。
5. Step 5：选取**接收方向、非零 checksum、20 字节首部**的包，把 10 个 16 位字逐项对应到字段，列出求和与回卷，验证结果 0xffff。

学校报告六部分：一、实验目的；二、实验内容与实验步骤；三、实验环境；四、实验过程与分析；五、实验结果总结；六、附录。模板有学校页眉和 PAGE/NUMPAGES 页脚，需保留。

## 实测环境

- Windows 11 25H2，build 26200，64 位。
- Wireshark/TShark 4.6.8，Npcap 1.88。
- curl 8.21.0。
- WLAN：MediaTek Wi-Fi 6E MT7922 (RZ616) 160MHz Wireless LAN Card。
- WLAN IPv4：`172.31.165.86`，网关 `172.31.0.1`。
- 本机 MAC `14:ac:60:56:df:85`；本次链路下一跳 MAC `54:c6:ff:7b:38:02`。
- 抓包接口：`\Device\NPF_{C59C96C9-17AD-4F4E-ADD7-2E166380D039}`。
- 实际 HTTP URL：`http://www.baidu.com/`，使用 `--resolve` 固定服务器 `182.61.200.108`，`--interface 172.31.165.86`，`--noproxy '*'`，`-4`。
- GET 成功，HTTP 200，Content-Length 2381，curl SIZE_DOWNLOAD 2381，TIME_TOTAL 0.854669 秒。响应首部和网页正文已保存。
- 捕获采用 Ethernet 链路层，关闭混杂模式，启用网络名称解析。

## 抓包文件与使用范围

全部在 `_lab3_work\captures`：

- `Lab3_HTTP.pcapng`：Wireshark GUI 实际捕获的原始 108 帧，包含其他应用的背景 HTTP；**不要将背景连接纳入 Lab3 分析**，也不建议放进最终交付包。
- `Lab3_HTTP_target.pcapng`：从原始迹线按 `tcp.stream == 0` 导出的真实目标连接，共 19 帧。导出未改写报文；目标是原始前 19 帧，因此帧号保持 1–19。本机发送 10 帧，接收 9 帧。后续报告以此为主。
- `Lab3_Traceroute.pcapng`：普通 Windows tracert 的 WLAN 迹线，共 10 帧；有 TUN 干扰，**不能把它当成真实逐跳路径**。保留作故障分析证据。
- `Lab3_Path_WLAN.pcapng`：已验证的源地址绑定 traceroute 迹线，共 76 帧：51 个 Echo Request，23 个 Time Exceeded，2 个最终 Echo Reply。TTL 1 至 17，每 TTL 恰好 3 个真实探测。
- `Lab3_source_test.pcapng`：前期两跳验证，非最终结果，不用在报告中。

`logs` 内有上述迹线对应 TSV，字段提取使用 `-E occurrence=f`，避免把 ICMP 引用包的内层 IP 当成外层字段。

## HTTP 字段与六题要点

- 本机 `172.31.165.86`，远端 `182.61.200.108`。
- HTTP GET 是第 4 帧：帧长 131 B，IP Total Length 117 B = 首部 20 B + TCP 20 B + HTTP 请求 77 B。IP 总长度不包含 Ethernet 首部。
- 第 4 帧 IPv4 首部：`45 00 00 75 ed c0 40 00 80 06 00 00 ac 1f a5 56 b6 3d c8 6c`。
- Version=4，IHL=5，首字节 0x45；首部长度 5×4=20 B，无 options；IHL 最大值 15，对应 60 B。
- DS=0，DSCP CS0，ECN Not-ECT。
- 本机 HTTP 发送报文 TTL 全部 128，8 位最大 255，因此初值不是最大值。**源地址绑定 traceroute 则故意设置 TTL 1–17**，不要混淆。
- Identification：本机方向依序 0xedbe、0xedbf、0xedc0……0xedc7；接收方向第 2 帧也为 0xedbe，随后第 5/6/7/8/9/14/17/18 帧分别为 0xb73c、0xb73e、0xb73f、0xb740、0xb741、0xb744、0xb745、0xb746。接收序列有跳号，**不能写成每包都加一，更不能断言两方向绝无重复**。ID 不是 TCP 连接号；同一原始数据报的分片依靠地址、Protocol、ID 等重组；对 atomic datagram，RFC 6864 不要求每包不同。
- 19 个目标连接包均 DF=1、MF=0、Offset=0。未分片的判断关键为 **MF=0 且 Offset=0**；DF=1 不是必要条件。MF=0 但 Offset>0 是最后一个分片。Offset 的单位是 8 B。
- 接收第 2 帧 TTL 45，其余接收包 TTL 40；**不要由 64−TTL 直接声称路径跳数，也不要断言服务器初值一定 64**。只能报告本次观测，并区分双向路由和测量协议。
- 发送包 checksum 在抓包处均 0x0000，GUI 提示可能由 IP checksum offload 引起；不能据此断言线上首部错误。
- 第 5 帧是接收 ACK：IP Total Length 40 B，TCP 20 B，checksum 0xcb73 [correct]。Ethernet 帧长 60 B，多出的 6 B 是链路填充；不属于 IP Total Length。
- 本次响应有重传/乱序和“Previous segment not captured”提示。curl 成功且 Follow TCP Stream 能看到 200 OK 和正文；报告应如实说明。不要将 TCP 分段/重传说成 IP 分片。

## 真实校验和计算 完整可直接使用

对象：`Lab3_HTTP_target.pcapng` 第 5 帧，服务器地址到本机地址，首部 20 B，非零实收校验和。

首部：`45 00 00 28 b7 3c 40 00 28 06 cb 73 b6 3d c8 6c ac 1f a5 56`。

| 序号 | 16 位字 | 字段 | 普通累计和 |
|---|---|---|---|
|1|0x4500|Version、IHL、DS|0x4500|
|2|0x0028|Total Length 40|0x4528|
|3|0xb73c|Identification|0xfc64|
|4|0x4000|Flags、Fragment Offset|0x13c64|
|5|0x2806|TTL 40、Protocol 6|0x1646a|
|6|0xcb73|实收 Header Checksum|0x22fdd|
|7|0xb63d|源地址前半 182.61|0x2e61a|
|8|0xc86c|源地址后半 200.108|0x3ae86|
|9|0xac1f|目的地址前半 172.31|0x45aa5|
|10|0xa556|目的地址后半 165.86|0x4fffb|

接收验证：普通和 0x4fffb → 高 16 位 0x0004 + 低 16 位 0xfffb = **0xffff**；再取反为 0x0000，验证通过。

生成复算：将第 6 字置零 → 普通和 0x43488 → 0x3488 + 0x0004 = 0x348c → 按位取反得到 **0xcb73**，与实收值、Wireshark [correct] 独立一致。

`analyze.py` 已从 pcapng 原始字节独立解析并断言上述结果，不是从截图抄数。

## 路径测量及 TUN 问题

普通命令 `tracert -4 -h 30 -w 700 182.61.200.108` 实际输出在 `logs\tracert.txt`：

```text
1  *  62 ms  *       182.61.200.108
2  33 ms 32 ms 33 ms 182.61.200.108
```

电脑启用 singbox_tun，系统默认 IPv4 路由经 `172.18.0.2`。上述普通 tracert 在 WLAN 抓包处发出的 Echo TTL 全是 128，而不是逐跳递增，所以“两跳到达”不能作为物理 Internet 路径。

**没有修改路由、VPN 或系统网络设置。** 采用微软文档提供的 `IcmpSendEcho2Ex` API，以 SourceAddress=`172.31.165.86` 发出逐 TTL、每跳三次的 ICMP 探测。脚本 `source_trace.py` 真实测量并保存输出，用 Wireshark WLAN 抓包交叉验证。此结果应明确称为“绑定 WLAN 源地址的 traceroute”，不要冒充 Windows tracert.exe 的输出。

最终路径在 `logs\source_trace.txt` 和 `logs\source_trace.json`：

|跳|三个 RTT ms|地址|组织说明|
|---|---|---|---|
|起点|—|172.31.165.86|本机 WLAN|
|1|* * *|未知|无回复|
|2|21 * *|10.100.4.1|私网路由，组织未知|
|3|* * *|未知|无回复|
|4|5 4 6|202.120.95.246|CERNET 地址登记|
|5|7 6 6|202.120.95.254|同上|
|6|* * *|未知|无回复|
|7|66 4 6|101.4.116.61|CERNET 地址登记|
|8|6 6 5|101.4.118.249|同上|
|9|* * *|未知|无回复|
|10|* 69 68|219.224.103.65|CERNET 地址登记|
|11|32 30 30|101.4.129.142|CERNET 地址登记|
|12|* * 33|182.61.255.32|百度地址登记|
|13|39 30 32|182.61.254.169|同上|
|14|* * *|未知|无回复|
|15|* * *|未知|无回复|
|16|* * *|未知|无回复|
|17|* 32 30|182.61.200.108|终点 百度服务器|

路径表已核对，最终绘图仍请直接读取 source_trace.json，避免人工抄写错位。

第 17 跳两次 Echo Reply；最终响应帧是 76，对应请求帧 75（ICMP seq 64）。第一个 Time Exceeded 为第 5 帧：外层源 IP=10.100.4.1、目标本机，ICMP Type=11、Code=0，内部引用源本机→目标服务器的 IP 首部及原始 Echo 请求。

全部路由器 PTR 均未解析成功，保存在 `logs\ptr.json`。公网组织标签来自 **APNIC 地址登记补充查询，不是反向域名、也不是物理位置证明**：

- `https://rdap.apnic.net/ip/202.120.95.246`：CERNET-CN，202.112.0.0–202.121.255.255。
- `https://rdap.apnic.net/ip/101.4.116.61`：BJR-CERNET，101.4.0.0–101.7.255.255。
- `https://rdap.apnic.net/ip/219.224.103.65`：BJR-CERNET，219.224.0.0–219.226.255.255。
- `https://rdap.apnic.net/ip/182.61.255.32`：Baidu，182.61.0.0–182.61.255.255。

原始 RDAP JSON 与摘要已保存在 `logs\rdap_*.json`、`logs\rdap_summary.json`。

星号只意味着在规定 900 ms 内没有收到对应回复，不证明该跳不存在、也不能仅据此断言路由器关闭 ICMP。ICMP 路径不保证与 TCP 路径或反向路径相同。

## 已准备的真实 Wireshark 截图

都在 `evidence`，以下文件可用于报告；其他 `obs_*` 只是中间观察，不要当作最终配图。

1. `01_capture_options.png`：WLAN、Ethernet、tcp port 80、混杂关闭。
2. `02_name_resolution.png`：Resolve network names 已勾选。建议裁去下部空白再放报告。
3. `04_outgoing_ipv4.png`：第 4 帧 HTTP GET 的 IPv4 全字段、首部原始字节、TTL 128、checksum 0x0000 卸载现象。
4. `05_incoming_checksum.png`：第 5 帧首部 20 B 高亮；0xcb73 [correct]、源/目的、原始字节，清晰局部截图。
5. `06_http_200_stream.png`：实际 Follow TCP Stream 窗口的 GET、200 OK、Content-Length 2381。
6. `07_id_ttl_fragmentation.png`：19 帧双向 Source/Destination、ID、TTL、IP Length、DF、MF、Offset 全列表。无其他桌面窗口干扰。
7. `08_path_ttl_probes.png`：TTL 1、2、3 的三次真实探测，正确过滤器排除了内层引用。`08_path_status.png` 是同一状态的底部计数，76 总帧、51 显示；两图可作为明确标注的局部截图配对，不能伪装成连续原始截图。
8. `09_icmp_time_exceeded.png`：ICMP Type 11、Code 0、路由器源地址和内部引用包。

尚可补一张终点回复图（可选）。当前 Wireshark 路径窗口中已输入 `frame.number >= 72`，**还没按 Enter 应用**。不要沿用旧坐标；重新观察窗口。

重要：`03_http_capture.png` 是捕获尚进行中的早期观察，`obs_filter_typed.png` 有聊天窗口遮挡，`08_path_ttl_probes.png` 现已覆盖为干净的正确版本。最终不要使用这些早期错误或遮挡画面。

## 本地技能与运行方式

请读 `.skills\cua-win\SKILL.md` 和 README。已学习并使用其 init、focus、clipboard type、真实截图方法。截图必须先设置 DPI，再检查目标窗口确实聚焦；不要造截图。

权威 Python：`C:\Users\18963\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

权威 Node：`C:\Users\18963\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe`

TShark：`C:\Program Files\Wireshark\tshark.exe`

示例（PowerShell，工作目录为根文件夹）：

```powershell
& 'C:\Users\18963\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '.skills\cua-win\scripts\cua.py' init
& 'C:\Users\18963\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '.skills\cua-win\scripts\cua.py' windows --process wireshark
& 'C:\Users\18963\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '_lab3_work\analyze.py'
```

Windows 沙盒内 TShark 只能看到 Loopback，Word COM 也会拒绝访问；真实网卡抓包、桌面控制、Word COM 需通过平台批准的非沙盒执行。之前自动审批已允许这些任务内操作。不要把沙盒权限错误理解成用户设备故障。

PowerShell 的 `InitializeDefaultDrives` 警告在沙盒中出现，但命令仍能读取文件。输出中文编码容易乱码；脚本首行使用 `sys.stdout.reconfigure(encoding='utf-8')`，中文路径最好放 `.py` 文件，不要通过复杂 `python -c` 传递。

`gui_action.py` 是基于现有 cua-win 的任务包装：验证 focus→一个动作→真实截图，支持观察、点击、剪贴板输入、按键、拖动和改变实验窗口尺寸。不要用于其他窗口，不要盲串点击。

## 已有脚本

- `inspect_sources.py`：PDF/Lab2 提取、参考渲染。
- `lab3_ops.py`：启动本次 GUI 抓包、固定 IP 的 curl、原生 tracert、环境日志。
- `source_trace.py`：Windows ICMP API 源地址绑定的真实 traceroute（**不改路由**）。已经完成，不必重复运行。
- `analyze.py`：从真实 pcapng 提取字段、独立核验 checksum、计数，并写 facts.json。
- `open_view.py`：打开本次指定抓包的 GUI 临时列设置。
- `fetch_rdap.py`：已完成的公开地址登记查询。
- `distill.py`：生成模板交接约束 artifact.md。
- **没有 `build_report.py`，没有最终 Lab3.docx。**

## 接续工作 建议顺序

1. 先读本交接、`facts.json`、`logs\source_trace.json` 与手册 Lab3，避免重复抓包。
2. 用 `template.docx` 副本生成最终报告，建议文件名 `10244602411_刘小凡_IPv4.docx`。学校模板 SHA-256 为 `100d6b4eb208559ef3a88bc0ea838a5e0945f056676604a9bd4beaf6c73ced7b`，原始学校 .doc 不动。
3. 绘制两张原创**示意图**：以第 4 帧为依据的 IPv4 字节布局；按 source_trace.json 的 17 跳路径图，包含未知跳和 APNIC 组织标注说明。明确图为绘制示意，不能称软件截图。
4. 按六部分模板写正文，逐条覆盖三项 Turn-in、六道题和校验和十字表。内容写成本次学生实验报告，不写“AI 制作”、不把学长数据复制过来。重点实测、异常排查、独立复核；不要只堆截图。
5. 引用 RFC 791（IPv4 格式/校验和）、RFC 6864（Identification 更新）、RFC 792（ICMP）和微软 IcmpSendEcho2Ex 文档；相应 URL 可用 RFC Editor 与 Microsoft Learn 官方页。正文引用要与实际结论对应。
6. 加入 8 张已准备的 Wireshark 图（及统计栏局部），每个图注说明证明什么、对应哪个 pcapng/帧号。截图已裁到目标区域；进一步裁剪只能去空白，不能改证据内容。
7. 原生 Word 渲染并检查每页：当前运行包不含 LibreOffice。已运行官方 `render_docx.py`，日志报 `soffice.exe was not found on PATH`；不使用用户系统 LibreOffice。已验证 Word COM 能成功转换 .doc、导出模板 PDF。可用 `Word.Application` 隐藏实例只读打开最终工作副本，`ExportAsFixedFormat(path,17)` 输出 QA PDF，然后用 bundled Python 的 fitz 逐页 PNG 渲染与目视检查。处理完在 finally 中关闭自己的 Word COM 实例，避免影响用户文档。
8. 复核图序、表头重复、表格跨页、字体替换、页脚页码、无占位红字、无多余空页、截图可读。保留原模板页边距及六部分结构。
9. 可交付最终 DOCX 和“实测数据与截图.zip”，包含 target HTTP、Path_WLAN、原生异常 trace、相关截图、验证脚本及必要日志；不要把无关背景 HTTP 或 QA 页图/PDF 当成交付内容。

## 无需再做的事

不必重新抓 HTTP、不必重新测路径、不必安装软件、不必改 VPN/路由。此次实测数据已经足以完成 Lab3。所有主要数字已在 facts.json 与原始 pcapng 中独立核对。
