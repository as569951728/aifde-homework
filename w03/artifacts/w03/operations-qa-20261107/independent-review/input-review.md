# 经营目标与运营协作七题输入门禁

结构化状态：`passed`；批准运行：`true`；失败项：无。

批准按冻结输入执行这7题各一次；真实输出后再独立判读。

共 49 项检查，49 项通过；评审没有模型调用。

范围：U01/U04/F03/F04/F05/F06/F09，全部 model_only，仅冻结正文、既有提示及单题原文，无额外来源/fixture/预期。

模型、提示、原题、预期与前批逐字相同；运行器相对原 model_only runner 仅更换隔离目录。原生 GUARD/模型参数/expected 空值策略不变，逐题实际 prepare 与 preflight 相同，12 份保护文件保持。

来源判据先保存再对照作者预期，七题一致；正文已承载核心所需内容。单卡日期模板不适用本组；不要求个人 Excel 或 FDE 管理进入回答。

每题只执行一次，保留全部结果，不语义重试。无答传输恢复另审，不把失败覆盖。DQ10/P09/B05原失分不变。

逐项检查：

- PASS — scope_exact_seven
- PASS — frozen_input/business_model.md
- PASS — frozen_input/knowledge.json
- PASS — frozen_input/knowledge_prompt.txt
- PASS — frozen_input/original_questions.json
- PASS — frozen_input/protected.json
- PASS — frozen_input/reviewer_expectations.json
- PASS — frozen_input/selected_questions.json
- PASS — protected_docs/w03/business_model.md
- PASS — protected_docs/w03/interview_notes.md
- PASS — protected_customer/w02/knowledge.json
- PASS — protected_customer/w02/knowledge_prompt.txt
- PASS — protected_customer/w02/workflow.json
- PASS — protected_customer/w02/extraction.json
- PASS — protected_customer/w02/skills/extract-business/SKILL.md
- PASS — protected_artifacts/w02/workflows/WF-8d2ebffec9d94a25bc164ae489fe13a0/session.json
- PASS — protected_artifacts/w03/model-draft-20261106/draft-03/business_model.md
- PASS — protected_docs/w03/metric_decisions.md
- PASS — protected_docs/w03/sow.md
- PASS — protected_customer/w03/tests.json
- PASS — unchanged_business_model.md
- PASS — unchanged_knowledge_prompt.txt
- PASS — unchanged_original_questions.json
- PASS — unchanged_reviewer_expectations.json
- PASS — model_hash
- PASS — prompt_hash
- PASS — criteria_saved_before_expectations
- PASS — expectation_alignment
- PASS — original_question_hash
- PASS — runner_only_isolated_runtime_changed
- PASS — runner_frozen_hash
- PASS — audit_hash
- PASS — config_only_frozen_paths
- PASS — actual_prepare_equals_frozen_preflight
- PASS — no_previous_calls
- PASS — selected_matches_source_first_question_objects
- PASS — all_model_only_no_fixture
- PASS — U01_exact_single_question_context
- PASS — U04_exact_single_question_context
- PASS — F03_exact_single_question_context
- PASS — F04_exact_single_question_context
- PASS — F05_exact_single_question_context
- PASS — F06_exact_single_question_context
- PASS — F09_exact_single_question_context
- PASS — runtime_policy_unchanged
- PASS — expected_empty_at_call
- PASS — no_semantic_retry
- PASS — model_supports_core_seven_criteria
- PASS — date_template_inapplicable_to_seven
