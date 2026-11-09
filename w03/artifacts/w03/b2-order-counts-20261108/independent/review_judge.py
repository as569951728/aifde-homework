#!/usr/bin/env python3
"""Offline comparator mutation audit using only frozen expected documents."""
import copy
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
ns = {'__name__':'independent_comparator_review'}
exec(compile((ROOT/'customer/w03/judge.py').read_text(), str(ROOT/'customer/w03/judge.py'), 'exec'), ns)
compare=ns['compare']
cases=json.loads((OUT/'tests-new-small.json').read_text())+json.loads((OUT/'tests-fixture.json').read_text())
checks=[]

def check(name, e, a, want):
    result=compare(e,a)
    checks.append({'name':name,'expected_passed':want,'observed_passed':result['passed'],'passed':result['passed']==want,
                   'differences':result['differences']})

for c in cases:
    e=c['expected']
    check(c['id']+' correct',e,copy.deepcopy(e),True)
    a=copy.deepcopy(e); a['rows'].reverse()
    check(c['id']+' reordered rows',e,a,True)
    a=copy.deepcopy(e); a['columns'].reverse(); a['rows']=[list(reversed(r)) for r in a['rows']]
    check(c['id']+' reordered columns',e,a,True)
    for metric in e['intent']['metrics']:
        a=copy.deepcopy(e); ix=a['columns'].index(metric); a['rows'][0][ix]+=1
        check(c['id']+' one wrong '+metric,e,a,False)
    a=copy.deepcopy(e); a['rows'].append(copy.deepcopy(a['rows'][0]))
    check(c['id']+' duplicate group',e,a,False)
    a=copy.deepcopy(e); a['rows']=a['rows'][1:]
    check(c['id']+' missing row',e,a,False)
    if e['intent']['group_by']:
        a=copy.deepcopy(e); a['rows'][0][0]='WRONG_GROUP'
        check(c['id']+' wrong identity',e,a,False)

e=cases[0]['expected']
mutations={
    'wrong status':lambda a:a.update(status='unsupported'),
    'wrong data version':lambda a:a.update(data_version='not-frozen'),
    'wrong end':lambda a:a['intent'].update(end='2026-08-31'),
    'extra filter':lambda a:a['intent']['filters'].append({'field':'order__status','op':'eq','value':'paid'}),
    'missing metric':lambda a:a['intent']['metrics'].pop(),
    'duplicate metric':lambda a:a['intent']['metrics'].append(a['intent']['metrics'][0]),
    'wrong unit':lambda a:a['units'].update(order_count='cents'),
    'missing unit':lambda a:a['units'].pop('paid_order_count'),
    'extra unit':lambda a:a['units'].update(UNKNOWN='count'),
    'duplicate column':lambda a:a['columns'].append(a['columns'][0]),
    'extra column':lambda a:a['columns'].append('UNKNOWN'),
    'wrong row width':lambda a:a['rows'][0].pop(),
    'no rows':lambda a:a.update(rows=[]),
}
for name,mutation in mutations.items():
    a=copy.deepcopy(e); mutation(a); check(name,e,a,False)
for value in (None,True,'32',32.000000001,float('nan'),float('inf')):
    a=copy.deepcopy(e); a['rows'][0][0]=value
    check('count rejects '+repr(value),e,a,False)
a=copy.deepcopy(e); a['rows'][0][0]=32.0; check('equal finite float accepted',e,a,True)
large=copy.deepcopy(e);large['rows'][0][0]=1000000000
a=copy.deepcopy(large);a['rows'][0][0]=1000000001;check('large integer difference one',large,a,False)
empty=next(c['expected'] for c in cases if c['id']=='B2-E01')
a=copy.deepcopy(empty);a['rows'][0][0]=None;check('empty count null not zero',empty,a,False)
locked=copy.deepcopy(e);locked['data_sha256']='synthetic-data-lock';locked['catalog_sha256']='synthetic-library-lock'
for key in ('data_sha256','catalog_sha256'):
    a=copy.deepcopy(locked);a.pop(key);check('missing locked '+key,locked,a,False)
output={'method':'Pure compare on frozen expectations and synthetic corruptions, no actual query or model',
        'total':len(checks),'passed':sum(c['passed'] for c in checks),'failed_checks':[c for c in checks if not c['passed']], 'checks':checks}
(OUT/'judge-reuse-checks.json').write_text(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in output.items() if k!='checks'},ensure_ascii=False))
assert output['passed']==output['total']
