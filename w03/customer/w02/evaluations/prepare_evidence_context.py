"""Read-only candidate evidence index with adjacent question/answer context.

Never corrects a claim, infers confirmation, or writes a business model. Use the
actual original export order; missing messages and quote mismatches are errors.
"""
import argparse
import json
from pathlib import Path


def build_context(claims, transcripts):
    meetings = {t["meeting_id"]: t for t in transcripts}
    if len(meetings) != len(transcripts):
        raise ValueError("Duplicate meeting ID")
    result = []
    for claim in claims:
        pairs = []
        for e in claim["evidence"]:
            if e["meeting_id"] not in meetings:
                raise ValueError("Missing meeting")
            transcript = meetings[e["meeting_id"]]
            messages = transcript["messages"]
            ids = [m["id"] for m in messages]
            if len(set(ids)) != len(ids) or e["message_id"] not in ids:
                raise ValueError("Missing or duplicate message ID")
            n = ids.index(e["message_id"])
            if not e["quote"] or e["quote"] not in messages[n]["content"]:
                raise ValueError("Quote not found")
            previous_question = next((m for m in reversed(messages[:n]) if m["speaker"] == "user"), None)
            pairs.append({"meeting_id": e["meeting_id"], "role_id": transcript["role_id"],
                          "previous_question": previous_question,
                          "cited_message": messages[n], "cited_quote": e["quote"],
                          "next_two_messages": messages[n+1:n+3]})
        result.append({"claim_id": claim["id"],
                       "claim_evidence_message_ids": [e["message_id"] for e in claim["evidence"]],
                       "source_contexts": pairs})
    return {"kind": "original_export_context_index", "claims": result,
            "boundary": "前后邻接只用于阅读原问答，不证明存在引导、支持该候选或已获确认。保留原候选，人工核主张与证据。"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidates", type=Path, required=True)
    p.add_argument("--transcript", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    raw = json.loads(args.candidates.read_text())
    claims = raw["claims"] if isinstance(raw, dict) else raw
    packet = build_context(claims, [json.loads(x.read_text()) for x in args.transcript])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(packet, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"claims": len(claims), "output_written": True, "business_model_written": False}))


if __name__ == "__main__":
    main()
