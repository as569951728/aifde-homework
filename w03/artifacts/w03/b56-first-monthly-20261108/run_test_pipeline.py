"""Run fixed native test partitions, preserving all reports and failures."""
import argparse
import json
import subprocess
from pathlib import Path

B = Path(__file__).resolve().parent
ROOT = B.parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('lane', choices=['a', 'b'])
parser.add_argument('--version', default='v3')
args = parser.parse_args()
lanes = {'a': [('small-a', 'small'), ('b5-fixture', 'b5-fixture'), ('b6-fixture', 'b6-fixture')],
         'b': [('small-b', 'small'), ('b2-fixture', 'b2-fixture')]}
gate = json.loads((B / f'execution-query-gate-{args.version}.json').read_text())
assert gate['passed'] is True
for label, dataset in lanes[args.lane]:
    output = B / ('test-' + label + '-' + args.version)
    cases = B / ('execution-' + label + '-' + args.version + '.json')
    project = ROOT / ('.runtime/qinghe-b56-' + dataset + '-' + args.version)
    assert not output.exists(), 'Prior run must not be overwritten'
    command = [str(ROOT / '.venv/bin/python'), '-B', str(ROOT / 'setup/run_with_local_key.py'),
               'w03', 'test', '--project', str(project), '--cases', str(cases), '--output', str(output),
               '--judge-command', str(ROOT / '.venv/bin/python'), str(ROOT / 'customer/w03/judge.py')]
    with (B / ('test-' + label + '-' + args.version + '.log')).open('x') as log:
        run = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    report_path = output / 'metric_test_report.json'
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    print(json.dumps({'partition': label, 'exit_code': run.returncode,
                      'complete': report.get('complete'), 'passed': report.get('passed'),
                      'total': report.get('total')}, ensure_ascii=False), flush=True)
    if run.returncode != 0 or report.get('complete') is not True:
        raise SystemExit(2)
