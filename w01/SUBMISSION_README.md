# W01 作业审阅包

本地整理日期：2026-10-22。此包尚未上传课程平台，提交入口和截止时间按班期配置。

先阅读 docs/w01/project_assessment.md 的阶段结论及第 4–5 节；学员原答与导师补充分开保存在 docs/w01/assessment_working_notes.md。

五份正式文件：
- artifacts/w01/environment_check.json
- artifacts/w01/product_fit_gap.json
- artifacts/w01/model_baseline.json
- artifacts/w01/runtime_evidence.json
- docs/w01/project_assessment.md

适配填写稿、正式访谈原件、运行与评估证据、课程来源、源码、依赖说明均保留相对路径。课程原始 MANIFEST.json 仅是来源记录；本包实际文件哈希见 SUBMISSION_MANIFEST.json。

复核时先按 README.md 安装依赖，再在此工程根目录执行：

    .venv/bin/python tools/check_product.py --root .

结构与证据哈希检查不需要模型密钥。现场行为重跑需由操作者自行设置模型凭证并启动标签服务，按工程 README、evals/README.md 和 docs/model-configuration.md 操作；本包不携带密钥、虚拟环境、私有 checkpoint 或数据库。重跑请用单独副本，保留本包基线。

已知限制：自动评估通过后仍有 M004 建议事实错误；M007 权益资格待核。青禾数据、采纳率、运营试点和复购效果均未验证。分项投入耗时未记录。不要把 checker 通过理解为课程评分通过、客户验收或已提交。

历史原始记录中的绝对路径只用于溯源；当前可携带评估报告为 artifacts/w01/promptfoo-results.json，trace 已另存。原件为保持证据完整未重写。
