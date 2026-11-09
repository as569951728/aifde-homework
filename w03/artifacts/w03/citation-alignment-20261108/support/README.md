# 本轮隔离运行准备

输入已冻结，机械输入核验通过；尚无live执行批准。使用现有 .venv，无初始化、无密钥读取、无模型调用。

六题为 U05、E01、TRACECTRL01、CTRL01、U01、P01：原题4道、控制2道。其中CTRL01采用有效W02陈姐原访谈，是原文控制；TRACECTRL01才是人工合成迁移控制。控制题不等于合成数据，二者均不增加原82题覆盖。

原题元信息、完整question/fixture/附加材料、原期望、全部6个控制元信息与既有批准绑定均保留。正文是11月8日澄清候选，仅隔离回答提示改变。runner/auditor与上一轮原字节相同；新脚本仅准备与机械检查，不修改课程实现。

核查文件：
- qa-01/input/manifest.json：全部输入冻结清单。
- qa-01/preflight.json：课程check-only输出，零模型调用。
- input-integrity/mechanical-check.json 与 .md：同结论，approved仅代表机械输入检查，execution_approved=false。
- input-integrity/baseline_snapshot.json：270个既有文件保护快照，含旧澄清整目录、旧修复completion/ledger/评审、12保护及旧proposal。
- input-integrity/preparation.json：来源与准备记录。

下一门禁必须由独立评审签发qa-01/gate_acceptance.json，至少绑定runner_sha256、manifest_sha256、preflight_sha256、input_review及input_review_sha256，并确认approved=true/failed_checks为空且审核正文一致。建议input-review同时绑定机械核验及baseline_snapshot的哈希。本目录没有签发该执行门禁。

获准后由主控使用：
.venv/bin/python -B artifacts/w03/citation-alignment-20261108/support/run_batch.py --batch artifacts/w03/citation-alignment-20261108/qa-01

每题一次，最多6个新run；确认length仅按原策略扩容一次。语义、格式及网络失败全部保留，本轮不另行恢复或抽样。
