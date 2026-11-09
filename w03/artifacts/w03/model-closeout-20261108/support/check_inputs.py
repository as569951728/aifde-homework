"""Small offline mechanical check using the unchanged course runner's check-only."""
from datetime import datetime, timezone
import json
import subprocess
import sys
from prepare_inputs import BASE, ROOT, PRIOR, SOURCE, CALIBRATION, INPUT, IDS, MODEL_SHA, EXPECTED_SHA, PROMPT_SHA, read, sha, save


def main():
    checks = []
    def check(ok, name):
        checks.append({"id": name, "passed": bool(ok)})
    selected = read(INPUT / "selected_questions.json")["cases"]
    requests = read(INPUT / "requests.json")["requests"]
    originals = {x["id"]: x for x in read(SOURCE / "selected_questions.json")["cases"]}
    old_requests = {x["id"]: x for x in read(SOURCE / "requests.json")["requests"]}
    check([x["id"] for x in selected] == [x["id"] for x in requests] == IDS and len(set(IDS)) == 7, "seven_case_order")
    for c, r in zip(selected, requests):
        check(c == originals[c["id"]], c["id"] + ":metadata_fixture_materials_exact")
        check(r == old_requests[c["id"]] and set(r) == {"id", "question"} and
              r["question"].encode() == old_requests[c["id"]]["question"].encode(), c["id"] + ":final_question_UTF8_exact_no_expected")
    for name in ["controls.json", "new_control_approval.json"]:
        check(sha(INPUT / name) == sha(SOURCE / name), "unchanged_control_bytes:" + name)
    check(sha(INPUT / "original_questions.json") == sha(CALIBRATION / "input/original_questions.json"), "unchanged_original_questions")
    check(sha(INPUT / "business_model.md") == MODEL_SHA == sha(CALIBRATION / "candidate/business_model.md"), "exact_63513_body")
    check(sha(INPUT / "reviewer_expectations.json") == EXPECTED_SHA == sha(CALIBRATION / "candidate/reviewer_expectations.json"), "exact_f799_reviewer_only_expected")
    check(sha(INPUT / "knowledge_prompt.txt") == PROMPT_SHA == sha(BASE / "candidate/knowledge_prompt.txt"), "exact_961464_prompt")
    control_ids = {c["id"] for c in read(INPUT / "controls.json")["cases"]}
    check(len(control_ids) == 6 and set(IDS) & control_ids == {"CTRL01", "TRACECTRL01"} and len(set(IDS) - control_ids) == 5, "five_original_two_controls_six_metadata_retained")
    approval = read(INPUT / "new_control_approval.json")
    check(approval["approved"] is True and approval["failed_checks"] == [] and approval["controls_sha256"] == sha(INPUT / "controls.json") and
          sha(ROOT / approval["reviewer_approval"]) == approval["reviewer_approval_sha256"], "original_control_approval_binding")
    for name in ["run_batch.py", "audit_results.py"]:
        check(sha(BASE / "support" / name) == sha(PRIOR / "support" / name), "unchanged_tool:" + name)
    protected = read(INPUT / "protected.json")
    snapshot = read(BASE / "input-integrity/baseline_snapshot.json")
    check(protected == snapshot["files"], "runtime_enforces_targeted_protection_manifest")
    check(all(protected.get(p) == h for p, h in read(SOURCE / "protected.json").items()), "original_12_protected_bindings_retained")
    for p, h in protected.items():
        check(sha(ROOT / p) == h, "protected:" + p)
    previous = read(SOURCE / "knowledge.json")
    previous.update(business_model=(INPUT / "business_model.md").relative_to(ROOT).as_posix(), prompt=(INPUT / "knowledge_prompt.txt").relative_to(ROOT).as_posix())
    check(read(INPUT / "knowledge.json") == previous, "config_only_isolated_paths_changed")
    manifest = read(INPUT / "manifest.json")
    paths = {p.relative_to(INPUT.parent).as_posix() for p in INPUT.rglob("*") if p.is_file() and p.name != "manifest.json"}
    check(set(manifest["files"]) == paths and all(sha(INPUT.parent / p) == h for p, h in manifest["files"].items()), "complete_frozen_manifest")
    check(not list((INPUT.parent / "output").glob("*")) and not (INPUT.parent / "run_index.json").exists(), "no_execution_records")
    if all(x["passed"] for x in checks):
        process = subprocess.run([sys.executable, "-B", str(BASE / "support/run_batch.py"), "--batch", str(INPUT.parent), "--check-only"], cwd=ROOT, capture_output=True, text=True)
        check(process.returncode == 0, "native_check_only_passed")
        if process.returncode == 0:
            result = json.loads(process.stdout)
            check(result["actual_model_calls"] == 0 and result["cases"] == 7, "check_only_zero_model_calls")
            pf = read(INPUT.parent / "preflight.json")
            check(len(pf["cases"]) == 7 and all(not c["expected_sent"] and not c["tools"] for c in pf["cases"]), "actual_messages_exclude_expected_and_tools")
    failed = [x for x in checks if not x["passed"]]
    report = {"status": "mechanical_input_integrity_passed" if not failed else "mechanical_input_integrity_failed",
              "approved": not failed, "approval_scope": "mechanical_input_integrity_only", "execution_approved": False,
              "reviewed_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "failed_checks": failed,
              "case_ids": IDS, "original_cases": 5, "controls": 2, "protected_files": len(protected), "formal_protected_files": 12,
              "runner_sha256": sha(BASE / "support/run_batch.py"), "manifest_sha256": sha(INPUT / "manifest.json"),
              "preflight_sha256": sha(INPUT.parent / "preflight.json") if (INPUT.parent / "preflight.json").exists() else None,
              "model_sha256": MODEL_SHA, "expected_sha256": EXPECTED_SHA, "prompt_sha256": PROMPT_SHA,
              "actual_model_calls": 0, "keychain_reads": 0, "required_gate": "qa-01/gate_acceptance.json"}
    save(BASE / "input-integrity/mechanical-check.json", report)
    text = "# 七题输入机械核验\n\n" + ("**机械核验通过，尚无执行批准。**" if not failed else "**机械核验失败，不可执行。**")
    text += f"\n\n检查 {len(checks)} 项；失败 {len(failed)} 项。7题=5原题+2控制，全部最终question/fixture/材料逐字复用Stage5（含E03），expected不发送。\n\n"
    text += f"正文63513、预期f799、提示961464原字节绑定；6个控制元信息与原批准保留。CTRL01是W02陈姐原访谈控制，TRACECTRL01为合成控制。{len(protected)}项定向hash保护（含12正式保护及旧proposal/历史原答评分链）；未复制历史目录。\n\n"
    text += "runner/auditor原字节复用，check-only未读钥匙串/密钥、0API。新语义门禁须由独立评审核状态、检查项与正文一致后签发；本JSON的approved只指机械完整性。最多7run，各题一次；仅框架确认length可扩一次，语义/格式/网络失败不重试。\n"
    with (BASE / "input-integrity/mechanical-check.md").open("x", encoding="utf-8") as f:
        f.write(text)
    print(json.dumps({k: report[k] for k in ["status", "approved", "execution_approved", "protected_files", "actual_model_calls", "failed_checks", "runner_sha256", "manifest_sha256", "preflight_sha256"]}, ensure_ascii=False))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
