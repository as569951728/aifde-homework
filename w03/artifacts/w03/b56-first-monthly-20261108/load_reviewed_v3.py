"""Promote one reviewed build and load isolated datasets, without activating chat."""
import hashlib
import json
import subprocess
from pathlib import Path

B = Path(__file__).resolve().parent
ROOT = B.parents[2]
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
review = read(B / 'execution-review/build-review-v3.json')
assert review['approved_for_merge_load'] and not review['failed_checks']
for p, h in review['evidence_sha256'].items():
    assert sha(ROOT / p) == h, p
old = read(B / 'regression-review/pretest-build-review-v3.json')
assert old['passed'] and not old['failed_checks']
for p, h in old['evidence_sha256'].items():
    assert sha(ROOT / p) == h, p
library = B / 'library-v3'
assert not library.exists()
python = str(ROOT / '.venv/bin/python')

def native(label, args):
    with (B / (label + '.log')).open('x') as log:
        p = subprocess.run([python, '-B', str(ROOT / 'tools/w03.py'), *map(str, args)],
                           cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    assert p.returncode == 0, label

native('merge-v3', ['merge', '--inputs', B / 'build-v3', '--data', ROOT / 'materials/data/small', '--output', library])
datasets = {'small': ROOT / 'materials/data/small',
            'b5-fixture': B / 'independent-b5/fixture-data',
            'b6-fixture': B / 'independent-b6-v2/fixture-data',
            'b2-fixture': ROOT / 'artifacts/w03/b2-order-counts-20261108/independent/fixture-data'}
for label, data in datasets.items():
    project = ROOT / f'.runtime/qinghe-b56-{label}-v3'
    assert not project.exists()
    native('load-' + label + '-v3', ['load', '--library', library, '--data', data, '--project', project])
    assert read(project / 'validation.json')['passed']
    print(json.dumps({'loaded': label, 'validation_passed': True}), flush=True)
inputs = {'small-a': ('small', B / 'tests-small-a-frozen.json'),
          'small-b': ('small', B / 'tests-small-b-frozen.json'),
          'b5-fixture': ('b5-fixture', B / 'independent-b5/tests-fixture.json'),
          'b6-fixture': ('b6-fixture', B / 'independent-b6-v2/tests-fixture.json'),
          'b2-fixture': ('b2-fixture', B / 'tests-regression-b2-fixture.json')}
for label, (dataset, source) in inputs.items():
    project = ROOT / f'.runtime/qinghe-b56-{dataset}-v3'
    result = subprocess.run([python, str(B / 'prepare_execution.py'), str(project), str(source),
                             str(B / f'execution-{label}-v3.json'), str(B / f'version-binding-{label}-v3.json')],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
gate = {'passed': True, 'independent_build_review': str((B / 'execution-review/build-review-v3.json').relative_to(ROOT)),
        'independent_regression_precheck': str((B / 'regression-review/pretest-build-review-v3.json').relative_to(ROOT)),
        'all_four_loads_validated': True, 'five_bindings_frozen_before_queries': True,
        'business_expectations_changed': False, 'chat_binding_changed': False,
        'binding_hashes': {str((B / f'version-binding-{label}-v3.json').relative_to(ROOT)):
                           sha(B / f'version-binding-{label}-v3.json') for label in inputs}}
(B / 'execution-query-gate-v3.json').write_text(json.dumps(gate, ensure_ascii=False, indent=2) + '\n')
print('All native loads and frozen bindings ready; no natural-language queries run yet', flush=True)
