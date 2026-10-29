"""Run a separate course extraction without resuming or applying a workflow.

Uses the existing local Keychain configuration. The config determines the bounded
input scope; sources, prompts, requests and responses are frozen by the course tool.
"""
import argparse
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys

import certifi

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "platform"))
from fde_product.interview_extraction import (
    Workspace, CheckError, ExtractionModel, load_config, batches, extract, validate_run,
)
from fde_product.models import ModelError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config")
    args = parser.parse_args()
    ws = Workspace(ROOT)
    config, transcripts = load_config(ws, args.config)
    parts = batches(transcripts, config)
    if config["profile"] != "deepseek-json" or sys.platform != "darwin":
        raise SystemExit("This local entry requires the existing macOS DeepSeek configuration.")
    print(json.dumps({"stage": "input_checked", "meetings": len(transcripts),
                      "messages": sum(len(t["messages"]) for t in transcripts),
                      "batches": len(parts), "planned_calls": len(parts) + 1}), flush=True)
    secret = subprocess.run(
        ["/usr/bin/security", "find-generic-password", "-a", getpass.getuser(),
         "-s", "com.chenzhaowen.aifde.w02.deepseek", "-w"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    key = secret.stdout.rstrip("\r\n")
    if secret.returncode or not key or any(c.isspace() for c in key):
        raise SystemExit("Configured local key unavailable; no model call was made.")
    os.environ["SSL_CERT_FILE"] = certifi.where()
    model = ExtractionModel(url="https://api.deepseek.com/chat/completions", key=key,
                            model="deepseek-flash", profile=config["profile"],
                            timeout=180, max_tokens=32768,
                            retry_max_tokens=65536, retry_timeout=360)
    path = extract(ws, args.config, model)
    run = ws.load(path)
    if run["status"] == "succeeded":
        validate_run(ws, path)
    print(json.dumps({"status": run["status"], "run": path, "error": run["error"],
                      "formal_model_applied": False}, ensure_ascii=False), flush=True)
    return 0 if run["status"] == "succeeded" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CheckError, ModelError) as exc:
        print(json.dumps({"status": "failed", "code": exc.code}, ensure_ascii=False))
        raise SystemExit(2)
