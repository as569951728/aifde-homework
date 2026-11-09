"""Index immutable native reports; test comparator on modified result copies only."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

B = Path(__file__).resolve().parent
ROOT = B.parents[2]
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
names = ['small-a', 'small-b', 'b5-fixture', 'b6-fixture', 'b2-fixture']
paths = [B / f'test-{name}-v3/metric_test_report.json' for name in names]
original_hashes = {p: sha(p) for p in paths}
reports = [read(p) for p in paths]
assert [r['total'] for r in reports] == [22, 21, 2, 1, 1]
assert all(r['complete'] for r in reports)
cases = [c for r in reports for c in r['cases']]
assert len(cases) == len({c['id'] for c in cases}) == 47
small_cases = reports[0]['cases'] + reports[1]['cases']
assert [c['id'] for c in small_cases] == [c['id'] for c in read(B / 'tests-small-all-planned-v2.json')]
index = {'kind': 'derived_index_not_a_new_native_run', 'complete': True,
         'total': 43, 'passed': sum(c['comparison']['passed'] for c in small_cases),
         'source_native_reports': [{'path': str(p.relative_to(ROOT)), 'sha256': sha(p)} for p in paths[:2]],
         'cases': small_cases, 'new_model_calls': 0, 'new_queries': 0}
out = B / 'combined-small-report-v3.json'
assert not out.exists()
out.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')
spec = importlib.util.spec_from_file_location('b56_judge', ROOT / 'customer/w03/judge.py')
judge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge)
by_id = {c['id']: c for c in cases}
controls = []

def check(label, cid, mutate, wanted):
    c = by_id[cid]
    if not c['comparison']['passed']:
        controls.append({'id': label, 'source_case': cid, 'status': 'not_run_original_failed'})
        return
    actual = copy.deepcopy(c['actual'])
    mutate(actual)
    result = judge.compare(c['expected'], actual)
    controls.append({'id': label, 'source_case': cid, 'kind': 'real_result_copy',
                     'expected_passed': wanted, 'actual_comparison': result,
                     'status': 'passed' if result['passed'] == wanted else 'failed'})

def value(actual, metric, replacement, group=None):
    column = actual['columns'].index(metric)
    row = next(r for r in actual['rows'] if group is None or r[0] == group)
    assert row[column] != replacement
    row[column] = replacement

check('correct_grouped_zero', 'B5-H03', lambda a: None, True)
check('zero_replaced_null', 'B5-H03', lambda a: value(a, 'first_order_count', None, 'M00005'), False)
check('window_reranked_first', 'B5-H03', lambda a: value(a, 'first_order_count', 1, 'M00005'), False)
check('first_payment_not_net', 'B5-H02-F', lambda a: value(a, 'first_order_sales_cents', 200), False)
check('correct_gte_two', 'B6-R01', lambda a: None, True)
check('incorrect_exact_two', 'B6-R01', lambda a: value(a, 'monthly_repeat_buyer_count', 0), False)
check('undefined_ratio_zero', 'B6-Z01', lambda a: value(a, 'monthly_repeat_rate', 0), False)
check('wrong_registered_denominator', 'B6-N01', lambda a: value(a, 'monthly_repeat_rate', 0.6), False)
check('missing_month', 'B6-M01', lambda a: a['rows'].pop(), False)
check('duplicate_month', 'B6-M01', lambda a: a['rows'].append(a['rows'][0][:]), False)
check('month_row_reordering', 'B6-M01', lambda a: a['rows'].reverse(), True)
assert all(sha(p) == original_hashes[p] for p in paths)
control_report = {'status': 'passed' if all(c['status'] == 'passed' for c in controls) else 'needs_review',
                  'controls': controls, 'total': len(controls), 'new_model_calls': 0, 'new_queries': 0,
                  'source_report_hashes': {str(p.relative_to(ROOT)): sha(p) for p in paths}}
(B / 'result-copy-controls-v3.json').write_text(json.dumps(control_report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'small': f"{index['passed']}/43", 'fixture': f"{sum(r['passed'] for r in reports[2:])}/4",
                  'controls': control_report['status']}, ensure_ascii=False))
