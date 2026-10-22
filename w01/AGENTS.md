# 实操工程运行约定

- 使用本工程 `.venv/bin/python`；课程材料中的原工程保留作参考，不覆盖用户运行记录。
- 2026-10-22 本机已复现 Python 默认可信证书缺失导致的 `MODEL_NETWORK_ERROR`。项目 certifi 证书库与系统 truststore 均通过真实 TLS 检查。此机启动产品时，在项目根目录、用户配置模型的同一终端设置 `export SSL_CERT_FILE="$(.venv/bin/python -m certifi)"`，再启动产品。
- 保持证书和主机名校验开启；不使用 `CERT_NONE`、未验证 SSLContext 或关闭 HTTPS 校验来处理网络错误。不修改系统代理或系统证书来代替定位原因。
- 用户终端与助手进程的环境变量独立。密钥不进入聊天、公开日志、学习记录或提交包。
- 首次失败记录及诊断已归档到 `artifacts/w01/diagnostics/20261022-model-network-aed40aeb/`。无密钥的 HTTP 401 只证明网络和 TLS 可达，真实模型与业务结果仍需重试核验。
- 网页“撤销刚才的标签动作”走 `/api/undo`，直接调用账本，不生成新的 Agent run JSON。复核撤销要读取动作账本和实际标签库（必要时只读 HTTP 查询），关联撤销前快照；不能因最新 runs 文件仍显示 applied 就判定撤销失败。不要为了取得证据重复执行用户的确认或撤销。
- 课程锁定 Promptfoo 0.122.2；本机已安装并验证 `npx --offline --yes promptfoo@0.122.2 --version` 可用。后续评估可优先用此缓存入口，`--offline` 只限制 npx 取包，不禁止 Python provider 调用真实模型。首次依赖下载超时的诊断保存在 `artifacts/w01/diagnostics/20261022-promptfoo-setup/`；需要调整下载网络时只在该安装进程使用已核实代理，不改全局配置或关闭 TLS 校验。
