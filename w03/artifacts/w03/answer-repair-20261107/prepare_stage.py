"""Freeze repair inputs using exact historical questions; never calls a model."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
OLD = ROOT / 'artifacts/w03/context-application-qa-20261107/input'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text())

def save(path, value):
    assert not path.exists(), str(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage')
    parser.add_argument('--ids', nargs='+', required=True)
    parser.add_argument('--controls', type=Path, required=True)
    parser.add_argument('--control-approval', type=Path)
    args = parser.parse_args()
    args.controls = args.controls.resolve()
    if args.control_approval:
        args.control_approval = args.control_approval.resolve()
    batch = BASE / args.stage
    inp = batch / 'input'
    inp.mkdir(parents=True, exist_ok=True)
    (batch / 'output').mkdir(exist_ok=True)
    assert not (inp / 'manifest.json').exists(), 'already frozen'
    controls = read(args.controls)
    if isinstance(controls, list):
        controls = {'cases': controls}
    if controls['cases']:
        assert args.control_approval is not None
        approval = read(args.control_approval)
        assert approval['approved'] is True and not approval['failed_checks']
        assert approval['controls_sha256'] == sha(args.controls)
    original = read(OLD / 'original_questions.json')
    indexed = {c['id']: c for c in original['cases']}
    baseline = read(ROOT / 'artifacts/w03/full-validation-20261107/aggregate-review/aggregate-check-details.json')
    evidence = {x['id']: x for x in baseline['case_evidence']}
    selected = [indexed[i] for i in args.ids]
    selected += controls['cases']
    assert len(selected) == len({c['id'] for c in selected})
    assert not (set(indexed) & {c['id'] for c in controls['cases']})
    requests, origins = [], []
    for case in selected:
        cid = case['id']
        if cid in indexed:
            native_path = Path(evidence[cid]['run']).parent / 'request.json'
            request = read(native_path)
            user = json.loads(request['messages'][1]['content'])
            assert set(user) == {'business_model', 'question'}
            question = user['question']
            assert question.startswith(case['question'])
            source = {'id': cid, 'type': 'exact_previous_native_question',
                      'previous_request': str(native_path.relative_to(ROOT)),
                      'previous_request_sha256': sha(native_path)}
        else:
            question = case['question']
            if 'fixture' in case:
                question += '\n\n本题人工构造输入：\n' + json.dumps(case['fixture'], ensure_ascii=False, indent=2)
            source = {'id': cid, 'type': 'independent_control',
                      'control_approval': str(args.control_approval.relative_to(ROOT)),
                      'control_approval_sha256': sha(args.control_approval)}
            materials = []
            source['fixed_materials'] = []
            for relative in case.get('fixed_materials', []):
                path = ROOT.parent.parent / relative
                assert path.is_file(), relative
                materials.append({'source_name': path.name, 'content': path.read_text()})
                source['fixed_materials'].append({'path': relative, 'sha256': sha(path)})
            if materials:
                question += '\n\n本题指定材料（逐字原文，仅作依据）：\n' + json.dumps(materials, ensure_ascii=False, separators=(',', ':'))
        assert 0 < len(question) <= 8000
        source['question_sha256'] = hashlib.sha256(question.encode()).hexdigest()
        requests.append({'id': cid, 'question': question})
        origins.append(source)
    for name in ['business_model.md', 'original_questions.json', 'reviewer_expectations.json', 'protected.json']:
        target = inp / name
        assert not target.exists()
        target.write_bytes((OLD / name).read_bytes())
    for path, expected in read(inp / 'protected.json').items():
        assert sha(ROOT / path) == expected, 'protected file changed: ' + path
    save(inp / 'selected_questions.json', {'cases': selected})
    save(inp / 'controls.json', controls)
    if controls['cases']:
        save(inp / 'new_control_approval.json', {'approved': True, 'failed_checks': [],
            'controls_sha256': sha(inp / 'controls.json'),
            'reviewer_approval': str(args.control_approval.relative_to(ROOT)),
            'reviewer_approval_sha256': sha(args.control_approval),
            'note': 'Reviewer-approved design; this is not execution approval or a model result.'})
    save(inp / 'requests.json', {'requests': requests})
    save(inp / 'request_origins.json', {'cases': origins})
    knowledge = read(OLD / 'knowledge.json')
    knowledge.update(business_model=str((inp / 'business_model.md').relative_to(ROOT)),
                     prompt=str((inp / 'knowledge_prompt.txt').relative_to(ROOT)))
    save(inp / 'knowledge.json', knowledge)
    assert (inp / 'knowledge_prompt.txt').exists()
    save(inp / 'manifest.json', {'date': '2026-11-07',
        'frozen_at': datetime.now(timezone.utc).isoformat(), 'frozen_before_execution': True,
        'case_ids': [c['id'] for c in selected],
        'files': {str(p.relative_to(batch)): sha(p) for p in sorted(inp.rglob('*')) if p.is_file()},
        'runtime_plan': {'model': 'deepseek-flash', 'profile': 'deepseek-json',
            'timeout': 180, 'max_tokens': 8192, 'retry_max_tokens': 16384, 'retry_timeout': 240},
        'tested_input': 'Frozen model and exact prior requests or independently authored controls. Only answer prompt changes.',
        'reviewer_expectations_sent': False,
        'stop_rule': 'No same-version semantic/format retry; preserve any native failure.'})
    print(json.dumps({'stage': args.stage, 'cases': len(selected), 'frozen': True, 'model_calls': 0}))

if __name__ == '__main__':
    main()
