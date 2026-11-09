"""Read-only counts/integrity verifier; no platform imports, keys, API or scoring.

Only new files inside aggregate-review are written. Final handoff content and
completion claims require a separate review; mechanical pass does not sign it.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[3]
EXECUTED = {"stage1": 18, "stage1-r2": 18, "stage2-r2": 8, "stage3-r2": 17,
            "stage4-evidence-trace": 22, "stage5-compact-evidence": 22}
CANCELLED = ("stage1-network-recovery", "stage2", "stage3", "stage4-network-recovery")
FINAL_CASES = {"U01", "U05", "P09", "DQ10", "B05", "F06", "A03", "E01", "E03", "E05", "REG01",
               "U04", "F05", "P01", "DQ09", "E02", "FMTCTRL01"}
OLD_PROPOSAL = "artifacts/w02/workflows/WF-8d2ebffec9d94a25bc164ae489fe13a0/proposal-3.json"
OLD_SESSION = "artifacts/w02/workflows/WF-8d2ebffec9d94a25bc164ae489fe13a0/session.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def check(condition, label):
    if not condition:
        raise ValueError(label)


def local(path):
    candidate = (ROOT / path).resolve()
    check(candidate.is_relative_to(ROOT), "path outside workspace")
    return candidate


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def unique(rows):
    result = {x["id"]: x for x in rows}
    check(len(result) == len(rows), "duplicate case ID")
    return result


def write_new(name, payload):
    path = (HERE / name).resolve()
    check(path.parent == HERE and path.suffix == ".json", "report path outside aggregate-review")
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def stage(name, require_complete=False):
    batch = BASE / name
    selected = unique(read(batch / "input/selected_questions.json")["cases"])
    requests = unique(read(batch / "input/requests.json")["requests"])
    originals = unique(read(batch / "input/original_questions.json")["cases"])
    controls = unique(read(batch / "input/controls.json")["cases"])
    check(set(selected) == set(requests) and len(selected) == EXECUTED[name], name + ": input case set")
    manifest = read(batch / "input/manifest.json")
    all_inputs = {p.relative_to(batch).as_posix() for p in (batch / "input").rglob("*")
                  if p.is_file() and p.name != "manifest.json"}
    check(set(manifest["files"]) == all_inputs, name + ": manifest coverage")
    for relative, expected in manifest["files"].items():
        check(sha(batch / relative) == expected, name + ": frozen " + relative)
    protected = read(batch / "input/protected.json")
    check(len(protected) == 12, name + ": protected count")
    for relative, expected in protected.items():
        check(sha(local(relative)) == expected, name + ": protected " + relative)
    for case_id, case in selected.items():
        check(case == originals.get(case_id, controls.get(case_id)), name + ": metadata " + case_id)
        check(set(requests[case_id]) == {"id", "question"}, name + ": request fields " + case_id)
    origins = unique(read(batch / "input/request_origins.json")["cases"])
    for case_id, origin in origins.items():
        question = requests[case_id]["question"]
        check(text_sha(question) == origin["question_sha256"], name + ": question hash " + case_id)
        if "previous_request" in origin:
            old = local(origin["previous_request"])
            check(sha(old) == origin["previous_request_sha256"], name + ": prior request unchanged " + case_id)
            check(json.loads(read(old)["messages"][1]["content"])["question"] == question,
                  name + ": exact prior question " + case_id)
    gate = read(batch / "gate_acceptance.json")
    check(gate["approved"] is True and gate["failed_checks"] == [], name + ": gate")
    gate_files = {"runner_sha256": BASE / "support/run_batch.py", "manifest_sha256": batch / "input/manifest.json",
                  "preflight_sha256": batch / "preflight.json", "input_review_sha256": batch / gate["input_review"]}
    for key, path in gate_files.items():
        check(sha(path) == gate[key], name + ": " + key)
    index = read(batch / "run_index.json")
    indexed = unique(index["cases"])
    records = {p.stem: read(p) for p in (batch / "output").glob("*.json") if "." not in p.stem}
    check(set(records) == set(indexed), name + ": output/index case set")
    check(index["completed_case_records"] == len(records), name + ": index completed count")
    check(set(index["pending_case_ids"]) == set(selected) - set(records), name + ": pending IDs")
    if require_complete:
        check(set(records) == set(selected), name + ": incomplete runs")
    review_path = batch / "independent-review/review.json"
    review = read(review_path) if review_path.exists() else None
    reviewed = unique(review["cases"]) if review else {}
    if require_complete:
        check(set(reviewed) == set(records), name + ": incomplete semantic review")
    details = []
    for case_id, output in records.items():
        output_path = batch / "output" / (case_id + ".json")
        check(sha(output_path) == indexed[case_id]["output_sha256"], name + ": output hash " + case_id)
        check(output["result"] == indexed[case_id]["result"], name + ": result index " + case_id)
        run_path = local(output["result"]["run"])
        run = read(run_path)
        check(run == output["native_run"] and sha(run_path) == output["native_run_sha256"], name + ": native run " + case_id)
        check(run["status"] == output["status"], name + ": status " + case_id)
        for relative, expected in output["native_files"].items():
            check(sha(local(relative)) == expected, name + ": native file " + relative)
        check(output["gate_sha256"] == sha(batch / "gate_acceptance.json"), name + ": output gate " + case_id)
        check(gate["signed_at"] <= output["started_at"], name + ": gate timing " + case_id)
        settings = read(run_path.parent / "settings.json")
        actual = read(run_path.parent / "request.json")
        check(settings["question"] == requests[case_id]["question"] and settings["expected"] == "",
              name + ": native question " + case_id)
        user = json.loads(actual["messages"][1]["content"])
        check(set(user) == {"business_model", "question"} and user["question"] == settings["question"],
              name + ": actual request " + case_id)
        check(user["business_model"] == (batch / "input/business_model.md").read_text(), name + ": actual model " + case_id)
        check(not actual.get("tools"), name + ": no tools " + case_id)
        attempts = read(run_path.parent / "attempts.json")["attempts"]
        check(1 <= len(attempts) <= 2, name + ": attempt count " + case_id)
        for attempt in attempts:
            check(attempt["request"]["messages"] == actual["messages"], name + ": attempt question " + case_id)
        if len(attempts) == 2:
            check(attempts[0].get("finish_reason") == "length" and attempts[0].get("error") == "MODEL_OUTPUT_TRUNCATED",
                  name + ": unapproved retry " + case_id)
        answer = read(run_path.parent / "answer.json")["answer"] if run["status"] == "succeeded" else None
        check(answer == output["actual_answer"], name + ": answer " + case_id)
        verdict = reviewed.get(case_id, {}).get("verdict", "not_reviewed")
        if case_id in reviewed:
            judged = reviewed[case_id]
            check(judged["output_sha256"] == sha(output_path), name + ": reviewed output " + case_id)
            check(judged["native_run_sha256"] == sha(run_path), name + ": reviewed run " + case_id)
            check(judged["actual_answer_sha256"] == (text_sha(answer) if answer is not None else None),
                  name + ": reviewed answer " + case_id)
            # Consolidated math/format rows may omit a per-case HTTP count.
            # Always derive it from native attempts; also verify any stated count.
            reviewed_attempt_count = judged.get("http_attempts", judged.get("native_attempt_count"))
            if reviewed_attempt_count is not None:
                check(reviewed_attempt_count == len(attempts), name + ": reviewed HTTP " + case_id)
        details.append({"id": case_id, "input_track": selected[case_id]["input_track"], "status": run["status"],
                        "verdict": verdict, "http_attempts": len(attempts), "native_error": run["error"],
                        "output": ref(output_path), "native_run": ref(run_path),
                        "actual_answer_sha256": text_sha(answer) if answer is not None else None})
    counts = {"native_runs": len(details), "http_attempts": sum(x["http_attempts"] for x in details),
              "native_succeeded": sum(x["status"] == "succeeded" for x in details),
              "native_failed": sum(x["status"] == "failed" for x in details),
              "semantic_passed": sum(x["verdict"] == "passed" for x in details),
              "semantic_failed": sum(x["verdict"] == "failed" for x in details),
              "semantic_not_assessable": sum(x["verdict"].startswith("not_assessable") for x in details),
              "semantic_pending": sum(x["verdict"] == "not_reviewed" for x in details)}
    if review:
        for key in ("http_attempts", "semantic_passed", "semantic_failed", "semantic_not_assessable"):
            check(review["summary"][key] == counts[key], name + ": review summary " + key)
        check(review["candidate_prompt_sha256"] == sha(batch / "input/knowledge_prompt.txt"), name + ": reviewed prompt")
        check(review["model_sha256"] == sha(batch / "input/business_model.md"), name + ": reviewed model")
    if name == "stage3-r2":
        check(set(selected) == FINAL_CASES, "final 17 scope")
    if name in {"stage4-evidence-trace", "stage5-compact-evidence"}:
        check(set(selected) & set(originals) == FINAL_CASES - {"FMTCTRL01"},
              name + ": original 16 scope")
        check(len(set(selected) & set(controls)) == 6, name + ": six approved controls")
    return {"stage": name, "counts": counts, "prompt": ref(batch / "input/knowledge_prompt.txt"),
            "manifest": ref(batch / "input/manifest.json"), "review": ref(review_path) if review else None,
            "cases": details, "scope_note": "Only this prompt version and these executed cases; never 82/82"}


def snapshot_paths():
    paths = {ROOT / OLD_PROPOSAL, ROOT / OLD_SESSION,
             ROOT / "artifacts/w03/full-validation-20261107/completion.json",
             ROOT / "artifacts/w03/full-validation-20261107/execution_ledger.json"}
    for name in ("stage1", "stage1-r2", "stage2-r2"):
        batch = BASE / name
        paths.update(p for p in batch.rglob("*") if p.is_file() and "/runtime/" not in p.as_posix())
        for p in (batch / "output").glob("*.json"):
            if "." not in p.stem:
                paths.update(local(x) for x in read(p)["native_files"])
    for origin in read(BASE / "stage3-r2/input/request_origins.json")["cases"]:
        if "previous_request" in origin:
            paths.update(p for p in local(origin["previous_request"]).parent.rglob("*") if p.is_file())
    paths.update(local(x) for x in read(BASE / "stage3-r2/input/protected.json"))
    return sorted(paths)


def scan_native_stages():
    found = {s: [] for s in (*EXECUTED, *CANCELLED)}
    for path in (ROOT / "artifacts/w02/knowledge_runs").glob("*/settings.json"):
        config = read(path).get("config_path", "")
        for name in found:
            if config == (BASE / name / "input/knowledge.json").relative_to(ROOT).as_posix():
                found[name].append(path.parent.relative_to(ROOT).as_posix())
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-baseline", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    errors, stages, pending_stages = [], [], []
    for name in EXECUTED:
        if not (BASE / name / "run_index.json").exists() and not args.require_complete:
            pending_stages.append({"stage": name, "status": "not_yet_executed", "planned_cases": EXECUTED[name]})
            continue
        try:
            stages.append(stage(name, args.require_complete or name in {"stage1", "stage1-r2", "stage2-r2"}))
        except Exception as exc:
            errors.append({"stage": name, "type": type(exc).__name__, "reason": str(exc)})
    native = scan_native_stages()
    for name in CANCELLED:
        if native[name] or list((BASE / name / "output").glob("*.json")):
            errors.append({"stage": name, "reason": "cancelled stage has execution evidence"})
    for result in stages:
        if len(native[result["stage"]]) != result["counts"]["native_runs"]:
            errors.append({"stage": result["stage"], "reason": "native/output count mismatch (or currently executing)"})
    baseline_path = HERE / "baseline_snapshot.json"
    if args.capture_baseline:
        write_new("baseline_snapshot.json", {"captured_at": datetime.now(timezone.utc).isoformat(),
                  "files": {p.relative_to(ROOT).as_posix(): sha(p) for p in snapshot_paths()},
                  "purpose": "Before final handoff: preserve earlier stages, historical original answers, formal/protected files and old proposal"})
    for snapshot in (baseline_path, HERE / "stage3-stage4-preservation.json"):
        if snapshot.exists():
            for relative, expected in read(snapshot)["files"].items():
                if sha(local(relative)) != expected:
                    errors.append({"reason": "pre-handoff evidence changed", "path": relative,
                                   "baseline": snapshot.name})
    report = {"status": "mechanical_checks_passed" if not errors else "mechanical_checks_need_attention",
              "recorded_at": datetime.now(timezone.utc).isoformat(), "stages": stages, "pending_stages": pending_stages, "errors": errors,
              "cancelled_stage_native_counts": {s: len(native[s]) for s in CANCELLED},
              "old_proposal": ref(ROOT / OLD_PROPOSAL), "old_session": ref(ROOT / OLD_SESSION),
              "verifier": ref(Path(__file__)), "baseline_snapshot": ref(baseline_path) if baseline_path.exists() else None,
              "reviewer_api_calls": 0, "final_completion_or_continuity_approval": False}
    write_new(args.output, report)
    print(json.dumps({"status": report["status"], "counts": {x["stage"]: x["counts"] for x in stages}, "errors": errors},
                     ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
