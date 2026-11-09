"""Launch the prepared W02 comparison using the existing local Keychain key.

--check-only validates local inputs without reading credentials or calling a model.
The course CLI owns execution, snapshots, and evidence; review remains manual.
"""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import certifi

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "platform"))
from fde_product.natural_knowledge import (
    CONFIG, CheckError, SnapshotReader, load_task, messages_for, require,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--case", default="QH-KNOW-01", help="Prepared question ID; defaults to the original role-support comparison.")
    parser.add_argument("--plan", default="customer/w02/knowledge_cases_v0.3.json")
    args = parser.parse_args()
    reader = SnapshotReader(ROOT)
    plan = reader.load(args.plan)
    config, document, prompt, _, _ = load_task(reader, CONFIG)
    require(config["business_model"] == plan["model_document"], "MODEL_PATH_CHANGED")
    require(config["extraction_run"] == plan["extraction_entry"], "EXTRACTION_CHANGED")
    digest = hashlib.sha256(reader.raw(config["business_model"])).hexdigest()
    require(digest == plan["document_sha256"], "MODEL_CHANGED_REVIEW_CASE_FIRST")
    require(config["profile"] == "deepseek-json", "PROFILE_CHANGED")
    case = next((c for c in plan["cases"] if c["id"] == args.case), None)
    require(case is not None, "CASE_NOT_FOUND")
    question = case["question"]
    expected = "\n".join(case["expected_for_reviewer_only"])
    require(0 < len(question.strip()) <= 8000, "QUESTION_INVALID")
    require(len(expected) <= 16000, "EXPECTED_INVALID")
    context_chars = len(json.dumps(messages_for(document, prompt, question, True),
                                  ensure_ascii=False))
    require(context_chars <= config["max_context_chars"], "CONTEXT_LIMIT")
    if args.check_only:
        print(json.dumps({"status": "input_checked", "case": case["id"],
                          "model_sha256": digest, "context_chars": context_chars,
                          "actual_model_calls": 0, "planned_answers": 2,
                          "semantic_review": "required"}, ensure_ascii=False, indent=2))
        return 0
    require(sys.platform == "darwin", "LOCAL_MACOS_KEYCHAIN_REQUIRED")
    secret = subprocess.run(
        ["/usr/bin/security", "find-generic-password", "-a", getpass.getuser(),
         "-s", "com.chenzhaowen.aifde.w02.deepseek", "-w"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    key = secret.stdout.rstrip("\r\n")
    require(secret.returncode == 0 and key and not any(c.isspace() for c in key),
            "LOCAL_KEY_UNAVAILABLE")
    env = os.environ.copy()
    env.update({"FDE_MODEL_URL": "https://api.deepseek.com/chat/completions",
                "FDE_MODEL_NAME": "deepseek-flash", "FDE_MODEL_KEY": key,
                "FDE_MODEL_PROFILE": "deepseek-json",
                "FDE_MODEL_MAX_TOKENS": "8192", "FDE_MODEL_RETRY_MAX_TOKENS": "16384",
                "FDE_MODEL_TIMEOUT": "180", "FDE_MODEL_RETRY_TIMEOUT": "360",
                "FDE_MODEL_TOKEN_LIMIT_FIELD": "max_tokens",
                "SSL_CERT_FILE": certifi.where()})
    print("正在启动同题对照：先不提供业务模型，再提供当前已核对版本。完成后仍需人工判读。", flush=True)
    print("测试问题：" + question, flush=True)
    # Only non-secret inputs enter argv. Expected points are saved for review by
    # the course tool, never included in either model's messages.
    os.execve(sys.executable, [sys.executable, str(ROOT / "tools/w02_knowledge.py"),
                              "--workspace", str(ROOT), "compare", "--config", CONFIG,
                              "--question", question, "--expected", expected], env)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CheckError, OSError, UnicodeError, KeyError, TypeError, ValueError, StopIteration) as exc:
        print(json.dumps({"status": "failed", "code": getattr(exc, "code", "LOCAL_INPUT_INVALID")},
                         ensure_ascii=False))
        raise SystemExit(2)
