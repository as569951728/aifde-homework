"""Reuse the reviewed date checker offline; never changes or scores source prose."""
import hashlib
import importlib.util
import json
from pathlib import Path

BATCH = Path(__file__).resolve().parent
ROOT = BATCH.parents[2]
CHECKER = ROOT / 'artifacts/w03/date-consistency-qa-20261107/independent-review/check_date_answer.py'
spec = importlib.util.spec_from_file_location('date_checker', CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
cases = json.loads((BATCH / 'input/selected_questions.json').read_text())['cases']
results = []
readable = ['# 日期补测：原题情境与实际回答', '']
for case in cases:
    record = json.loads((BATCH / 'output' / (case['id'] + '.json')).read_text())
    answer = record['actual_answer']
    result = checker.check_answer(answer, case['fixture']) if answer is not None else {
        'machine_pass': False, 'machine_status': 'native_answer_missing',
        'semantic_review_required': True,
    }
    results.append({'id': case['id'], **result})
    readable += ['## ' + case['id'], '', case['question'], '',
                 '```json', json.dumps(case['fixture'], ensure_ascii=False, indent=2), '```', '',
                 answer if answer is not None else '没有原生合格答复；见保留的失败运行。', '']
report = {'checker_path': str(CHECKER), 'checker_sha256': hashlib.sha256(CHECKER.read_bytes()).hexdigest(),
          'cases': results, 'machine_pass': sum(x['machine_pass'] for x in results),
          'count': len(results), 'source_and_prose_review_separate': True, 'model_calls': 0}
(BATCH / 'machine_results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
(BATCH / 'actual_answers_with_fixtures.md').write_text('\n'.join(readable))
print(json.dumps({'machine_pass': report['machine_pass'], 'count': len(results)}))
