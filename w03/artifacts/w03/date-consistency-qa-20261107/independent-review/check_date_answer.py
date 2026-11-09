"""Reviewer-only checker for date-answer-table-1. No model calls or repairs.

API: check_answer(actual_answer: str, fixture: dict) -> JSON-serializable dict.
CLI: python check_date_answer.py OUTPUT_RECORD.json
Only a machine pass is returned; all prose/source claims still need review.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re

CONDITION_COLUMNS = ["检查项", "题设日期", "判定日是否满足本项条件", "依据"]
INTERVAL_COLUMNS = ["区间种类", "起点", "含起点", "终点", "含终点"]
CONDITION_FIELDS = {"生效日": "valid_from", "计划结束日": "valid_until", "提前终止日": "ended_at"}
INTERVAL_ROWS = {"计划区间", "综合有效区间"}
LABELS = {"判定日", "产品范围", "结论", "来源与范围"}
SUPPORTED_PRODUCTS = {"悦享年卡", "家庭季卡"}


def _presentation(value: str) -> str:
    """Strip balanced whole-cell Markdown wrappers, never infer token meanings."""
    value = value.strip()
    for _ in range(6):
        for wrapper in ("**", "__", "`", "*", "_"):
            if len(value) > len(wrapper) * 2 and value.startswith(wrapper) and value.endswith(wrapper):
                value = value[len(wrapper):-len(wrapper)].strip()
                break
        else:
            return value
    return value


def _date(value: object) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("not an exact ISO date")
    return date.fromisoformat(value)


def _cells(line: str) -> list[str]:
    line = line.strip().replace("｜", "|")
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith(r"\|"):
        line = line[:-1]
    return [_presentation(x.replace(r"\|", "|")) for x in re.split(r"(?<!\\)\|", line)]


def _parse(answer: str) -> tuple[dict, list[dict]]:
    parsed = {"labels": {}, "conditions": {}, "intervals": {}, "source_continuation": []}
    errors = []
    if not isinstance(answer, str) or not answer.strip():
        return parsed, [{"code": "EMPTY_OR_NONSTRING_ANSWER"}]
    if "```" in answer or "~~~" in answer:
        errors.append({"code": "CODE_FENCE_UNSUPPORTED"})
    lines = answer.splitlines()
    tables = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if "|" in line or "｜" in line:
            block = []
            while i < len(lines) and ("|" in lines[i] or "｜" in lines[i]):
                block.append(_cells(lines[i]))
                i += 1
            tables.append(block)
            continue
        normalized = _presentation(line)
        pair = re.split(r"[：:]", normalized, maxsplit=1)
        label = _presentation(pair[0]) if len(pair) == 2 else None
        if label in LABELS:
            if label in parsed["labels"]:
                errors.append({"code": "DUPLICATE_LABEL", "label": label})
            else:
                parsed["labels"][label] = _presentation(pair[1])
        elif "来源与范围" in parsed["labels"]:
            # Prose may wrap after the source label; it is preserved for human review.
            # Known duplicate labels are still caught above. No prose is machine-scored.
            parsed["source_continuation"].append(line)
        else:
            errors.append({"code": "UNPARSED_LINE", "line": line})
        i += 1
    for label in sorted(LABELS - set(parsed["labels"])):
        errors.append({"code": "MISSING_LABEL", "label": label})
    if len(tables) != 2:
        errors.append({"code": "TABLE_COUNT", "actual": len(tables), "expected": 2})
    seen_tables = set()
    for block in tables:
        header = block[0]
        if header == CONDITION_COLUMNS:
            kind, expected_rows, columns = "conditions", set(CONDITION_FIELDS), CONDITION_COLUMNS
        elif header == INTERVAL_COLUMNS:
            kind, expected_rows, columns = "intervals", INTERVAL_ROWS, INTERVAL_COLUMNS
        else:
            errors.append({"code": "UNKNOWN_TABLE_HEADER", "header": header})
            continue
        if kind in seen_tables:
            errors.append({"code": "DUPLICATE_TABLE", "table": kind})
        seen_tables.add(kind)
        if len(block) < 2 or len(block[1]) != len(columns) or not all(re.fullmatch(r":?-{3,}:?", x) for x in block[1]):
            errors.append({"code": "INVALID_TABLE_SEPARATOR", "table": kind})
            continue
        for row in block[2:]:
            if len(row) != len(columns):
                errors.append({"code": "COLUMN_COUNT", "table": kind, "row": row})
                continue
            name = row[0]
            if name not in expected_rows:
                errors.append({"code": "UNKNOWN_ROW", "table": kind, "row": name})
            elif name in parsed[kind]:
                errors.append({"code": "DUPLICATE_ROW", "table": kind, "row": name})
            else:
                parsed[kind][name] = dict(zip(columns[1:], row[1:]))
        for missing in sorted(expected_rows - set(parsed[kind])):
            errors.append({"code": "MISSING_ROW", "table": kind, "row": missing})
    for kind in {"conditions", "intervals"} - seen_tables:
        errors.append({"code": "MISSING_TABLE", "table": kind})
    if parsed["labels"].get("来源与范围") == "":
        errors.append({"code": "EMPTY_SOURCE_SCOPE"})
    for name, row in parsed["conditions"].items():
        if not row["依据"]:
            errors.append({"code": "EMPTY_BASIS", "row": name})
    return parsed, errors


def independent_expected(fixture: dict) -> dict:
    """Reviewer-side oracle from frozen C01-C05, never sent to the model."""
    if not isinstance(fixture, dict) or fixture.get("card_type") not in SUPPORTED_PRODUCTS:
        raise ValueError("supported scope is the two in-scope card products only")
    start, planned, decision = (_date(fixture[k]) for k in ("valid_from", "valid_until", "decision_date"))
    ended = None if fixture["ended_at"] is None else _date(fixture["ended_at"])
    effective = min(planned, ended) if ended is not None else planned
    if start >= effective:
        raise ValueError("empty/reversed fixture intervals are outside this batch contract")
    conditions = {"生效日": decision >= start, "计划结束日": decision < planned,
                  "提前终止日": ended is None or decision < ended}
    return {"decision_date": decision.isoformat(), "product_scope": "纳入", "conditions": conditions,
            "planned_interval": {"起点": start.isoformat(), "含起点": "是", "终点": planned.isoformat(), "含终点": "否"},
            "effective_interval": {"起点": start.isoformat(), "含起点": "是", "终点": effective.isoformat(), "含终点": "否"},
            "final_conclusion": "有效" if all(conditions.values()) else "无效"}


def check_answer(actual_answer: str, fixture: dict) -> dict:
    result = {"contract": "date-answer-table-1", "machine_status": "unparseable", "machine_pass": False,
              "semantic_review_required": True, "full_answer_pass": None,
              "limitations": ["Does not validate prose or source-to-claim semantics.",
                              "No card_type echo is required: object identity is checked in native request audit; only product_scope is checked here.",
                              "Exact Markdown 是/否 tokens are parsed; JSON booleans, numbers and prefixes are not inferred."],
              "errors": []}
    try:
        expected = independent_expected(fixture)
    except (ValueError, KeyError, TypeError) as exc:
        result.update(machine_status="unsupported_fixture", errors=[{"code": "UNSUPPORTED_FIXTURE", "detail": str(exc)}])
        return result
    parsed, errors = _parse(actual_answer)
    result.update(parsed=parsed, independently_expected=expected, errors=errors)
    if errors:
        return result

    def mismatch(code, field, actual, wanted):
        if actual != wanted:
            errors.append({"code": code, "field": field, "actual": actual, "expected": wanted})

    def token(value, allowed, field):
        if value == "待核":
            errors.append({"code": "UNKNOWN_REQUIRED_VALUE", "field": field})
            return False
        if value not in allowed:
            errors.append({"code": "INVALID_ENUM", "field": field, "actual": value})
            return False
        return True

    def date_token(value, field, allow_empty=False):
        if value == "待核":
            errors.append({"code": "UNKNOWN_REQUIRED_VALUE", "field": field})
            return False
        if value == "空" and allow_empty:
            return True
        try:
            _date(value)
            return True
        except (ValueError, TypeError):
            errors.append({"code": "INVALID_DATE", "field": field, "actual": value})
            return False

    labels = parsed["labels"]
    date_token(labels["判定日"], "判定日")
    token(labels["产品范围"], {"纳入", "排除"}, "产品范围")
    token(labels["结论"], {"有效", "无效"}, "结论")
    mismatch("FIELD_MISMATCH", "判定日", labels["判定日"], expected["decision_date"])
    mismatch("PRODUCT_SCOPE_MISMATCH", "产品范围", labels["产品范围"], expected["product_scope"])
    mismatch("CONCLUSION_MISMATCH", "结论", labels["结论"], expected["final_conclusion"])
    for name, field in CONDITION_FIELDS.items():
        row = parsed["conditions"][name]
        date_token(row["题设日期"], name + ".题设日期", allow_empty=name == "提前终止日")
        token(row["判定日是否满足本项条件"], {"是", "否"}, name + ".满足")
        mismatch("FIELD_MISMATCH", name + ".题设日期", row["题设日期"], "空" if fixture[field] is None else fixture[field])
        mismatch("CONDITION_MISMATCH", name + ".满足", row["判定日是否满足本项条件"], "是" if expected["conditions"][name] else "否")
    for name, expkey in (("计划区间", "planned_interval"), ("综合有效区间", "effective_interval")):
        row = parsed["intervals"][name]
        for field in ("起点", "终点"):
            date_token(row[field], name + "." + field)
        for field in ("含起点", "含终点"):
            token(row[field], {"是", "否"}, name + "." + field)
        for field, value in expected[expkey].items():
            mismatch("INTERVAL_MISMATCH", name + "." + field, row[field], value)
    # Cross-check what the model itself declared, in addition to independent truth.
    truth_tokens = [row["判定日是否满足本项条件"] for row in parsed["conditions"].values()]
    if all(x in {"是", "否"} for x in truth_tokens) and labels["产品范围"] in {"纳入", "排除"}:
        own_conclusion = "有效" if all(x == "是" for x in truth_tokens) and labels["产品范围"] == "纳入" else "无效"
        mismatch("CONJUNCTION_INCONSISTENT", "结论", labels["结论"], own_conclusion)
    interval = parsed["intervals"]["综合有效区间"]
    try:
        d, low, high = (_date(x) for x in (labels["判定日"], interval["起点"], interval["终点"]))
        if interval["含起点"] in {"是", "否"} and interval["含终点"] in {"是", "否"}:
            member = (d > low or d == low and interval["含起点"] == "是") and (d < high or d == high and interval["含终点"] == "是")
            own_conclusion = "有效" if member and labels["产品范围"] == "纳入" else "无效"
            mismatch("INTERVAL_CONCLUSION_INCONSISTENT", "结论", labels["结论"], own_conclusion)
    except (ValueError, TypeError):
        pass  # Invalid tokens are already recorded and can never pass.
    result.update(machine_status="fail" if errors else "pass", machine_pass=not errors)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="Frozen output JSON with fixture and actual_answer")
    args = parser.parse_args()
    record = json.loads(args.record.read_text())
    result = check_answer(record["actual_answer"], record["fixture"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["machine_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
