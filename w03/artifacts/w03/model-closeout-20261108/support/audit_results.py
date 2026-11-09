"""Offline structure and exact actual-input audit; never semantic scoring."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import run_batch as runner


def audit_case(context, case_id):
    batch = context["batch"]
    output_path = batch / "output" / (case_id + ".json")
    if not output_path.exists():
        return {"id": case_id, "audit_status": "missing_case_record", "api_attempt_count": 0}
    record = runner.read(output_path)
    result = record.get("result") or {}
    item = {"id": case_id, "audit_status": "failed", "execution_status": record.get("status"),
            "run": result.get("run"), "native_structure_check": record.get("native_structure_check"),
            "output_sha256": runner.sha(output_path), "checks": [], "errors": [], "api_attempt_count": 0}
    try:
        question = context["requests"][case_id]["question"]
        expected_messages = runner.messages_for(context["document"], context["prompt"], question, True)
        runner.require(record["case_id"] == case_id and record["actual_question_sha256"] == runner.text_sha(question), "OUTPUT_CASE_MISMATCH")
        runner.require(record["requests_sha256"] == runner.sha(batch / "input/requests.json"), "REQUESTS_FILE_CHANGED")
        runner.require(record["gate_sha256"] == runner.sha(batch / "gate_acceptance.json"), "GATE_CHANGED_AFTER_EXECUTION")
        native_files = record.get("native_files", {})
        runner.require(native_files, "NATIVE_EVIDENCE_MISSING")
        for name, digest in native_files.items():
            runner.require(runner.sha(runner.confined(runner.ROOT, name)) == digest, "NATIVE_FILE_CHANGED", name)
        item["checks"].append("native_file_hashes_match")
        runner.require(result.get("run"), "NATIVE_RESULT_MISSING")
        run_path = runner.confined(runner.ROOT, result["run"])
        run = runner.read(run_path)
        runner.require(record["native_run"] == run and record["native_run_sha256"] == runner.sha(run_path), "NATIVE_RUN_CHANGED")
        settings = runner.read(run_path.parent / "settings.json")
        runner.require(settings["question"] == question and settings["expected"] == ""
                       and settings["include_knowledge"] is True, "ACTUAL_QUESTION_CHANGED")
        request = runner.read(run_path.parent / "request.json")
        runner.require(request["messages"] == expected_messages and not request.get("tools"), "ACTUAL_MESSAGES_CHANGED")
        runner.require(set(json.loads(request["messages"][1]["content"])) == {"business_model", "question"}, "ACTUAL_FIELDS_CHANGED")
        item.update(question_sha256=runner.text_sha(settings["question"]),
                    messages_sha256=runner.json_sha(request["messages"]),
                    request_sha256=runner.sha(run_path.parent / "request.json"), expected_sent=False, tools=[])
        item["checks"].append("actual_request_exactly_matches_frozen_question_model_prompt")
        attempts = runner.read(run_path.parent / "attempts.json")
        rows = attempts["attempts"]
        runner.require(1 <= len(rows) <= 2, "UNEXPECTED_ATTEMPT_COUNT")
        for number, attempt in enumerate(rows):
            actual = attempt["request"]
            runner.require(actual["messages"] == expected_messages and not actual.get("tools"), "ATTEMPT_MESSAGES_CHANGED")
            runner.require(actual["model"] == runner.POLICY["model"], "ATTEMPT_MODEL_CHANGED")
            tokens = runner.POLICY["max_tokens"] if number == 0 else runner.POLICY["retry_max_tokens"]
            allowance = runner.POLICY["timeout"] if number == 0 else runner.POLICY["retry_timeout"]
            runner.require(attempt["max_tokens"] == tokens and 0 < attempt["timeout_seconds"] <= allowance, "ATTEMPT_POLICY_CHANGED")
            if number:
                runner.require(rows[0].get("error") == "MODEL_OUTPUT_TRUNCATED"
                               and rows[0].get("finish_reason") == "length", "UNAPPROVED_AUTOMATIC_RETRY")
        item["api_attempt_count"] = len(rows)
        item["attempt_outcomes"] = [{k: row.get(k) for k in ("finish_reason", "error", "seconds")} for row in rows]
        item["usage"] = attempts.get("usage")
        item["checks"].append("all_http_attempt_inputs_and_policy_match")
        runner.check_run(runner.Workspace(runner.ROOT), result["run"])
        runner.require(record["native_structure_check"] == "passed", "RECORDED_STRUCTURE_CHECK_FAILED")
        answer_path = run_path.parent / "answer.json"
        answer = runner.read(answer_path)["answer"] if run["status"] == "succeeded" else None
        runner.require(record["actual_answer"] == answer, "ACTUAL_ANSWER_MISMATCH")
        runner.require(run["status"] == result["status"] == record["status"], "EXECUTION_STATUS_MISMATCH")
        item["checks"].append("native_contract_and_output_record_match")
        item["audit_status"] = "passed"
        item["native_error"] = run.get("error")
    except Exception as exc:
        item["errors"].append(runner.safe_error(exc))
    return item


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--cases", nargs="+")
    parser.add_argument("--output", default="protocol_audit.json", help="New batch-relative JSON file; never overwrite a differing audit")
    args = parser.parse_args()
    context = runner.prepare(runner.batch_path(args.batch))
    runner.check_gate(context)
    selected = args.cases if args.cases else list(context["cases"])
    runner.require(len(set(selected)) == len(selected) and set(selected) <= context["cases"].keys(), "UNKNOWN_OR_DUPLICATE_CASE")
    checks = [audit_case(context, case_id) for case_id in selected]
    index = runner.read(context["batch"] / "run_index.json")
    indexed = runner.by_id(index["cases"], "INDEX")
    index_errors = []
    try:
        actual_ids = {i for i in context["cases"] if (context["batch"] / "output" / (i + ".json")).exists()}
        runner.require(set(indexed) == actual_ids and index["completed_case_records"] == len(actual_ids)
                       and index["total_selected"] == len(context["cases"]), "INDEX_CASE_SET_MISMATCH")
        for case_id in actual_ids:
            path = context["batch"] / "output" / (case_id + ".json")
            record = runner.read(path)
            runner.require(indexed[case_id]["output_sha256"] == runner.sha(path)
                           and indexed[case_id]["status"] == record["status"]
                           and indexed[case_id]["result"] == record["result"], "INDEX_RECORD_MISMATCH")
    except Exception as exc:
        index_errors.append(runner.safe_error(exc))
    passed = all(item["audit_status"] == "passed" for item in checks) and not index_errors
    report = {"status": "all_selected_native_records_and_model_inputs_checked" if passed else "audit_failed",
              "cases": checks, "index_errors": index_errors, "audited_cases": len(checks),
              "http_attempts": sum(item["api_attempt_count"] for item in checks),
              "successful_answers": sum(item.get("execution_status") == "succeeded" for item in checks),
              "semantic_review": "not_performed; independent reviewer required",
              "auditor_sha256": runner.sha(Path(__file__)), "actual_model_calls_by_auditor": 0}
    output = runner.confined(context["batch"], args.output)
    runner.require(output.suffix == ".json" and not output.is_relative_to(context["batch"] / "input")
                   and not output.is_relative_to(context["batch"] / "output"), "AUDIT_OUTPUT_PATH_INVALID")
    runner.write_identical_or_new(output, report)
    print(json.dumps({k: report[k] for k in ("status", "audited_cases", "http_attempts", "successful_answers")}))
    return 0 if passed else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "audit_failed", **runner.safe_error(exc)}))
        raise SystemExit(2)
