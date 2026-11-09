"""Mechanical input audit only. Produces matching JSON and Markdown; no API."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent.parent
ROOT = BASE.parents[2]
SOURCE = ROOT / "artifacts/w03/answer-repair-20261107/stage5-compact-evidence/input"
BATCH = BASE / "qa-01"
INPUT = BATCH / "input"
checks = []


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(value, name):
    checks.append({"id": name, "passed": bool(value)})
    if not value:
        raise ValueError(name)


def main():
    scope = read(BASE / "scope.json")
    selected = read(INPUT / "selected_questions.json")["cases"]
    requests = read(INPUT / "requests.json")["requests"]
    originals = {c["id"]: c for c in read(SOURCE / "selected_questions.json")["cases"]}
    old_requests = {r["id"]: r for r in read(SOURCE / "requests.json")["requests"]}
    check([c["id"] for c in selected] == [r["id"] for r in requests] == scope["case_ids"], "six_case_order")
    check(len(selected) == len({c["id"] for c in selected}) == 6, "six_unique_cases")
    for c, request in zip(selected, requests):
        check(c == originals[c["id"]], c["id"] + ":original_metadata_and_fixture_exact")
        check(request == old_requests[c["id"]] and set(request) == {"id", "question"}, c["id"] + ":final_question_exact_no_expected")
        check(request["question"].encode() == old_requests[c["id"]]["question"].encode(), c["id"] + ":question_UTF8_bytes_exact")
    for filename in ("original_questions.json", "reviewer_expectations.json", "controls.json", "new_control_approval.json", "protected.json"):
        check(sha(INPUT / filename) == sha(SOURCE / filename), "unchanged_bytes:" + filename)
    control_doc = read(INPUT / "controls.json")
    control_ids = {c["id"] for c in control_doc["cases"]}
    check(len(control_ids) == 6 and len(control_ids & set(scope["case_ids"])) == 2, "six_control_metadata_two_selected")
    check(len(set(scope["case_ids"]) - control_ids) == 4, "four_original_cases")
    approval = read(INPUT / "new_control_approval.json")
    check(approval["approved"] is True and approval["failed_checks"] == []
          and approval["controls_sha256"] == sha(INPUT / "controls.json")
          and sha(ROOT / approval["reviewer_approval"]) == approval["reviewer_approval_sha256"], "original_control_approval_binding")
    check(sha(INPUT / "business_model.md") == scope["model_sha256"] == sha(ROOT / scope["model_source"]), "unchanged_clarified_body")
    check(sha(INPUT / "knowledge_prompt.txt") == scope["candidate_prompt_sha256"]
          == sha(BASE / "candidate/knowledge_prompt.txt"), "exact_candidate_prompt")
    for filename in ("run_batch.py", "audit_results.py"):
        source = ROOT / "artifacts/w03/model-clarification-20261108/support" / filename
        check(sha(BASE / "support" / filename) == sha(source), "original_tool_bytes:" + filename)
    protected = read(INPUT / "protected.json")
    check(len(protected) == 12, "twelve_protected_files")
    for relative, digest in protected.items():
        check(sha(ROOT / relative) == digest, "protected:" + relative)
    snapshot = read(BASE / "input-integrity/baseline_snapshot.json")
    for relative, digest in snapshot["files"].items():
        check(sha(ROOT / relative) == digest, "preserved:" + relative)
    config, previous = read(INPUT / "knowledge.json"), read(SOURCE / "knowledge.json")
    expected = {**previous, "business_model": (INPUT / "business_model.md").relative_to(ROOT).as_posix(),
                "prompt": (INPUT / "knowledge_prompt.txt").relative_to(ROOT).as_posix()}
    check(config == expected, "config_only_isolated_paths_changed")
    manifest = read(INPUT / "manifest.json")
    all_input_files = {p.relative_to(BATCH).as_posix() for p in INPUT.rglob("*") if p.is_file() and p.name != "manifest.json"}
    check(set(manifest["files"]) == all_input_files, "complete_manifest_coverage")
    for relative, digest in manifest["files"].items():
        check(sha(BATCH / relative) == digest, "frozen:" + relative)
    check(not list((BATCH / "output").glob("*")) and not (BATCH / "run_index.json").exists(), "not_executed")
    completed = subprocess.run([sys.executable, "-B", str(BASE / "support/run_batch.py"),
                                "--batch", str(BATCH), "--check-only"], capture_output=True, text=True, cwd=ROOT)
    check(completed.returncode == 0, "native_check_only_passed")
    result = json.loads(completed.stdout)
    check(result["actual_model_calls"] == 0 and result["cases"] == 6, "check_only_zero_model_calls")
    preflight = read(BATCH / "preflight.json")
    check(len(preflight["cases"]) == 6 and all(not c["expected_sent"] and not c["tools"] for c in preflight["cases"]),
          "no_expected_or_tools_in_frozen_messages")
    report = {"status": "mechanical_input_integrity_passed", "approved": True,
              "approval_scope": "mechanical_input_integrity_only", "execution_approved": False,
              "reviewed_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "failed_checks": [],
              "case_ids": scope["case_ids"], "original_cases": 4, "controls": 2,
              "model_sha256": sha(INPUT / "business_model.md"), "prompt_sha256": sha(INPUT / "knowledge_prompt.txt"),
              "runner_sha256": sha(BASE / "support/run_batch.py"), "manifest_sha256": sha(INPUT / "manifest.json"),
              "preflight_sha256": sha(BATCH / "preflight.json"),
              "baseline_snapshot_sha256": sha(BASE / "input-integrity/baseline_snapshot.json"),
              "baseline_files_checked": len(snapshot["files"]), "protected_files": 12,
              "actual_model_calls": 0, "keychain_reads": 0,
              "required_next_gate": "qa-01/gate_acceptance.json signed after fresh independent source/candidate/input review"}
    path = BASE / "input-integrity/mechanical-check.json"
    with path.open("x", encoding="utf-8") as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = ["# 六题冻结输入机械核验", "",
             "**机械输入核验通过；尚无执行批准。** JSON中approved仅用于mechanical_input_integrity_only，execution_approved=false，failed_checks为空。",
             "", f"- 检查 {len(checks)} 项通过；6题=4原题+2控制。", "- 最终question的UTF-8内容与Stage5逐题完全相同；fixture和材料已包含在冻结问题内，未拼新内容。",
             "- 原题元信息、原期望、6个控制元信息及批准绑定逐字保留；expected不发送，工具列表为空。",
             "- 正文保留11月8日澄清候选；唯一变化为root提供的候选回答提示。知识配置只改新隔离路径。",
             f"- 旧目录/评审/保护快照共{len(snapshot['files'])}个文件hash未变，12保护项全部一致。", "- 原runner/auditor原字节复制；check-only通过，模型调用0、钥匙串读取0。未初始化工程，未读取.env或密钥。",
             "- 每题仅一次新run，确认length可按原策略扩一次；本轮语义/格式/网络失败留档，不另恢复或抽样。", "",
             "必须由新鲜独立来源评审完成candidate及完整输入审查后，在qa-01/gate_acceptance.json签发执行门禁。该门禁需绑定runner、manifest、preflight及input-review的文件hash；本核验不能替代该批准。", "",
             f"runner SHA256：{report['runner_sha256']}", f"manifest SHA256：{report['manifest_sha256']}", f"preflight SHA256：{report['preflight_sha256']}", ""]
    with (BASE / "input-integrity/mechanical-check.md").open("x", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(json.dumps({k: report[k] for k in ("status", "approved", "execution_approved", "original_cases", "controls",
                                            "baseline_files_checked", "actual_model_calls", "failed_checks")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
