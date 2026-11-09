"""Close B1 only after complete execution and independent approval; no model calls."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
B = Path(__file__).resolve().parent
REL = B.relative_to(ROOT).as_posix()


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def replace(path, old, new):
    text = path.read_text()
    assert old in text, (path, old[:70])
    path.write_text(text.replace(old, new, 1))


report = read(B / "test-v2/metric_test_report.json")
review = read(B / "independent/final-review-v2.json")
assert report["complete"] and report["passed"] == report["total"] == 15
assert review["approved_for_batch_closeout"] and not review["failed_checks"]
for path, digest in review["evidence_sha256"].items():
    assert sha(ROOT / path) == digest, path
assert read(B / "batch-controls-v2.json")["status"] == "passed"
assert read(B / "judge-injections-v2.json")["status"] == "passed"
assert not (B / "completion.json").exists(), "Closeout is one-time; preserve evidence"
binding = read(B / "version-binding-v2.json")
tests = read(ROOT / "customer/w03/tests.json")
assert tests == read(B / "independent/tests-all.json")
original = read(B / "before/customer/w03/tests.json")
assert [c for c in tests if c["id"].startswith("NS")] == original
assert sha(B / "execution-tests-v2.json") == binding["execution_tests_sha256"]
freeze = read(B / "independent/expected-freeze.json")
for path, digest in freeze["source_sha256"].items():
    assert sha(ROOT / path) == digest, path
for path, digest in freeze["expected_artifact_sha256"].items():
    assert sha(B / "independent" / path) == digest, path
assert sha(B / "before/customer/w03/test-plans/metric_cases.json") == freeze["source_sha256"]["customer/w03/test-plans/metric_cases.json"]

# Adopt the exact reviewed and exercised scope fix, retaining original relative paths.
scope_review = read(B / "independent/scope-config-review.json")
assert scope_review["approved_to_regenerate"] and not scope_review["failed_checks"]
adoption = B / "candidate-build-for-adoption.json"
assert sha(adoption) == scope_review["adoption_candidate_sha256"]
old_config = read(B / "before/customer/w03/build.json")
new_config = read(adoption)
check_config = copy.deepcopy(new_config)
check_config["scope"]["statistics_unit"] = old_config["scope"]["statistics_unit"]
assert check_config == old_config
protected = read(B / "protected.json")
assert all(sha(ROOT / p) == h for p, h in protected.items()), "Unexpected pre-adoption change"
(ROOT / "customer/w03/build.json").write_bytes(adoption.read_bytes())
changed = [p for p, h in protected.items() if sha(ROOT / p) != h]
assert changed == ["customer/w03/build.json"]

# Count real saved attempts; do not infer calls from test count alone.
trace_files = [B / "build-v1/trace.json", B / "build-v2/trace.json"]
trace_files += sorted((B / "test-v1/traces").glob("*/*-trace.json"))
trace_files += sorted((B / "test-v2/traces").glob("*/*-trace.json"))
calls = []
for p in trace_files:
    trace = read(p)
    calls.append({"trace": p.relative_to(ROOT).as_posix(),
                  "http_attempts": len(trace["call"]["attempts"])})
reports = [read(B / f"test-v{i}/metric_test_report.json") for i in [1, 2]]
audit = {"logical_model_calls": len(calls),
         "http_attempts": sum(c["http_attempts"] for c in calls),
         "natural_language_test_executions": sum(r["total"] for r in reports),
         "successful_sql_executions": sum(c["actual"]["status"] == "ok" for r in reports for c in r["cases"]),
         "build_runs": 2, "calls": calls,
         "protected_files": len(protected), "unchanged_protected_files": len(protected) - 1,
         "approved_protected_change": {"file": "customer/w03/build.json", "field": "scope.statistics_unit",
                                        "before_sha256": protected["customer/w03/build.json"],
                                        "after_sha256": sha(ROOT / "customer/w03/build.json")},
         "original_net_8_cases_unchanged": True,
         "W02_and_business_model_unchanged": True, "product_binding_unchanged": True,
         "scope": "Two B1 builds and two same15 runs; controls are offline copies, not extra queries"}
save(B / "execution-audit.json", audit)

evidence = {"report": f"{REL}/test-v2/metric_test_report.json",
            "review": f"{REL}/independent/final-review-v2.json",
            "expected": f"{REL}/independent/tests-all.json",
            "freeze": f"{REL}/independent/expected-freeze.json",
            "library": f"{REL}/library-v2", "project": binding["project"]}
completion = {"status": "B1_completed_small_scope", "metrics": ["payment_cents", "refund_cents", "net_sales_cents", "gross_cents", "discount_cents"],
              "small_cases_passed": 15, "small_cases_total": 15, "explanations_passed": 15,
              "new_multi_metric_questions": 7, "unchanged_net_regression_questions": 8,
              "auxiliary_identity_rows": 14, "scale_run": False,
              "v1": {"numeric_passed": 15, "explanation_passed": 11,
                     "failed_explanations": ["B1-R01", "B1-R02", "NS02-july-transaction-store", "NS04-partial-refund-day"]},
              "config_scope_fix_adopted": True, "skill_and_judge_changed": False,
              "evidence": evidence, "versions": binding,
              "next_batch": "B2 seven order-count metrics; cumulative build scope 12",
              "unvalidated": ["scale", "remaining33 metrics", "remaining dimension behaviors", "unseen phrasings", "production", "acceptance", "submission"],
              "attribution": "导师执行与独立Agent核查，不登记本人独立作答或客户验收"}

# Existing machine register: preserve every untouched metric and the original plan.
reg_path = ROOT / "customer/w03/metric_register.json"
reg = read(reg_path)
reg["version"] = "w03-metric-register-v2"
reg["execution_review"] = evidence["review"]
reg["current_library"] = evidence["library"]
for batch in reg["batches"]:
    if batch["id"] == "B1":
        batch.update(status="completed_small", already_small_passed=completion["metrics"], result_reference=f"{REL}/completion.json")
    elif batch["id"] == "B2":
        batch["status"] = "next_batch"
for m in reg["metrics"]:
    if m["batch"] != "B1":
        continue
    m["previous_status"] = copy.deepcopy(m)
    m.update(definition_status="已核字段、粒度、日期、单位与范围", build_status="B1 build-v2/library-v2已构建并加载",
             test_design_status="7道多指标测试及辅助关系已完成；原8题净额回归保留",
             expected_status="原CSV独立核算并于构建/查询前冻结", small_status="本批7/7多指标题通过" if m["id"] != "net_sales_cents" else "7道多指标+8道原题，15/15通过",
             explanation_status="相应成功解释通过；本批15题完整独立审查通过",
             current_adopted_library_scope="B1五项金额小样本库", known_pending="规模、其他维度行为及未见问法待后续；本批无阻断业务缺口",
             result_reference=f"{REL}/completion.json", expected_reference=evidence["expected"], review_reference=evidence["review"], catalog_sha256=binding["catalog_sha256"])
reg["summary"].update(metrics_with_frozen_existing_tests=5, metrics_with_small_pass=5,
                       existing_real_cases=15, original_net_regression_cases=8, new_design_entries=53,
                       new_design_query_entries_executed=7, new_design_auxiliary_entries_checked=1,
                       new_design_entries_not_run=45, new_model_calls=audit["logical_model_calls"],
                       new_queries=audit["successful_sql_executions"], new_http_attempts=audit["http_attempts"],
                       last_batch="B1", next_batch="B2", metrics_with_scale_pass=0)
save(reg_path, reg)

plan_path = ROOT / "customer/w03/test-plans/metric_cases.json"
plan = read(plan_path)
plan["version"] = "w03-metric-test-plan-v4"
plan["status"] = "B1_frozen_executed_and_reviewed_remaining_design_only"
plan["rule"] = "B1七题及净额原八题已有独立冻结期望和本批结果；B1-A01是已核辅助关系，非查询。其余45条新增设计仍不可直接运行，不填假0/null。参数化设计不冒充多个已执行子例。"
test_map = {c["id"]: c for c in tests}
for c in plan["cases"]:
    if c["id"] in test_map:
        t = test_map[c["id"]]
        c["previous_evidence"] = {k: v for k, v in c.items() if k in ["state", "execution_state", "expected_reference", "result_reference", "review_reference", "catalog_sha256"]}
        c.update(state="passed_on_B1_library_v2", executable=True, expected_state="independently_frozen_before_build_and_query", execution_state="passed_and_explanation_reviewed",
                 question_or_fixture=t["question"], execution_question=t["question"],
                 expected_reference=evidence["expected"] + "#" + c["id"], result_reference=evidence["report"] + "#" + c["id"],
                 review_reference=evidence["review"], data_version=binding["data_version"], catalog_sha256=binding["catalog_sha256"])
        if c["id"].startswith("B1-"):
            c["data_state"] = "原small CSV，逐单台账已核；适用限制见本批结果，不声称所有错误均可由数值区分"
        else:
            c["expected_behavior"] = "沿用原8题冻结期望，在B1新库完成回归；旧库原证据保留。"
    elif c["id"] == "B1-A01":
        c.update(state="auxiliary_checked", executable=False, execution_state="checked_14_rows_after_independent_values",
                 expected_state="identities_not_a_replacement_for_independent_expected", result_reference=f"{REL}/batch-controls-v2.json#B1_A01")
for dim in plan["common_design"]["dimensions"]:
    if dim["id"] == "store":
        dim.update(status="B1_multi_metric_grouping_passed", evidence="B1-D01; NS02-july-transaction-store")
    elif dim["id"] == "order__channel":
        dim.update(status="B1_eq_filter_and_AND_passed", evidence="B1-F01; NS03-aug-mini-program")
    elif dim["id"] == "store__region":
        dim.update(status="B1_eq_filter_only_passed_grouping_not_run", evidence="B1-F01")
    elif dim["id"] == "metric_time__day":
        dim.update(status="B1_grouping_passed", evidence="B1-D02")
plan["common_design"]["B1_current_evidence"] = {
    "batch_controls": f"{REL}/batch-controls-v2.json", "real_copy_controls": f"{REL}/judge-injections-v2.json",
    "independent_preflight_synthetic_judge_checks": f"{REL}/independent/judge-multi-metric-selfcheck.json",
    "note": "判定器合成正反对照、真实结果副本注入、真实业务问数三类分开；不泛化为后续比率/月报已通过。"}
controls = {
    "J01": ("passed_real_copy", "wrong_date"), "J02": ("passed_real_copy", "wrong_metric"),
    "J03": ("passed_real_copy", "extra_filter"), "J04": ("passed_real_copy", "wrong_unit"),
    "J05": ("partial_one_cent_checked_large_integer_not_rerun", "wrong_value_one_cent"),
    "J06": ("passed_real_copy", "error_with_original_number"), "J07": ("passed_real_copy", "wrong_data_version"),
    "J08": ("passed_real_copy", "missing_group"), "J09": ("passed_real_copy", "duplicate_group"),
    "J10": ("passed_explicit_synthetic_null_control_not_real_null_query", "null_replaced_by_zero"),
    "J15": ("passed_real_copy", "correct_original"), "J16": ("passed_real_copy", "row_order_only"),
    "J17": ("passed_real_copy", "column_order_only")}
for c in plan["common_design"]["judge_controls"]:
    if c["id"] in controls:
        c["status"], case_id = controls[c["id"]]
        c["evidence"] = f"{REL}/judge-injections-v2.json#{case_id}"
    elif c["id"] in {"J12", "J13", "J18"}:
        c["status"] = {"J12": "passed_synthetic_swapped_identities", "J13": "partial_numeric_string_checked_other_types_not_rerun", "J18": "partial_AND_order_checked_in_set_not_rerun"}[c["id"]]
        c["evidence"] = f"{REL}/independent/judge-multi-metric-selfcheck.json"
save(plan_path, plan)

# The two user-facing registers keep the original detailed design; only B1/current state changes.
path = ROOT / "docs/w03/指标核对与测试登记.md"
replace(path, "当前：**38项已登记；38项均有测试场景设计；仅净销售额具备已跑的8例；其余37项尚未冻结数值期望、未构建/问数；规模0/38。** 本轮新增模型调用/查询为0。",
        "当前：**B1五项金额已构建并通过小样本数值与解释核查：5/38项（约13%）；其余33项待按批执行，规模0/38。** 本批15题＝7道多指标＋8道净额回归；[结果与失败修复记录](../../" + REL + "/结果速览.md)。")
replace(path, "不代表新增指标已核数。", "设计审批与实际执行分开；当前B1执行证据见上方结果。")
replace(path, "| B1 | 订单金额 | 5 | 下一批：新增4项金额，同时回归净销售额 |", "| B1 | 订单金额 | 5 | 小样本与解释通过，已完成本批 |")
replace(path, "| B2 | 订单数量 | 7 | 排队，依赖核定后整批推进 |", "| B2 | 订单数量 | 7 | 下一批；累计金额5项＋订单数7项构建，回归B1 |")
text = path.read_text()
lines = text.splitlines()
for i, line in enumerate(lines):
    for m in reg["metrics"]:
        if m["batch"] == "B1" and line.startswith("| " + m["name"] + " `"):
            coverage = "15/15含原8题回归" if m["id"] == "net_sales_cents" else "7/7多指标题"
            lines[i] = f"| {m['name']} `{m['id']}` | 01，另核02/05 | 已核 | B1 v2已构建/加载 | 独立期望已冻结 | {coverage}通过，解释已审 | 未跑 |"
path.write_text("\n".join(lines) + "\n")
replace(path, "不是运行tests.json；新期望未计算，不填假0或null。", "保留全部设计与状态；B1已提升为原生测试，其余新期望未计算，不填假0或null。")
replace(path, "[已具备的原生8例]", "[当前原生15例（含未改的原8例）]")
replace(path, "当前边界：12维度已结构可达，仅成交门店分组与渠道eq筛选有首项真实用例；其余维度行为待测。", "当前边界：12维度结构可达；B1已测成交门店/逐日分组、渠道eq及成交地区eq的AND筛选。地区分组及其他维度行为仍待测，不计12维度全部通过。")

path = ROOT / "docs/w03/指标模型测试集设计.md"
replace(path, "本文新条目均未计算期望、未运行，不能直接作为原生tests.json。", "B1七道新问数已冻结并运行，B1-A01已核辅助关系；其余45条新设计仍未计算期望/运行，不能直接作为原生tests.json。")
replace(path, "现在状态是设计，金额期望待独立核算。", "本批独立期望已冻结：实付5000、退款5000、净额0、原价5000、优惠0（分），真实结果一致；其全退订单原优惠本来为0，不能凭此例单独证明所有优惠退款处理。8月31日含原优惠100分的全退单已被逐日和整月测试覆盖。")
replace(path, "净销售额NS01—NS08在记录的small/library-v2上通过；6份成功回答、2份非成功理由已独立审。只覆盖原题、原库和对应范围，不覆盖下方新设计。", "净销售额NS01—NS08在首项库通过，原证据保留；现同8题已在B1 library-v2回归通过并独立审解释。连同7道新多指标题，本批15/15通过；[本批记录](../../" + REL + "/结果速览.md)。不覆盖后续45条新设计。")
replace(path, "| 原库已通过 |", "| B1新库回归通过；原记录保留 |")
# All eight table statuses use the same phrase; the first was replaced above.
path.write_text(path.read_text().replace("| 原库已通过 |", "| B1新库回归通过；原记录保留 |"))
old = "本批指标：`payment_cents`、`refund_cents`、`net_sales_cents`、`gross_cents`、`discount_cents`。每项来源、独立核算方法和用例映射见机器登记账；下表未写执行结果，统一为**设计／待核字段、样本及独立期望**。"
new = "本批五项金额已完成定义核查、独立冻结、构建和真实验证。下表保留原设计简写，实际运行使用完整独立问句，见[原生15题](../../customer/w03/tests.json)。**B1-N01/R01/R02/D01/F01/Z01/D02共7题通过，A01为14行辅助关系核对，不另算问数题。**"
replace(path, old, new)

# Existing continuity pages: insert one short current entry and explicitly demote old stop points.
current = ("**B1金额批次完成（2026-11-08，当前）：** 五项金额在small合成数据上完成15题：7道多指标＋8道原净额回归，数值与完整解释均通过独立审核。首轮数值15/15、解释11/15的4条错误保留；有源修正build.json的全局单位说明后重建并复验，Skill v0.1.2、judge、独立业务期望未改。现小样本5/38（约13%），规模0/38；后续45条新设计未运行。\n\n"
           "**下一批：B2订单数量7项。** 按创建、支付、有效、取消、退款、部分退、全退准备独立期望与边界；默认累计B1五项一次构建12项，并回归已通过测试。无需重开建模或重复访谈，只有现有来源不能解决的业务决策交本人。产品聊天绑定未切换；W02和W03业务模型未改。导师执行不等于本人独立掌握或提交。\n\n")
for rel, link in [("AGENTS.md", f"{REL}/结果速览.md"),
                  ("开始这里.md", f"{REL}/结果速览.md"),
                  ("docs/w03/test_design.md", f"../../{REL}/结果速览.md"),
                  ("../W03-学习会话接续.md", f"实操工程/{REL}/结果速览.md")]:
    p = ROOT / rel
    text = p.read_text()
    text = text.replace("**指标分批推进（2026-11-08，当前）：**", "**指标分批推进（2026-11-08，历史计划）：**", 1)
    first, rest = text.split("\n", 1)
    p.write_text(first + "\n\n" + current + "本批证据：[结果速览](" + link + ")。下方旧停点按其记录时点保留。\n" + rest)

path = ROOT / "docs/w03/metric_decisions.md"
replace(path, "下一批B1处理五项金额（含净额回归），不再逐项停点。", "B1五项金额已完成，下一批B2七项订单数量；不再逐项停点。")
first, rest = path.read_text().split("\n", 1)
path.write_text(first + "\n\n## B1五项金额核定（2026-11-08，当前）\n\n"
               "本批共用orders的一订单粒度、ordered_at原订单日、paid集合与整数分。实付＝paid；退款＝累计refund；净额＝paid−refund；支付订单原价＝gross；优惠＝gross−paid。取消贡献0，全退仍保留原实付/原价/优惠；无月末资格或整月附加限制。式中paid为paid_cents，条件status='paid'另行判断。\n\n"
               "依据与字段映射见[本批口径](../../" + REL + "/口径与本批检查.md)。15题真实结果、解释和原失败见[结果速览](../../" + REL + "/结果速览.md)。build.json已将无条件账户单位改为按指标区分；不改业务定义或期望，也不能据一次回归证明错误唯一原因或长期稳定。\n\n"
               "目前没有阻断B1的业务缺口。不能验证的范围：生产记录、现金退款日、规模数据、尚未测试维度/问法。以下保留首项核定历史。\n" + rest)

path = ROOT / "../W03-学习笔记.md"
first, rest = path.read_text().split("\n", 1)
path.write_text(first + "\n\n## 2026-11-08 实操概念速记：指标单位与完整验证\n\n"
               "含义：每个指标有自己的统计对象和单位。青禾实付/退款/净额等金额按订单贡献累计，以分保存；账户数才按CRM账户计数，不能把客户统一的“账户”说明套给金额。\n\n"
               "本批例子：8月实付119050分−退款18750分＝净额100300分；原价124250分−实付119050分＝优惠5200分。易混点：这些恒等式成立，仍不能替代逐单独立期望；数值正确，也不能豁免解释把金额说成账户数。使用时先核来源/字段/单位，再分别查数值与原回答。记忆要求：能区分口径、实现、独立期望、实际结果和解释五层证据；本次不登记本人已独立掌握。\n\n"
               "来源：本周01订单日报、02财务邮件、05字典及本批实际运行/独立审核。B1小样本5/38、15题通过；首轮4条解释失败保留。详见[结果速览](实操工程/" + REL + "/结果速览.md)。下一批B2七项订单数。\n" + rest)
save(B / "completion.json", completion)
save(B / "bookkeeping-update.json", {
    "status": "source_evidence_preserved_current_status_updated_after_review",
    "frozen_design": {"path": "customer/w03/test-plans/metric_cases.json",
                      "before_sha256": freeze["source_sha256"]["customer/w03/test-plans/metric_cases.json"],
                      "snapshot": f"{REL}/before/customer/w03/test-plans/metric_cases.json",
                      "current_sha256": sha(plan_path),
                      "change": "B1 execution and evidence links; remaining designs untouched"},
    "expected_artifacts_unchanged": True,
    "note": "Independent review is of frozen execution inputs/results. Later progress bookkeeping is not retroactively claimed as part of the frozen source version."})
save(B / "progress.json", {"stage": "B1_completed_small", "completion": f"{REL}/completion.json", "next_batch": "B2", "formal_config_adopted": True})
print(json.dumps({"completed": "B1", "metrics_small": "5/38", "cases": "15/15", "next": "B2", "audit": {k: audit[k] for k in ["logical_model_calls", "http_attempts", "successful_sql_executions"]}}, ensure_ascii=False))
