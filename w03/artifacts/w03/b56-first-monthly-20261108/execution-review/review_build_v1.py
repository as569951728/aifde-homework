from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json,csv,subprocess,sys,yaml
root=Path(__file__).resolve().parents[4];B=root/'artifacts/w03/b56-first-monthly-20261108';O=B/'execution-review';V=B/'build-v1'
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
expected=read(O/'diagnostic-v1-request.json')['expected'];actual=read(O/'diagnostic-v1-actual.json')
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
j= json.loads(judge.stdout);(O/'diagnostic-v1-judge.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
check('H03_grouped_zero',j['passed'],'Native deterministic result compared against unchanged frozen expected; four null-versus-zero cells fail')
(O/'static-checks-v1.json').write_text(json.dumps({'checks':checks,'frozen_hash_checks':freeze_checks,'raw_csv_recomputed_H03':independent},ensure_ascii=False,indent=2)+'\n')
fail=[{'id':'B5-08-grouped-zero','severity':'blocking','metrics':['first_buyer_count','first_order_sales_cents','first_order_count','repeat_order_count'],'case_id':'B5-H03','expected_rows':expected['rows'],'actual_rows':actual['rows'],'evidence':[rel(O/'diagnostic-v1.sql'),rel(O/'diagnostic-v1-actual.json'),rel(O/'diagnostic-v1-judge.json')],'reason':'first_valid_orders and repeat_valid_orders remove the other subset before grouping. FULL OUTER JOIN keeps each account but absent submodel columns are NULL. No fill_nulls_with or equivalent generated handling exists; Engine only normalizes simple NULL for ungrouped aggregate. Existing account groups require known business zeros.','required_change':'Regenerate the model with correct conditional metrics over shared retained order rows, or equivalent supported metric-level zero handling; keep raw v1 and frozen expected/judge unchanged. Recheck identical H03 before merge/load.'}]
limitations=[{'id':'B5-filter-dimensions','detail':'first/repeat semantic models expose account/home_store/tier/time, not original order store/channel. No store/channel filtering acceptance is claimed; planned13 only require account filtering and registration grouping.'},{'id':'B6-empty-month-group','detail':'monthly_member_orders only contains months with valid purchases. Frozen B6-Z01 is an ungrouped empty month and Engine additive normalization applies. Grouped queries including an empty month may omit that month; no native empty-month-group query was run. Design review already records no such candidate; not claimed covered.'},{'id':'B6-grain-declaration','detail':'Actual aggregation is member_id+month_start, serialized grain declares synthetic member_month_key. Primary uniqueness passed; explicit two-column grain_keys would better satisfy contract wording for composite grain.'},{'id':'native-explanation','detail':'No natural-language model query or answer generated in this review. Planned47 and new13 complete explanation audits remain pending.'}]
semantic=[('G01','Catalog and model usage source spans and support checked; 02 financial rules also read for old ratios.'),('G02','All32 targets present; ratios have correct closed dependencies.'),('G03','Orders/order_id, members/member_id and stores/store_id; first/repeat per order, monthly per account-month; no card join.'),('G04','Raw dates and full coverage preserved; actual H03 SQL uses Aug1 inclusive to Aug31 inclusive native representation.'),('G05','Old order-store versus member-home-store paths retained; B5 limited dimensions disclosed.'),('G06','Current source/dimension/grain/MetricFlow checks passed; independent blocker overrides.'),('B5-01','Member registration time and distinct member IDs correct.'),('B5-02','Both ranked models filter paid and net>0 before ranking.'),('B5-03','ROW_NUMBER partition member ordered_at,order_id over full source before runtime filters.'),('B5-04','First buyer distinct member from first effective order.'),('B5-05','First order count of rank1 rows; tie ordered by order_id.'),('B5-06','First net value paid-refund in cents from rank1 original order date.'),('B5-07','Repeat rows rank>=2, with own order date.'),('B6-01','Monthly GROUP BY member_id, CAST(date_trunc(month,ordered_at) AS DATE).'),('B6-02','Only valid-order account-month rows; denominator distinct account, not registration.'),('B6-03','Repeat condition valid_order_count>=2, not ==2.'),('B6-04','Ratio monthly_repeat_buyer_count / monthly_buyer_count; dependencies closed.'),('B6-06','All3 full_month_only true, Engine enforces complete month.'),('B6-07','Engine full_month_only rejects filters and non-month groups; channel restriction attributed to implementation contract.'),('B6-08','Engine rejects multi-month ungrouped query and allows month grouping; normal nonzero month grain correct.'),('R01','Old24 measure expressions and 8 financial ratios match source scope and units. Full old regression still required.')]
evidence=[]
for p in V.glob('*'):
 if p.is_file():evidence.append(p)
for name in ['dataset.json','dimensions.json','validation.json','grain_check.json','metricflow_check.json']:evidence.append(V/'validation-project'/name)
for name in ['review-contract.json','review-contract.md','static-checks-v1.json','diagnostic-v1-request.json','diagnostic-v1-actual.json','diagnostic-v1-judge.json','diagnostic-v1.sql','run_diagnostic_v1.py','diagnostic-v1.log','diagnostic-v1-rerun.log']:evidence.append(O/name)
for b in ['independent-b5','independent-b6-v2']:
 for n in ['expected-freeze.json','tests-small.json','tests-fixture.json','design.json']:evidence.append(B/b/n)
evidence += [B/'design-review/final-review-v2.json',B/'design-review/final-review-v2.md']
evidence += [root/p for p in read(O/'review-contract.json')['business_source_sha256']]+[root/'materials/w03/02_财务邮件.md',root/'materials/data/small/orders.csv',root/'platform/fde_product/metrics/engine.py',root/'customer/w03/judge.py']
report={'reviewer':'b56_execution_review','reviewed_at':datetime.now(timezone.utc).isoformat(),'stage':'independent_actual_build_semantic_review','build':'artifacts/w03/b56-first-monthly-20261108/build-v1','status':'changes_requested','approved_for_merge_load':False,'failed_checks':fail,'passed_checks':[{'id':a,'finding':b} for a,b in semantic],'mechanical_checks':{'passed':sum(x['passed'] for x in checks),'total':len(checks),'failed':[x['id'] for x in checks if not x['passed']]},'reviewed_metrics':ids,'diagnostic':{'native_deterministic_queries':1,'model_api_calls':0,'case_id':'B5-H03','ordinary_batch_test_pass':False,'project_copy':rel(O/'diagnostic-v1-project'),'initial_setup_failure':'ModuleNotFoundError before query; log retained; fixed review script root path then 1 actual query','raw_generated_files_modified':False},'limitations':limitations,'evidence_sha256':{rel(p):digest(p) for p in evidence},'next':'Regenerate a separate candidate; independently review changes and rerun unchanged deterministic H03; only then consider merge/load and the47 real-question regression. No changes to expected/judge or original generated files.'}
(O/'build-review-v1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
md=['# B5＋B6 实际构建独立审核 v1','','结论：**不批准 merge/load**。`approved_for_merge_load=false`；`failed_checks` 1项阻断。','', '审核对象 build-v1，累计32指标、0未决；来源、维度、粒度、MetricFlow技术检查均通过。已逐项核对32项原始response、catalog、metrics与派生SQL。设计批准不构成本次语义通过。','','## 已确证问题','B5-H03的两个账户在8月都有有效订单：M00005只有后续单，其首购数、首单金额与首单数应为0；M00007只有首单，其后续单数应为0。','',f'冻结期望：`{expected["rows"]}`',f'实际结果：`{actual["rows"]}`','','原因：首单和后续单分别先过滤成不同事实子集；原生FULL OUTER JOIN保留账户行，却将不存在的子集列留为NULL。生成指标没有补零机制，Engine仅对无分组加总补零，分组结果不能靠judge将NULL改成0。独立重新读原CSV核算，与冻结期望完全一致。','','一次确定性原生查询已保存实际SQL与完整数值响应；没有模型API调用、没有自然语言回答。为保全生成物，查询在execution-review内的项目副本运行。最初脚本根路径导入错误发生在查询前，原日志保留；纠正后仅执行1次查询。','','## 其他审查','B5有效单过滤、全覆盖排序、同日订单号裁决、原订单日期、首单净额和CRM账户去重符合来源。B6先按账户自然月汇总、>=2阈值、同月购买账户分母、比率依赖和full_month_only限制正确。旧24项定义与财务比率未见语义偏移；仍需实际回归。','','## 保留边界']
md += [x['detail'] for x in limitations]
md += ['','## 后续','由构建输入/Skill生成独立新版本，正确表达已有分组内空子集的0；不得手改生成物、期望或judge。保留v1失败，先用同一H03复验，再申请merge/load。47题和新增13题完整解释均尚未通过。','',f'机械证据检查 {report["mechanical_checks"]["passed"]}/{len(checks)}；唯一失败为H03_grouped_zero。来源与产物哈希见 build-review-v1.json。']
(O/'build-review-v1.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'status':report['status'],'approved_for_merge_load':False,'failed_checks':len(fail),'mechanical_checks':report['mechanical_checks'],'reviewed_metrics':len(ids)},ensure_ascii=False))
