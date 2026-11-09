"""Adopt passed B2 tests and update existing registers only after independent approval."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
B = Path(__file__).resolve().parent
REL = B.relative_to(ROOT).as_posix()
rd = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def save(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")

review = rd(B / "independent/final-review-v1.json")
assert review["approved_for_batch_closeout"] and not review["failed_checks"]
for p, h in review["evidence_sha256"].items():
    assert sha(ROOT / p) == h, p
small = rd(B / "test-small-v1/metric_test_report.json")
fixture = rd(B / "test-fixture-v1/metric_test_report.json")
assert small["complete"] and small["passed"] == small["total"] == 21
assert fixture["complete"] and fixture["passed"] == fixture["total"] == 1
assert rd(B / "judge-injections-v1.json")["status"] == "passed"
assert rd(B / "order-controls-v1.json")["status"] == "passed"
assert not (B / "completion.json").exists()
guard = rd(B / "protected.json")
assert all(sha(ROOT / p) == h for p, h in guard.items())
freeze = rd(B / "independent/expected-freeze.json")
assert all(sha(ROOT / p) == h for p, h in freeze["input_hashes"].items())
assert all(sha(B / "independent" / p) == h for p, h in freeze["artifact_hashes"].items())
tests = rd(B / "independent/tests-small-all.json")
assert tests[6:] == rd(B / "before/customer/w03/tests.json")
small_bind = rd(B / "version-binding-small-v1.json")
fixture_bind = rd(B / "version-binding-fixture-v1.json")
assert small_bind["catalog_sha256"] == fixture_bind["catalog_sha256"]
assert small_bind["data_sha256"] != fixture_bind["data_sha256"]

traces = [B / "build-v1/trace.json"]
for sub in ["test-small-v1", "test-fixture-v1"]:
    traces.extend(sorted((B / sub / "traces").glob("*/*-trace.json")))
calls = [{"trace": p.relative_to(ROOT).as_posix(), "http_attempts": len(rd(p)["call"]["attempts"])} for p in traces]
audit = {"logical_model_calls": len(calls), "http_attempts": sum(c["http_attempts"] for c in calls),
         "build_runs": 1, "natural_language_tests": 22,
         "successful_sql_queries": sum(c["actual"]["status"] == "ok" for r in [small, fixture] for c in r["cases"]),
         "protected_files": len(guard), "all_protected_unchanged": True, "calls": calls,
         "fixture_separate": True, "old_15_questions_and_business_expectations_unchanged": True,
         "skill_judge_config_and_business_model_unchanged": True}
save(B / "execution-audit.json", audit)
save(ROOT / "customer/w03/tests.json", tests)
fixture_dest = ROOT / "customer/w03/tests-fixtures/b2-order-boundaries.json"
assert not fixture_dest.exists()
save(fixture_dest, rd(B / "independent/tests-fixture.json"))

new_ids = rd(B / "scope.json")["new_metrics"]
completion = {"status": "B2_completed_small_and_isolated_boundary", "new_metrics": new_ids,
              "cumulative_metric_count": 12, "small_passed": 21, "small_total": 21,
              "small_new_questions": 6, "small_regression_questions": 15,
              "fixture_passed": 1, "fixture_total": 1, "explanations_passed": 22,
              "library": f"{REL}/library-v1", "primary_project": small_bind["project"],
              "fixture_project": fixture_bind["project"], "scale_run": False,
              "review": f"{REL}/independent/final-review-v1.json",
              "small_report": f"{REL}/test-small-v1/metric_test_report.json",
              "fixture_report": f"{REL}/test-fixture-v1/metric_test_report.json",
              "small_binding": small_bind, "fixture_binding": fixture_bind,
              "next_batch": "B3 four distinct-account/store/item metrics; cumulative 16",
              "attribution": "导师执行与独立测试Agent核查；不登记本人独立作答、客户验收或正式提交"}

reg_path = ROOT / "customer/w03/metric_register.json"
reg = rd(reg_path)
reg["version"] = "w03-metric-register-v3"
reg["execution_review"] = completion["review"]
reg["current_library"] = completion["library"]
for batch in reg["batches"]:
    if batch["id"] in ["B1", "B2"]:
        batch.update(status="completed_small", current_regression_reference=f"{REL}/completion.json")
        if batch["id"] == "B2":
            batch.update(already_small_passed=new_ids, result_reference=f"{REL}/completion.json")
    elif batch["id"] == "B3":
        batch["status"] = "next_batch"
for m in reg["metrics"]:
    if m["batch"] not in ["B1", "B2"]:
        continue
    m["before_B2_reference"] = f"{REL}/before/customer/w03/metric_register.json#{m['id']}"
    m.update(build_status="B2累计12项build-v1/library-v1已构建并加载", current_adopted_library_scope="B1+B2累计12项小样本库",
             result_reference=f"{REL}/completion.json", review_reference=completion["review"], catalog_sha256=small_bind["catalog_sha256"])
    if m["batch"] == "B2":
        m.update(definition_status="已核字段、订单粒度、下单日、count单位及范围", test_design_status="6道small七指标题+1道人工逐日边界题；辅助恒等式另记",
                 expected_status="原CSV及明确人工fixture独立核算，构建前冻结", small_status="6/6新small题通过", fixture_status="1/1人工逐日题通过（5种订单边界）",
                 explanation_status="相应7题完整解释通过独立审核", known_pending="规模、未见问法及其他维度行为；无阻断本批的业务缺口",
                 expected_reference=f"{REL}/independent/tests-new-small.json")
        if "B2-E01" not in m["test_case_ids"]:
            m["test_case_ids"].append("B2-E01")
    else:
        m["small_status"] = "B2新库已回归原7道多指标金额题" if m["id"] != "net_sales_cents" else "B2新库已回归原15题"
        m["explanation_status"] = "B2新库对应解释及非成功原因通过独立审核"
reg["summary"].update(metrics_with_frozen_existing_tests=12, metrics_with_small_pass=12, metrics_with_scale_pass=0,
                       existing_real_cases=22, native_small_tests=21, isolated_fixture_tests=1,
                       new_design_entries=54, new_design_query_entries_executed=14,
                       new_design_auxiliary_entries_checked=2, new_design_entries_not_run=38,
                       new_model_calls=audit["logical_model_calls"], new_queries=audit["successful_sql_queries"],
                       new_http_attempts=audit["http_attempts"], last_batch="B2", next_batch="B3")
save(reg_path, reg)

plan_path = ROOT / "customer/w03/test-plans/metric_cases.json"
plan = rd(plan_path)
plan["version"] = "w03-metric-test-plan-v5"
plan["status"] = "B1_B2_executed_and_reviewed_remaining_design_only"
plan["rule"] = "small原生21题与人工fixture1题分数据集运行，期望已冻结；B1/B2辅助关系另记。其他38条设计未执行，不填假0/null。"
template = copy.deepcopy(next(c for c in plan["cases"] if c["id"] == "B2-N01"))
template.update(id="B2-E01", question_or_fixture=tests[5]["question"], kind="empty_window",
                expected_behavior="覆盖内不分组七计数为一行0；日期半开到6月30日，不包含该日订单。",
                fault_to_detect="将计数空窗当未知、null、空行或覆盖外；结束日多计")
assert not any(c["id"] == "B2-E01" for c in plan["cases"])
plan["cases"].append(template)
all_tests = {c["id"]: c for c in tests + rd(fixture_dest)}
for c in plan["cases"]:
    if c["id"] in all_tests:
        is_fixture = c["id"] == "B2-Z01"
        t = all_tests[c["id"]]
        c["before_B2_reference"] = f"{REL}/before/customer/w03/test-plans/metric_cases.json#{c['id']}" if c["id"] != "B2-E01" else "本批新增的计数空窗例"
        c.update(state="passed_on_B2_library_v1", executable=True, expected_state="frozen_before_build_and_actual",
                 execution_state="passed_and_explanation_reviewed", question_or_fixture=t["question"], execution_question=t["question"],
                 expected_reference=f"{REL}/independent/" + ("tests-fixture.json" if is_fixture else "tests-small-all.json") + "#" + c["id"],
                 result_reference=(completion["fixture_report"] if is_fixture else completion["small_report"]) + "#" + c["id"],
                 review_reference=completion["review"], data_version=(fixture_bind if is_fixture else small_bind)["data_version"],
                 catalog_sha256=small_bind["catalog_sha256"], dataset_kind="artificial_isolated_fixture" if is_fixture else "course_small")
        if c["batch"] == "B2":
            c["data_state"] = "明确人工5行边界样本，非青禾经营事实" if is_fixture else "原small CSV，逐单归属与区分力见independent台账/判据"
    elif c["id"] == "B2-A01":
        c.update(state="auxiliary_checked", executable=False, execution_state="checked_after_independent_values",
                 expected_state="identities_not_independent_expected_replacement", result_reference=f"{REL}/order-controls-v1.json#B2_A01")
for d in plan["common_design"]["dimensions"]:
    if d["id"] == "order__status":
        d.update(status="B2_grouping_passed", evidence="B2-D01")
    elif d["id"] == "metric_time__day":
        d.update(status="B1_B2_grouping_and_cross_month_boundary_passed", evidence="B1-D02; B2-D02; B2-Z01 isolated")
plan["common_design"]["B2_current_evidence"] = {"review": completion["review"], "generic_controls": f"{REL}/judge-injections-v1.json", "order_controls": f"{REL}/order-controls-v1.json", "fixture_separate": True}
save(plan_path, plan)

# The human-readable registers and continuity entries are updated in the companion function below.
def finish_documents():
    p = ROOT / "docs/w03/指标核对与测试登记.md"
    text = p.read_text()
    old = next(line for line in text.splitlines() if line.startswith("当前：**"))
    text = text.replace(old, "当前：**B1+B2共12/38项（约32%）通过小样本与解释核查；其余26项待按批执行，规模0/38。** 最新21道课程small题＝6道B2新题＋15道原题回归；另有1道人工逐日边界题，数据集独立。[本批结果](../../" + REL + "/结果速览.md)。", 1)
    text = text.replace("| B2 | 订单数量 | 7 | 下一批；累计金额5项＋订单数7项构建，回归B1 |", "| B2 | 订单数量 | 7 | small与人工边界、解释全部通过；已回归B1 |")
    text = text.replace("| B3 | 账户去重、门店与件数 | 4 | 排队，依赖核定后整批推进 |", "| B3 | 账户去重、门店与件数 | 4 | 下一批；累计构建16项并回归已通过测试 |")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        for m in reg["metrics"]:
            if m["batch"] in ["B1", "B2"] and line.startswith("| " + m["name"] + " `"):
                state = "6/6 small＋1/1人工边界；解释已审" if m["batch"] == "B2" else ("原15题回归通过；解释已审" if m["id"] == "net_sales_cents" else "原7道金额题回归通过；解释已审")
                lines[i] = f"| {m['name']} `{m['id']}` | 01，另核02/05 | 已核 | B2累计库v1 | 独立期望已冻结 | {state} | 未跑 |"
    text = "\n".join(lines) + "\n"
    text = text.replace("B1已提升为原生测试，其余新期望未计算", "B1/B2已提升为原生测试，fixture另存；其余新期望未计算")
    text = text.replace("[当前原生15例（含未改的原8例）]", "[当前small原生21例（含未改的原15例）]")
    text = text.replace("新增用例按批审核后追加，不覆盖旧失败。", "新增用例按批审核后追加，不覆盖旧失败；[B2人工边界题](../../customer/w03/tests-fixtures/b2-order-boundaries.json)只在对应fixture数据运行。")
    text = text.replace("B1已测成交门店/逐日分组、渠道eq及成交地区eq的AND筛选。", "B1/B2已测成交门店/逐日/订单状态分组、跨月日边界、渠道eq及成交地区eq的AND筛选。")
    p.write_text(text)

    p = ROOT / "docs/w03/指标模型测试集设计.md"
    text = p.read_text()
    text = text.replace("现形成53条新增设计条目，另引用8条真实已跑用例。", "现有54条新增设计条目（本批补B2-E01空窗），另引用8条原净额用例。新增条目中14条已真实问数、2条辅助关系已核、38条仍待执行。")
    text = text.replace("B1七道新问数已冻结并运行，B1-A01已核辅助关系；其余45条新设计仍未计算期望/运行，不能直接作为原生tests.json。", "当前small原生21题＋独立人工fixture1题已运行并审解释，B1-A01/B2-A01为辅助关系；其余38条新设计仍未计算期望/运行，不能直接作为原生tests.json。")
    text = text.replace("现同8题已在B1 library-v2回归通过并独立审解释。", "同8题先后在B1库和B2累计库回归通过并独立审解释。")
    text = text.replace("不覆盖后续45条新设计。", "最新完整成绩为B2累计库small21/21＋fixture1/1；不覆盖后续38条新设计。")
    text = text.replace("B1新库回归通过；原记录保留", "B2累计库回归通过；旧记录保留")
    start, end = text.index("## B2 ·"), text.index("## B3 ·")
    section = text[start:end]
    old_intro = next(line for line in section.splitlines() if line.startswith("本批指标："))
    section = section.replace(old_intro, "本批7项订单数已完成。**N01/R01/R02/D01/D02/E01六道课程small题通过；Z01在单独人工数据逐日核5种订单边界通过；A01为辅助关系，不算问数。** 实际完整问句、独立值和数据标识见[本批结果](../../" + REL + "/结果速览.md)。下表保留设计简写；D02单独检验日期边界，不冒称该例能区分同额订单去重，N01另核重复实付金额订单。")
    section = section.replace("| B2-A01 |", "| B2-E01 | 6月1日至29日（含首尾）七项订单数量。 | 覆盖内无订单，不分组返回一行七个0，不含6月30日。 | null/零/覆盖外混淆、结束日多计 |\n| B2-A01 |", 1)
    text = text[:start] + section + text[end:]
    text = text.replace("当前只store分组及order__channel的eq筛选有真实证据；还需归属门店/名称/地区、会员、等级、成交名称/地区、日期/月分组。", "已测store、metric_time__day和order__status分组，order__channel与store__region的eq组合筛选；还需归属门店/名称/地区、会员、等级、成交名称/地区分组及月分组。")
    p.write_text(text)

    current = ("**B2订单数量批次完成（2026-11-08，当前）：** 累计12项库一次生成，small21/21（6新题＋15原题回归）、人工边界1/1，22题完整解释及20条成功SQL均通过独立审核。人工样本5天逐日核零实付、正实付无退、部分退、全退、取消，不改课程数据。Skill v0.1.2、judge、build配置、W02基线及业务模型均未改。当前小样本12/38（约32%），规模0/38；其余38条新设计未执行。\n\n"
               "**下一批：B3账户去重、门店与件数4项。** 购买会员数、退款会员数、成交门店数、有效订单商品件数；先核各自入选订单集合和去重键，独立冻结期望，再累计构建16项并回归已通过测试。无新增待本人裁决事项。聊天绑定未切换；导师执行不等于本人独立掌握、验收或提交。\n\n")
    for name, link in [("AGENTS.md", f"{REL}/结果速览.md"), ("开始这里.md", f"{REL}/结果速览.md"),
                       ("docs/w03/test_design.md", f"../../{REL}/结果速览.md"),
                       ("../W03-学习会话接续.md", f"实操工程/{REL}/结果速览.md")]:
        p = ROOT / name
        text = p.read_text().replace("**B1金额批次完成（2026-11-08，当前）：**", "**B1金额批次完成（2026-11-08，历史）：**", 1)
        title, rest = text.split("\n", 1)
        p.write_text(title + "\n\n" + current + "本批证据：[结果速览](" + link + ")。以下旧停点按发生时点保留。\n" + rest)
    p = ROOT / "docs/w03/metric_decisions.md"
    title, rest = p.read_text().split("\n", 1)
    rest = rest.replace("B1五项金额已完成，下一批B2七项订单数量", "B1+B2共12项已完成small核查，下一批B3四项账户/门店/件数")
    p.write_text(title + "\n\n## B2订单数量核定（2026-11-08，当前）\n\n"
                "七项均按唯一订单号和ordered_at统计，单位count。创建含取消；paid不因全退或零实付而排除；有效需实付减退款>0；取消只看cancelled；退款需paid且退款>0；部分退需0<退款<实付；全退需paid、实付>0、退款=实付。COUNT(order_id)基于本期已核一行一单、主键唯一非空，不宣称脏数据去重。\n\n"
                "原small缺零实付paid，使用明确人工5行fixture逐日验证，非青禾经营事实。定义/字段无新增阻断缺口；[依据表](../../" + REL + "/口径与本批检查.md)、[21+1实际结果与独立审查](../../" + REL + "/结果速览.md)。模型、Skill、配置及原数据未改。以下保留此前核定记录。\n" + rest)
    p = ROOT / "../W03-学习笔记.md"
    title, rest = p.read_text().split("\n", 1)
    p.write_text(title + "\n\n## 2026-11-08 实操概念速记：订单集合与边界样本\n\n"
                "含义：一个订单可以同时属于多种统计集合，不能拿一项过滤条件套全批。青禾8月创建32单＝支付30单＋取消2单；退款4单＝部分退1单＋全退3单。全退仍是支付单，但不是有效单；部分退只要净额>0仍属有效。\n\n"
                "易混点：0实付/0退款的paid订单不能仅凭“两者相等”算全退，材料还要求实付>0。原small缺此记录，因此另建人工fixture；例子用于检验代码，不是新客户事实。用法：先列各指标的集合条件和独立期望，再挑能区分错误的记录；恒等式只作辅助。记忆要求：能解释paid、有效、退款三者关系，以及真实数据、人工样本和客户事实的区别；本轮不登记本人已独立掌握。\n\n"
                "来源：01订单日报、05字典和本批实际运行。累计12/38项small通过，21道课程题＋1道人工边界题已独立审解释。[本批证据](实操工程/" + REL + "/结果速览.md)。下一批B3四项去重与件数。\n" + rest)

finish_documents()
save(B / "completion.json", completion)
save(B / "bookkeeping-update.json", {"frozen_inputs_snapshot": f"{REL}/before", "updated_after_execution": ["customer/w03/tests.json", "customer/w03/test-plans/metric_cases.json"], "source_definitions_and_csv_unchanged": True, "expected_artifacts_unchanged": True})
save(B / "progress.json", {"stage": "B2_completed", "completion": f"{REL}/completion.json", "next_batch": "B3"})
print(json.dumps({"status": "B2_completed", "small": "21/21", "fixture": "1/1", "metrics": "12/38", "calls": len(calls)}, ensure_ascii=False))
