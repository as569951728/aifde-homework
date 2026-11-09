"""Bounded offline regression; temporary artifacts stay inside support only."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

sys.dont_write_bytecode = True
import run_batch as r


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix="offline-", dir=r.SUPPORT) as temporary:
        batch = Path(temporary)
        old = r.ROOT / "artifacts/w03/operations-qa-20261107/input"
        inputs = batch / "input"
        inputs.mkdir()
        for name in ("business_model.md", "knowledge_prompt.txt", "original_questions.json", "protected.json"):
            shutil.copyfile(old / name, inputs / name)
        case = r.read(old / "selected_questions.json")["cases"][0]
        question = case["question"]
        if "fixture" in case:
            question += "\n\n本题人工构造输入：\n" + json.dumps(case["fixture"], ensure_ascii=False, indent=2)
        r.save_new(inputs / "selected_questions.json", {"cases": [case]})
        r.save_new(inputs / "controls.json", {"cases": []})
        r.save_new(inputs / "requests.json", {"requests": [{"id": case["id"], "question": question}]})
        config = r.read(old / "knowledge.json")
        config.update(business_model=(inputs / "business_model.md").relative_to(r.ROOT).as_posix(),
                      prompt=(inputs / "knowledge_prompt.txt").relative_to(r.ROOT).as_posix())
        r.save_new(inputs / "knowledge.json", config)
        r.save_new(inputs / "manifest.json", {"files": {p.relative_to(batch).as_posix(): r.sha(p) for p in inputs.iterdir()}})
        with patch.object(r, "batch_path", return_value=batch), patch.object(r, "read_key", side_effect=AssertionError("KEY_FORBIDDEN")), \
             patch.object(r, "Agent", side_effect=AssertionError("AGENT_FORBIDDEN")), \
             patch.object(r, "ContextModel", side_effect=AssertionError("MODEL_FORBIDDEN")), \
             patch.object(sys, "argv", ["run_batch.py", "--batch", str(batch), "--check-only"]), redirect_stdout(io.StringIO()):
            assert r.main() == 0
        checks.append("check_only_did_not_read_key_construct_agent_or_model")
        context = r.prepare(batch)
        original = (inputs / "requests.json").read_bytes()
        (inputs / "requests.json").write_bytes(original + b" ")
        try:
            r.prepare(batch)
            raise AssertionError("TAMPER_ACCEPTED")
        except r.CheckError as exc:
            assert exc.code == "FROZEN_INPUT_CHANGED"
        (inputs / "requests.json").write_bytes(original)
        checks.append("frozen_input_tampering_rejected")
        r.save_new(batch / "input-review.json", {"status": "approved", "checks": [], "conclusion": "Offline fixture only"})
        gate = {"approved": True, "failed_checks": [], "runner_sha256": r.sha(Path(r.__file__)),
                "manifest_sha256": r.sha(inputs / "manifest.json"), "preflight_sha256": r.sha(batch / "preflight.json"),
                "input_review_sha256": r.sha(batch / "input-review.json")}
        r.save_new(batch / "gate_acceptance.json", gate)
        r.check_gate(context)
        for key, value, expected in (("approved", False, "GATE_NOT_APPROVED"),
                                     ("failed_checks", ["failure"], "GATE_NOT_APPROVED"),
                                     ("runner_sha256", "incorrect", "GATE_HASH_MISMATCH"),
                                     ("manifest_sha256", "incorrect", "GATE_HASH_MISMATCH"),
                                     ("preflight_sha256", "incorrect", "GATE_HASH_MISMATCH"),
                                     ("input_review_sha256", "incorrect", "INPUT_REVIEW_CHANGED")):
            (batch / "gate_acceptance.json").write_text(json.dumps({**gate, key: value}))
            try:
                r.check_gate(context)
                raise AssertionError("INVALID_GATE_ACCEPTED")
            except r.CheckError as exc:
                assert exc.code == expected
        (batch / "gate_acceptance.json").write_text(json.dumps(gate))
        checks.append("approval_failed_checks_and_all_four_gate_hashes_enforced")
        native = batch / "fake_native"
        native.mkdir()
        run_rel = (native / "run.json").relative_to(r.ROOT).as_posix()
        native_result = {"status": "failed", "run": run_rel, "error": {"code": "MODEL_JSON_INVALID"}}

        class OfflineModel:
            def __init__(self, **kwargs):
                pass

        class OfflineAgent:
            def __init__(self, *args):
                pass

            def answer_business_model(self, *args, **kwargs):
                r.save_new(native / "run.json", {"status": "failed", "error": {"code": "MODEL_JSON_INVALID"}})
                r.save_new(native / "response.json", {"message": {"role": "assistant", "content": "malformed outer response"}})
                return native_result

            def close(self):
                pass

        with patch.object(r, "ContextModel", OfflineModel), patch.object(r, "Agent", OfflineAgent), \
             patch.object(r, "check_run", side_effect=r.CheckError("HASH_MISMATCH")):
            r.execute(context, case["id"], "offline-placeholder-never-used")
        record = r.read(batch / "output" / (case["id"] + ".json"))
        assert record["result"] == native_result and record["actual_answer"] is None
        assert record["native_structure_check"] == "failed" and record["native_run"]["error"]["code"] == "MODEL_JSON_INVALID"
        assert (native / "response.json").relative_to(r.ROOT).as_posix() in record["native_files"]
        checks.append("check_run_failure_preserves_result_native_error_raw_hashes_without_fabricated_answer")
        with patch.object(r, "batch_path", return_value=batch), patch.object(r, "read_key", side_effect=AssertionError("KEY_FORBIDDEN")), \
             patch.object(sys, "argv", ["run_batch.py", "--batch", str(batch)]):
            try:
                r.main()
                raise AssertionError("EXISTING_OUTPUT_ACCEPTED")
            except r.CheckError as exc:
                assert exc.code == "CASE_OUTPUT_ALREADY_EXISTS"
        checks.append("existing_case_evidence_blocks_rerun_before_key_access")
    report = {"status": "passed", "checks": checks, "actual_model_calls": 0, "keychain_reads": 0,
              "runner_sha256": r.sha(Path(r.__file__))}
    r.write_identical_or_new(r.SUPPORT / "offline_checks.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
