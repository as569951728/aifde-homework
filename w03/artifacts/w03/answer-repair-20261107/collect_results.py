"""Collect independently graded new runs. Does not run or score the model."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
STAGES = ['stage1', 'stage1-r2', 'stage2-r2', 'stage3-r2', 'stage4-evidence-trace', 'stage5-compact-evidence']

def read(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save_new(path, value):
    with path.open('x') as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    original = read(BASE / 'stage1/input/original_questions.json')
    original_ids = {x['id'] for x in original['cases'] if x['input_track'] != 'artifact_review'}
    before = ROOT / 'artifacts/w03/full-validation-20261107/completion.json'
    baseline = read(before)
    rows, batches = [], []
    for stage in STAGES:
        path = BASE / stage
        review_path = path / 'independent-review/review.json'
        review = read(review_path)
        grades = {x['id']: x for x in review['cases']}
        audit = read(path / 'protocol_audit.json')
        audited = {x['id']: x for x in audit['cases']}
        selected = read(path / 'input/selected_questions.json')['cases']
        assert set(grades) == set(audited) == {x['id'] for x in selected}
        assert audit['index_errors'] == []
        manifest = read(path / 'input/manifest.json')
        for relative, expected in manifest['files'].items():
            assert sha(path / relative) == expected
        stage_rows = []
        for case in selected:
            cid = case['id']
            output_path = path / 'output' / (cid + '.json')
            output = read(output_path)
            g, a = grades[cid], audited[cid]
            assert sha(output_path) == g['output_sha256'] == a['output_sha256']
            assert a['errors'] == []
            native = ROOT / output['result']['run']
            assert sha(native) == g['native_run_sha256']
            if g['verdict'] == 'passed':
                assert output['status'] == 'succeeded' and isinstance(output['actual_answer'], str)
            row = {'stage': stage, 'id': cid, 'input_track': case['input_track'],
                'case_origin': 'original_82' if cid in original_ids else 'independent_control',
                'verdict': g['verdict'], 'native_status': output['status'],
                'http_attempts': a['api_attempt_count'],
                'output': str(output_path.relative_to(ROOT)), 'output_sha256': sha(output_path),
                'native_run': str(native.relative_to(ROOT)), 'native_run_sha256': sha(native),
                'review': str(review_path.relative_to(ROOT)), 'review_sha256': sha(review_path),
                'model_sha256': sha(path / 'input/business_model.md'),
                'prompt_sha256': sha(path / 'input/knowledge_prompt.txt')}
            rows.append(row)
            stage_rows.append(row)
        batches.append({'stage': stage, 'native_runs': len(stage_rows),
            'http_attempts': sum(x['http_attempts'] for x in stage_rows),
            'native_successes': sum(x['native_status'] == 'succeeded' for x in stage_rows),
            'verdicts': dict(Counter(x['verdict'] for x in stage_rows)),
            'prompt_sha256': sha(path / 'input/knowledge_prompt.txt'),
            'review_sha256': sha(review_path), 'audit_sha256': sha(path / 'protocol_audit.json'),
            'manifest_sha256': sha(path / 'input/manifest.json'),
            'gate_sha256': sha(path / 'gate_acceptance.json')})
    final = {x['id']: x for x in rows if x['stage'] == STAGES[-1]}
    closure_ids = baseline['counts']['current_raw_failed_ids'] + ['U04', 'TRACECTRL01']
    closure = [{'id': cid, 'historical_failure_retained': True,
                'origin': {'U04': 'stage1_regression', 'TRACECTRL01': 'stage4_control_failure'}.get(cid, 'prior_full_suite'),
                'final_verdict': final[cid]['verdict'], 'evidence': final[cid]} for cid in closure_ids]
    final_original = set(final) & original_ids
    ledger = {'recorded_at': datetime.now(timezone.utc).isoformat(),
        'baseline_completion': str(before.relative_to(ROOT)), 'baseline_completion_sha256': sha(before),
        'baseline_counts_unchanged': baseline['counts'], 'batches': batches, 'executions': rows,
        'failure_closure': closure,
        'counts': {'native_runs': len(rows), 'http_attempts': sum(x['http_attempts'] for x in rows),
            'successful_native_answers': sum(x['native_status'] == 'succeeded' for x in rows),
            'unique_original_questions': len({x['id'] for x in rows if x['case_origin'] == 'original_82'}),
            'unique_controls': len({x['id'] for x in rows if x['case_origin'] == 'independent_control'}),
            'all_run_verdicts': dict(Counter(x['verdict'] for x in rows)),
            'final_prompt_tests': len(final), 'final_prompt_original_questions': len(final_original),
            'final_prompt_independent_controls': len(set(final) - original_ids),
            'original_questions_not_rerun_on_final_prompt': len(original_ids - final_original)},
        'final_prompt_untested_original_ids': sorted(original_ids - final_original),
        'original_failure_grades_overwritten': False,
        'no_cross_version_82_pass_claim': True,
        'unexecuted_batches': ['stage1-network-recovery', 'stage2', 'stage3', 'stage4-network-recovery'],
        'formal_model_applied': False, 'formal_prompt_or_skill_replaced': False,
        'metric_queries_executed': 0}
    save_new(BASE / 'execution_ledger.json', ledger)
    print(json.dumps(ledger['counts'], ensure_ascii=False))

if __name__ == '__main__':
    main()
