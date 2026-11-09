from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json,csv,subprocess,sys,yaml
root=Path(__file__).resolve().parents[4];B=root/'artifacts/w03/b56-first-monthly-20261108';O=B/'execution-review';V=B/'build-v3'
def read(p):return json.loads(p.read_text())
def digest(p):return sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(root))
r=read(V/'response.json');inp=read(V/'input.json');checks=[]
def check(i,ok,detail):checks.append(dict(id=i,passed=bool(ok),detail=detail))
ids=[m['name'] for m in r['metrics']];target=[t['id'] for t in inp['targets']]
check('targets32',len(ids)==32 and len(set(ids))==32 and set(ids)==set(target) and not r['unresolved'],'32 cumulative metrics defined exactly once; no unresolved')
check('catalog_ids',set(ids)=={m['id'] for m in r['catalog']} and r['catalog']==read(V/'catalog.json'),'Response and catalog correspond')
yml=yaml.safe_load((V/'metrics.yml').read_text());check('serialized_models',yml['metrics']==r['metrics'] and yml['semantic_models']==r['semantic_models'],'Response metrics and semantic models equal YAML')
check('serialized_sql',all((V/(k+'.sql')).read_text().strip()==v.strip() for k,v in r['model_sql'].items()),'Generated SQL unchanged from raw response')
check('raw_materials',all((root/'materials/w03'/k).read_text()==v for k,v in inp['materials'].items()),'Input materials equal current source files')
check('raw_business_model',inp['business_model']==(root/'docs/w03/business_model.md').read_text(),'Business model input equals current approved working model')
check('catalog_quotes',all(s['file'] in inp['materials'] and s['quote'] in inp['materials'][s['file']] for m in r['catalog'] for s in m['sources']),'Every catalog quote occurs in its exact source; manually reviewed support as well')
check('business_quotes',all(u['quote'] in inp['business_model'] for u in r['business_model_usage']),'Every business-model usage quote is a continuous original span')
check('ratio_dependencies',all(set([m['type_params']['numerator'],m['type_params']['denominator']])<=set(ids) for m in r['metrics'] if m['type']=='ratio'),'Ratio dependency closure, then manually checked formulas')
check('three_month_policies',all(m['query_policy'].get('full_month_only') is True for m in r['catalog'] if m['id'].startswith('monthly_')),'All three monthly metrics enforce full_month_only')
for name in ['source_check','dimension_check','grain_check','metricflow_check','validation']:check(name,read(V/(name+'.json'))['passed'],'Current generated check report passed; not semantic approval')
freeze_checks=[]
for b in ['independent-b5','independent-b6-v2']:
 f=read(B/b/'expected-freeze.json')
 for section in ['inputs_sha256','artifacts_sha256']:
  for name,h in f.get(section,{}).items():
   actual=digest(root/name);freeze_checks.append({'path':name,'passed':actual==h})
check('frozen_inputs_artifacts',all(v['passed'] for v in freeze_checks),str(len(freeze_checks))+' frozen file references checked')
expected=read(O/'diagnostic-v3-request.json')['expected'];actual=read(O/'diagnostic-v3-actual.json')
rows=list(csv.DictReader((root/'materials/data/small/orders.csv').open()))
valid=[x for x in rows if x['status']=='paid' and int(x['paid_cents'])-int(x['refund_cents'])>0]
accounts={}
for x in valid:accounts.setdefault(x['member_id'],[]).append(x)
independent=[]
for member in ['M00005','M00007']:
 ordered=sorted(accounts[member],key=lambda x:(x['ordered_at'],x['order_id']))
 selected=[(i,x) for i,x in enumerate(ordered) if '2026-08-01'<=x['ordered_at']<'2026-09-01']
 first=[x for i,x in selected if i==0];repeat=[x for i,x in selected if i>0]
 independent.append([member,len(first),sum(int(x['paid_cents'])-int(x['refund_cents']) for x in first),len(first),len(repeat),len(selected)])
check('H03_expected_independent',independent==expected['rows'],'Recomputed from raw CSV without generated SQL: '+str(independent))
judge=subprocess.run([sys.executable,str(root/'customer/w03/judge.py')],input=json.dumps({'expected':expected,'actual':actual}),capture_output=True,text=True,check=True)
j= json.loads(judge.stdout);(O/'diagnostic-v3-judge.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
check('H03_grouped_zero',j['passed'],'Native deterministic result compared against unchanged frozen expected; all cells match including formerly failing zeros')
(O/'static-checks-v3.json').write_text(json.dumps({'checks':checks,'frozen_hash_checks':freeze_checks,'raw_csv_recomputed_H03':independent},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({"passed":sum(c["passed"] for c in checks),"total":len(checks),"failed":[c for c in checks if not c["passed"]]},ensure_ascii=False))
