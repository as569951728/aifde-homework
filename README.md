# FDE W01 作业：青禾会员运营助手

学员：陈昭文。整理日期：2026-10-22。采用课程标准产品，完成本地实操、正式沈总访谈和初步适配判断。

## 阅读顺序

1. [立项报告：阶段结论、依据与下一步](w01/docs/w01/project_assessment.md)
2. [适配判断 JSON：4 条诉求、16 条引用](w01/artifacts/w01/product_fit_gap.json)
3. [运行证据](w01/artifacts/w01/runtime_evidence.json)、[模型基线](w01/artifacts/w01/model_baseline.json)、[环境检查](w01/artifacts/w01/environment_check.json)
4. [正式访谈阅读版](w01/docs/w01/interviews/official/586a7063-87f3-5da5-b8ec-e2a52c3a18f1/transcript.md)及[原件核对记录](w01/docs/w01/interviews/official/586a7063-87f3-5da5-b8ec-e2a52c3a18f1/review.md)
5. [评估人工复核](w01/artifacts/w01/evaluation/20261022-promptfoo/review.md)与[学员回答及整理过程](w01/docs/w01/assessment_working_notes.md)

## 当前判断

有条件继续调研与试点方案设计；确认业务口径、可用数据、运营责任和投入范围后，再评审是否启动小范围试点。当前不承诺三个月复购止跌回升，也不承诺提升幅度或达成时间。

既有运行记录包括环境检查 9/9、正式行为验证 11/11、Promptfoo 自动评估 7/7。人工复核仍发现 M004 建议中“近两月无下单”的事实错误，M007 权益资格待核，均保留在作业证据中；自动通过不代表建议全部正确。青禾真实数据、建议采纳率、运营执行和复购效果尚未验证。

本周完成一次正式沈总访谈，原始 public/transcript JSON 和文件哈希保存在访谈目录。姓名、手机号等业务样例来自课程虚构教学材料；本仓库未接入真实客户数据。各环节工时未记录，报告据实保留。学员回答与助手的整理、补充分开记录。

## 工程与复核

[工程说明](w01/README.md)、[模型配置说明](w01/docs/model-configuration.md)、[依赖清单](w01/requirements.txt)和[预检记录](w01/docs/w01/submission_review.md)位于 `w01/`。文件保留包内的相对路径，全部源码、依赖说明和被引用证据一起提供。

工程来源为 `session-finalize-20261018`，材料版本 `w01-materials-0.2.4`。原始 `MANIFEST.json` 保留课程来源信息；W01 审阅快照的文件哈希见 [SUBMISSION_MANIFEST.json](w01/SUBMISSION_MANIFEST.json)。本仓库首页和 `.gitignore` 不属于该快照。

按工程说明在本地建立虚拟环境并安装依赖后，在 `w01/` 目录执行：

```sh
.venv/bin/python tools/check_product.py --root .
```

结构与哈希预检不需要模型密钥；重新运行真实模型场景时，由复核者自行配置凭证。此目录不包含 `.venv`、`.runtime`、`node_modules`、环境密钥文件或私有运行状态。

## 提交说明

课程页面：[W01 作业页面](https://u.geekbang.org/lesson/909?article=1024102)。根据学员粘贴的说明，先将作业托管到可阅读的仓库或在线文档，课程服务期内保持阅读权限，再把链接填入页面最下方的作业提交框。所贴说明没有给出截止时间。

本仓库用于提供 W01 作业的在线阅读和复核入口。仓库发布、课程表单提交和课程批改是独立状态；历史快照中的“尚未上传”反映快照生成时的状态，不代表后续提交回执。
