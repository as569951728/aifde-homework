"""Pure comparison for the W03 contract; no model, database or file access.

Integer expectations compare exactly (an equal finite float is accepted).
Float expectations use the declared tolerances; null is distinct from zero.
Intent lists/AND filters and result columns/rows may be reordered, not omitted.
First validated use: net_sales_cents, small dataset. Wider coverage is separate.
"""
import datetime
import json
import math
import sys

REL_TOL = 1e-9
ABS_TOL = 1e-7
STATUSES = ("ok", "clarify", "unsupported", "error")
VERSIONS = ("data_version", "data_sha256", "catalog_sha256")
INTENT_FIELDS = {"metrics", "start", "end", "group_by", "filters"}


def safe(value):
    if type(value) is float and not math.isfinite(value):
        return repr(value)
    if isinstance(value, list):
        return [safe(v) for v in value]
    if isinstance(value, dict):
        return {k: safe(v) for k, v in value.items()}
    return value


def names(value, nonempty=False):
    return (isinstance(value, list) and (bool(value) or not nonempty)
            and all(isinstance(v, str) and v for v in value)
            and len(value) == len(set(value)))


def normalized_intent(intent):
    if not isinstance(intent, dict) or set(intent) != INTENT_FIELDS:
        raise ValueError("intent requires exactly metrics/start/end/group_by/filters")
    if not names(intent["metrics"], True) or not names(intent["group_by"]):
        raise ValueError("metric and group lists require unique nonempty strings")
    for key in ("start", "end"):
        v = intent[key]
        if not isinstance(v, str) or datetime.date.fromisoformat(v).isoformat() != v:
            raise ValueError("invalid ISO date")
    if intent["start"] >= intent["end"]:
        raise ValueError("invalid half-open interval")
    if not isinstance(intent["filters"], list):
        raise ValueError("filters must be a list")
    filters = []
    for f in intent["filters"]:
        if not isinstance(f, dict) or set(f) != {"field", "op", "value"}:
            raise ValueError("invalid filter fields")
        field, op, value = f["field"], f["op"], f["value"]
        if not isinstance(field, str) or not field:
            raise ValueError("invalid filter field")
        if op == "eq" and isinstance(value, str):
            normalized = value
        elif op == "in" and names(value, True):
            normalized = sorted(value)
        else:
            raise ValueError("invalid filter operation or value")
        filters.append(json.dumps([field, op, normalized], ensure_ascii=False))
    if len(filters) != len(set(filters)):
        raise ValueError("duplicate filters")
    return {"metrics": sorted(intent["metrics"]), "start": intent["start"],
            "end": intent["end"], "group_by": sorted(intent["group_by"]),
            "filters": sorted(filters)}


def equal_value(want, got):
    if want is None:
        return got is None
    if type(want) not in (int, float) or type(got) not in (int, float):
        return False
    if type(got) is float and not math.isfinite(got):
        return False
    if type(want) is int:
        return got == want
    return math.isfinite(want) and math.isclose(want, got, rel_tol=REL_TOL, abs_tol=ABS_TOL)


def compare(expected, actual):
    differences = []

    def add(path, want, got, rule):
        differences.append({"path": path, "expected": safe(want),
                            "actual": safe(got), "rule": rule})

    def done():
        return {"passed": not differences, "differences": differences}

    if not isinstance(expected, dict) or not isinstance(actual, dict):
        add("root", "two objects", [expected, actual], "contract")
        return done()
    want_status, got_status = expected.get("status"), actual.get("status")
    if want_status not in STATUSES or got_status != want_status:
        add("status", want_status, got_status, "exact supported status")
    for key in VERSIONS:
        if key in expected and (key not in actual or actual[key] != expected[key]):
            add(key, expected[key], actual.get(key), "locked version")
    if differences or want_status != "ok":
        return done()
    normalized = {}
    for side, document in (("expected", expected), ("actual", actual)):
        try:
            normalized[side] = normalized_intent(document.get("intent"))
        except (ValueError, TypeError) as exc:
            add(side + ".intent", "valid intent", document.get("intent"), str(exc))
    if len(normalized) != 2:
        return done()
    for key in sorted(INTENT_FIELDS):
        if normalized["expected"][key] != normalized["actual"][key]:
            add("intent." + key, expected["intent"][key], actual["intent"][key], "exact intent")
    metrics = normalized["expected"]["metrics"]
    groups = normalized["expected"]["group_by"]
    expected_units = expected.get("units")
    if (not isinstance(expected_units, dict) or set(expected_units) != set(metrics)
            or not all(isinstance(v, str) and v for v in expected_units.values())):
        add("expected.units", metrics, expected_units, "one unit per metric")
    if actual.get("units") != expected_units:
        add("units", expected_units, actual.get("units"), "exact units, no missing/extra units")
    indexed = {}
    for side, document in (("expected", expected), ("actual", actual)):
        columns, rows = document.get("columns"), document.get("rows")
        if not names(columns, True) or set(columns) != set(groups + metrics):
            add(side + ".columns", groups + metrics, columns, "unique exact columns")
            continue
        if not isinstance(rows, list):
            add(side + ".rows", "array", rows, "contract")
            continue
        if not groups and len(rows) != 1:
            add(side + ".rows", "one aggregate row", rows, "single aggregate")
        index = {}
        for position, row in enumerate(rows):
            if not isinstance(row, list) or len(row) != len(columns):
                add(f"{side}.rows[{position}]", len(columns), row, "row width")
                continue
            values = dict(zip(columns, row))
            if any(type(values[g]) not in (str, int, float, bool, type(None))
                   or (type(values[g]) is float and not math.isfinite(values[g])) for g in groups):
                add(f"{side}.rows[{position}]", "scalar group values", row, "group key")
                continue
            key = tuple((type(values[g]).__name__, values[g]) for g in groups)
            if key in index:
                add(f"{side}.rows[{position}]", "unique group", row, "duplicate group")
                continue
            index[key] = values
        indexed[side] = index
    if len(indexed) == 2:
        wanted, got = indexed["expected"], indexed["actual"]
        for key in wanted.keys() - got.keys():
            add("rows", wanted[key], None, "missing group")
        for key in got.keys() - wanted.keys():
            add("rows", None, got[key], "extra group")
        for key in wanted.keys() & got.keys():
            for metric in metrics:
                if not equal_value(wanted[key][metric], got[key][metric]):
                    group = {g: wanted[key][g] for g in groups}
                    add("rows." + str(group) + "." + metric,
                        wanted[key][metric], got[key][metric], "null/exact integer/declared float tolerance")
    return done()


if __name__ == "__main__":
    data = json.load(sys.stdin)
    print(json.dumps(compare(data["expected"], data["actual"]), ensure_ascii=False, allow_nan=False))
