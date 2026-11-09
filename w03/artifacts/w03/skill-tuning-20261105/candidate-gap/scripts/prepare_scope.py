"""Index supplied target names against verbatim Markdown headings.

No business-rule inference, expected answers, model calls, or formal-document writes.
Unmatched/ambiguous sections remain visible for review; all source texts stay intact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re


def build_scope(target_id, catalog, materials):
    by_id = {}
    for item in catalog:
        if not item.get("id") or not item.get("name") or item["id"] in by_id:
            raise ValueError("Invalid or duplicate target ID")
        by_id[item["id"]] = item
    if target_id not in by_id:
        raise ValueError("Target not found in supplied catalog")
    headings = []
    for source, content in materials.items():
        lines = content.splitlines()
        marks = [(n, m.group(1).strip()) for n, line in enumerate(lines)
                 if (m := re.match(r"^##\s+(.+?)\s*$", line))]
        for idx, (start, heading) in enumerate(marks):
            end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
            matches = [x["id"] for x in catalog if x["name"].strip() == heading]
            headings.append({"source": source, "heading": heading, "line": start + 1,
                             "catalog_ids": matches,
                             "relation": "selected_title" if target_id in matches else "other_target_title" if matches else "unmatched_title",
                             "verbatim_section": "\n".join(lines[start:end])})
    direct = [x for x in headings if x["relation"] == "selected_title"]
    return {"selected_target": by_id[target_id], "catalog": catalog,
            "source_sha256": {p: hashlib.sha256(s.encode()).hexdigest() for p, s in materials.items()},
            "heading_index": headings, "exact_title_match_found": bool(direct),
            "mapping_kind": "exact_catalog_name_to_heading_only",
            "limitation": "目录与标题用于定位，不裁定规则优先级或依赖。未匹配/一名多ID须核；正文、跨章节依赖及共同边界仍读原文。原资料未裁剪。"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--material", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    catalog = json.loads(args.catalog.read_text())
    materials = {str(f): f.read_text() for f in args.material}
    result = build_scope(args.target, catalog, materials)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"target": args.target, "headings": len(result["heading_index"]),
                      "exact_title_match_found": result["exact_title_match_found"]}))


if __name__ == "__main__":
    main()
