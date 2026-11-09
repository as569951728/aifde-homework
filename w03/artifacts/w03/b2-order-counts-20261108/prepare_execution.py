"""Bind independently frozen expectations to a reviewed loaded project, before queries."""
import copy
import hashlib
import json
import sys
from pathlib import Path

project, tests_path, output, binding_path = map(Path, sys.argv[1:5])
assert not output.exists() and not binding_path.exists(), "Preserve prior versions"
assert json.loads((project / "validation.json").read_text())["passed"]
dataset = json.loads((project / "dataset.json").read_text())
data_hash = hashlib.sha256(json.dumps({k: v for k, v in dataset.items() if k != "library_sha256"}, sort_keys=True).encode()).hexdigest()
tests = json.loads(tests_path.read_text())
assert len({c["id"] for c in tests}) == len(tests)
execution = copy.deepcopy(tests)
for case in execution:
    if case["expected"]["status"] == "ok":
        case["expected"].update(data_version=dataset["id"], data_sha256=data_hash,
                                catalog_sha256=dataset["library_sha256"])
output.write_text(json.dumps(execution, ensure_ascii=False, indent=2) + "\n")
binding = {"status": "frozen_before_query", "project": str(project), "case_count": len(tests),
           "data_version": dataset["id"], "data_sha256": data_hash,
           "catalog_sha256": dataset["library_sha256"], "independent_tests": str(tests_path),
           "independent_tests_sha256": hashlib.sha256(tests_path.read_bytes()).hexdigest(),
           "execution_tests_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
           "business_expectations_changed": False}
binding_path.write_text(json.dumps(binding, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(binding, ensure_ascii=False))
