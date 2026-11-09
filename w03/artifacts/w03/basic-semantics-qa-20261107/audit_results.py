"""Audit saved native inputs and records; never calls a model or scores semantics."""
import hashlib
import importlib.util
import json
from pathlib import Path

BATCH = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("batch_runner", BATCH / "run_batch.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
ROOT = runner.ROOT


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


cases, _ = runner.prepare()
assert len(cases) == 6
index = read(BATCH / "run_index.json")
assert index["completed_case_records"] == len(cases)
assert {c["id"] for c in index["cases"]} == {c["id"] for c in cases}
assert not list((BATCH / "output").glob("*.runner-error.json"))
_, document, prompt, _, _ = runner.load_task(runner.SnapshotReader(ROOT), runner.CONFIG)
checks = []
readable = ["# 订单等基础含义：6题实际回答原文", "",
            "6个既有材料应用题；每题只收到来源细化候选、沿用提示、原问题及该题指定原文。下方完整保留实际回答，语义由独立Agent判读，不计为正文独立记忆或指标运行。", ""]
for case in cases:
    case_id = case["id"]
    output = read(BATCH / "output" / f"{case_id}.json")
    run_path = ROOT / output["result"]["run"]
    run, settings, _, _ = runner.check_run(runner.Workspace(ROOT), output["result"]["run"])
    request = read(run_path.parent / "request.json")
    attempts = read(run_path.parent / "attempts.json")
    answer = read(run_path.parent / "answer.json")["answer"] if (run_path.parent / "answer.json").exists() else None
    assert run["status"] in {"succeeded", "failed"} and run["mode"] == "live"
    assert (answer is not None) == (run["status"] == "succeeded")
    assert settings["expected"] == "" and settings["include_knowledge"]
    assert settings["question"] == runner.question_for(case)
    assert request["messages"] == runner.messages_for(document, prompt, runner.question_for(case), True)
    assert not request.get("tools")
    assert output["actual_answer"] == answer
    assert output["question"] == case["question"] and output["fixture"] == case.get("fixture")
    assert output["input_track"] == case["input_track"]
    assert output["fixed_materials"] == case["fixed_materials"]
    assert output["native_run_sha256"] == digest(run_path)
    checks.append({"id": case_id, "run": output["result"]["run"], "structure_checked": True, "status": run["status"], "error": run["error"],
                   "exact_question_and_fixture": True, "exact_frozen_model_and_prompt": True,
                   "fixed_materials": case["fixed_materials"], "exact_designated_materials": True,
                   "expected_sent": False, "tools": [],
                   "api_attempt_count": len(attempts["attempts"]),
                   "attempt_outcomes": [{k: a.get(k) for k in ("finish_reason", "error", "seconds")} for a in attempts["attempts"]],
                   "usage": attempts.get("usage"), "request_sha256": digest(run_path.parent / "request.json"),
                   "output_sha256": digest(BATCH / "output" / f"{case_id}.json")})
    readable += [f"## {case_id} · {case['dimension']}", "", case["question"], "",
                 "指定材料：" + "、".join(case["fixed_materials"]), "",
                 "### 实际回答", "", answer if answer is not None else "未取得答案；原生失败：" + str(run["error"]["code"]), "",
                 f"原生执行：[run.json]({run_path.as_posix()})。", ""]
audit = {"status": "all_native_records_and_model_inputs_checked", "cases": checks,
         "live_cases": len(checks), "successful_answers": sum(c["status"] == "succeeded" for c in checks), "execution_failures": sum(c["status"] == "failed" for c in checks), "http_attempts": sum(c["api_attempt_count"] for c in checks),
         "semantic_review": "independent reviewer required; this audit does not judge answers"}
(BATCH / "protocol_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
(BATCH / "actual_answers.md").write_text("\n".join(readable))
print(json.dumps({"audited_cases": len(checks), "http_attempts": audit["http_attempts"],
                  "expected_sent": False, "protected_unchanged": len(read(BATCH / "input/protected.json"))}))
