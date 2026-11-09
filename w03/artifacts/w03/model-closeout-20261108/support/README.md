# 七题隔离运行准备

输入已冻结、check-only通过，尚待独立来源/输入门禁。125项机械检查通过，0模型调用、0密钥读取；未初始化环境。详见`../input-integrity/mechanical-check.json`与同名Markdown。

- 顺序：U05、U01、P01、E01、TRACECTRL01、CTRL01、E03。5原题+2控制；CTRL01为真实W02陈姐访谈控制，TRACECTRL01为合成控制。
- 全部最终question（包括fixture与逐题材料）逐字复用Stage5原版，E03未裁剪或重拼；完整六个controls元信息及原批准保留。
- 正文严格63513，评审预期严格f799（不发送模型），提示严格961464。原runner/auditor原字节复用，知识配置只改隔离路径。
- 92项定向hash保护包含12正式保护、旧proposal/session、历史结果/评审链、七题最近可比原答与原生顶层证据；只保存hash，不复制历史目录。保护项全部由运行器再次强校验。
- 每题一次，共最多7run。原生确认length时允许8192/180秒扩至16384/240秒一次；语义、格式、网络失败不重试。严格外层answer JSON，不修解析器或人工替换答案。

## 命令

以下命令的工作目录均为`/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程`。准备脚本已执行一次，不要再执行prepare_inputs或check_inputs以覆盖记录；原runner的check-only可核对相同冻结输入。

```sh
.venv/bin/python -B artifacts/w03/model-closeout-20261108/support/run_batch.py --batch artifacts/w03/model-closeout-20261108/qa-01 --check-only
```

独立评审签门禁后，由主控仅执行一次：

```sh
.venv/bin/python -B artifacts/w03/model-closeout-20261108/support/run_batch.py --batch artifacts/w03/model-closeout-20261108/qa-01
```

完成后作原生记录/实际输入结构审计（不评分）：

```sh
.venv/bin/python -B artifacts/w03/model-closeout-20261108/support/audit_results.py --batch artifacts/w03/model-closeout-20261108/qa-01
```

## 待签门禁

目标：`qa-01/gate_acceptance.json`。独立评审先写输入审阅JSON/正文，核status、failed_checks/checks及文字结论一致，然后签发以下字段。示例为格式说明，**不是已签批准**，input_review_sha256须取实际审阅文件hash。

```json
{
  "approved": true,
  "failed_checks": [],
  "runner_sha256": "a594b197a85587c26b0686d21c93d9e7bfb421edc13c12827930176d223040d8",
  "manifest_sha256": "c4cd4d6e96ab63ab8a7813235a2f6e50602c143f96c6e416226299190a171557",
  "preflight_sha256": "77b3acffc11d62e3fa07a7e1e39754cd4863fad56ab924abc7c5b0fbfebd4a88",
  "input_review": "independent-review/input-review.json",
  "input_review_sha256": "填写实际受审文件的SHA256"
}
```

input_review路径相对qa-01；不得移到batch外。机械核验approved只指输入完整性，execution_approved=false，不能替代语义门禁。runner会拒绝已有该题output/runtime，保留失败及全部原生证据。
