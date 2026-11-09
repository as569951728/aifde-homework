"""One explicit FDE correction per candidate proposal; keep the first proposal."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "customer/w02/evaluations"))
from replay_review_stages import wf, Workspace, FixedExtraction, write
import getpass, subprocess, os, certifi

case = sys.argv[1]
assert case in ("qinghe", "transfer")
base = Path(__file__).resolve().parent / "protocol-fixed"
folder = base / "runs" / (case + "-v6.1")
assert not (folder / "revision.json").exists()
feedback = json.loads((base / "revision-feedback.json").read_text())[case]
setup = json.loads((folder / "setup.json").read_text())
ws = Workspace(folder / "workspace")
path = setup["session"]
before = wf.load_session(ws, path)
old_proposal = before["proposal_path"]
old_hash = wf.digest(ws.raw(old_proposal))
assert before["status"] == "awaiting_apply"
wf.revise(ws, path, "【仅隔离测试的FDE复审意见，非学员/客户采纳】\n" + feedback)
key = subprocess.run(["/usr/bin/security", "find-generic-password", "-a", getpass.getuser(),
    "-s", "com.chenzhaowen.aifde.w02.deepseek", "-w"], capture_output=True, text=True, check=True).stdout.strip()
os.environ["SSL_CERT_FILE"] = certifi.where()
model = wf.WorkflowModel(url="https://api.deepseek.com/chat/completions", key=key,
    model="deepseek-flash", profile="deepseek-json", timeout=180,
    max_tokens=16384, retry_max_tokens=32768, retry_timeout=240)
fixture = json.loads((base / "inputs" / (case + ".json")).read_text())
result = wf.advance(ws, path, model, FixedExtraction(fixture["claims"]))
summary = {"status": result["status"], "error": result["error"],
    "first_proposal_unchanged": old_hash == wf.digest(ws.raw(old_proposal)),
    "revision_number": result.get("proposal_revision"), "apply_performed": False,
    "source_documents_unchanged": all(wf.digest(ws.raw(result["task"][k])) == h for k,h in setup["base_hashes"].items())}
assert summary["source_documents_unchanged"] and summary["first_proposal_unchanged"]
if result["status"] == "awaiting_apply":
    write(folder / "revised-proposal.json", result["proposal"])
    for k in ("business_model", "notes_update"):
        with (folder / ("revised_" + k + ".md")).open("x") as f:
            f.write(result["proposal"][k])
write(folder / "revision.json", summary)
print(json.dumps({"case": case, **summary}, ensure_ascii=False))
