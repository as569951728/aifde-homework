# 隔离问答运行与结构审计

入口 `run_batch.py` 沿用课程 `Agent.answer_business_model`、`ContextModel` 和严格外层 `answer` JSON 校验；没有修改课程解析器，没有语义评分或语义／格式自动重试。模型固定为 `deepseek-flash` / `deepseek-json`，初次 8192 tokens / 180 秒；课程内置的**已确认 token 截断**扩容仍是 16384 tokens / 240 秒，最多一次。网络错误不自动恢复。每题 fresh Agent，无工具调用；最多两题并发。

## 冻结输入约定

`--batch` 必须指向 `answer-repair-20261107` 下的新隔离阶段目录，不可为 `support`。需要：

- `input/requests.json`：`{"requests":[{"id":"U01","question":"最终完整字符串"}]}`。请求条目只允许这两个字段。模型收到这条已冻结字符串，不会从元信息重新拼题或补材料；expected 不进入请求。
- `input/selected_questions.json`：`{"cases":[完整原题或控制题元信息]}`。原题元信息必须与 `input/original_questions.json` 的同 ID 对象完全相等。新增控制与 `input/controls.json` 的同 ID 对象完全相等，ID 不可与原题重合。
- `input/controls.json`：即使无控制也提供 `{"cases":[]}`。存在新增控制时，须同时冻结 `input/new_control_approval.json`：`{"approved":true,"controls_sha256":"文件SHA256"}`。
- 三轨均支持：`model_only`、`model_with_fixed_materials`、`model_with_source_context`。经独立审核的材料可直接嵌入题干，不能用 `fixed_materials` 为空推断输入缺失。
- `input/business_model.md`、`input/knowledge_prompt.txt`、`input/knowledge.json`：配置明确指向该 batch 的模型／提示快照；有效 extraction_run 沿用课程来源链。
- `input/protected.json`：工程根目录相对文件路径到 SHA256 的非空映射。
- `input/manifest.json`：`files` 为 batch 相对路径到 SHA256，必须覆盖 `input` 下所有文件，唯一排除 manifest 本身。存在 `case_ids` 时必须与 selected 顺序一致。

先执行只读输入检查（唯一写入为确定性的 `preflight.json`）：

```sh
.venv/bin/python -B artifacts/w03/answer-repair-20261107/support/run_batch.py --batch artifacts/w03/answer-repair-20261107/stage1 --check-only
```

check-only 不读钥匙串、不构造 Agent、不调用模型，亦不要求已有 gate。已有 preflight 只能在内容完全相同时复用；如修改冻结文件或 runner，应保留旧评审证据，另建批次或显式归档旧 preflight 后重新签审，不能把运行后补核记录为运行前通过。

## 独立执行门禁

门禁作者先核 input-review 的结构化 status、checks、正文结论一致，再签发 `batch/gate_acceptance.json`：

```json
{
  "approved": true,
  "failed_checks": [],
  "runner_sha256": "support/run_batch.py 的文件哈希",
  "manifest_sha256": "input/manifest.json 的文件哈希",
  "preflight_sha256": "preflight.json 的文件哈希",
  "input_review": "independent-review/input-review.json",
  "input_review_sha256": "该审核文件的文件哈希"
}
```

`input_review` 是 batch 相对路径，缺省为 `input-review.json`。runner 校验 gate 和精确文件哈希，不用关键词替独立 reviewer 解释审核正文。preflight 还绑定课程实现文件、当前原生读取的来源链及每题 messages / question 哈希。首次取 key 前和逐题执行前均重新核门禁。

```sh
.venv/bin/python -B artifacts/w03/answer-repair-20261107/support/run_batch.py --batch artifacts/w03/answer-repair-20261107/stage1
.venv/bin/python -B artifacts/w03/answer-repair-20261107/support/run_batch.py --batch artifacts/w03/answer-repair-20261107/stage1 --cases U01 U05
```

同题只执行一次。任何同 ID output（包括 started 标记、runner-error）或 runtime 已存在均拒绝覆盖；子集运行必须只选尚未开始的题。异常中止后的标记不自动清除。任何恢复需先保留旧证据，再另建获审批次，不能删除标记重抽样。

## 留档与审计

课程原生 run / request / response / attempts / snapshot 仍由课程记录器写入 `artifacts/w02/knowledge_runs/RUN-…`；这是原入口的固定记录位置，不表示修改 W02 正式基线。batch 下写 `runtime/`、每题 `output/*.started.json`、`output/*.json` 和汇总 `run_index.json`。输出记录引用并哈希全部原生文件；原生 `check_run` 失败也保存 result、run 内容、原生错误与 raw 路径，`actual_answer` 留空而不重新解析或编造答案。

```sh
.venv/bin/python -B artifacts/w03/answer-repair-20261107/support/audit_results.py --batch artifacts/w03/answer-repair-20261107/stage1
```

审计逐一比对实际原生请求、每个 HTTP attempt 的 messages、冻结完整 question、模型／提示、无 expected／tools、token／timeout、原生输出文件哈希及 index。原生 failed run 可以通过结构审计，但不计为成功答案；check_run 本身失败会记审计失败并保留原证据。审计不评语义、不取 key、不调用模型。部分审计可用 `--cases` 和新的 `--output protocol_audit-partial.json`；不同内容不得覆盖旧审计。

仅支持本机 macOS 已有钥匙串账户；key 只留内存，无打印或落盘。SSL 使用 certifi 且保留 TLS 校验。CLI 的异常输出只含代码和类型，原生公开响应及错误保存在原生证据文件。
