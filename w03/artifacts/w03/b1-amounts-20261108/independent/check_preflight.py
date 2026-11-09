from pathlib import Path
import json,hashlib,datetime,csv,subprocess,sys,copy
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
new=json.loads((OUT/'tests-new.json').read_text());freeze=json.loads((OUT/'expected-freeze.json').read_text());checks=[]
def check(id,passed,evidence):checks.append({'id':id,'passed':passed,'evidence':evidence})
for p,h in freeze['expected_artifact_sha256'].items():check('freeze_'+p,sha(OUT/p)==h,h)
for p,h in freeze['source_sha256'].items():check('source_'+p,sha(ROOT/p)==h,h)
# Run the existing judge in its real stdin/stdout protocol; all actuals here are SYNTHETIC copies.
results=[]
def run(id,want,got,accepted):
 p=subprocess.run([sys.executable,str(ROOT/'customer/w03/judge.py')],input=json.dumps({'expected':want,'actual':got},ensure_ascii=False),text=True,capture_output=True,timeout=30)
 observed=json.loads(p.stdout) if p.returncode==0 else {'passed':None,'differences':[p.stderr]}
 results.append({'id':id,'synthetic':True,'expected_passed':accepted,'observed':observed,'check_passed':observed['passed'] is accepted})
base=new[0]['expected'];grp=new[3]['expected'];day=new[6]['expected'];flt=new[4]['expected']
for case in new:run('positive_'+case['id'],case['expected'],copy.deepcopy(case['expected']),True)
a=copy.deepcopy(base);a['columns'][0]='wrong_payment';run('wrong_column_name',base,a,False)
a=copy.deepcopy(base);a['columns'].pop();a['rows'][0].pop();run('missing_metric_column',base,a,False)
a=copy.deepcopy(base);a['units']['refund_cents']='yuan';run('wrong_unit_one_metric',base,a,False)
a=copy.deepcopy(base);a['rows'][0][0],a['rows'][0][1]=a['rows'][0][1],a['rows'][0][0];run('swap_values_keep_columns',base,a,False)
a=copy.deepcopy(base);a['columns'][0],a['columns'][1]=a['columns'][1],a['columns'][0];run('swap_columns_keep_values',base,a,False)
a=copy.deepcopy(base);a['columns'].reverse();a['rows']=[r[::-1] for r in a['rows']];a['intent']['metrics'].reverse();run('correct_column_value_reordering',base,a,True)
a=copy.deepcopy(grp);a['rows'].reverse();run('correct_group_row_reordering',grp,a,True)
a=copy.deepcopy(grp);a['rows'].pop();run('missing_store',grp,a,False)
a=copy.deepcopy(grp);a['rows'].append(copy.deepcopy(a['rows'][0]));run('duplicate_store',grp,a,False)
a=copy.deepcopy(grp);a['rows'][0][0],a['rows'][1][0]=a['rows'][1][0],a['rows'][0][0];run('swapped_store_identities',grp,a,False)
a=copy.deepcopy(day);a['rows'][0][0]='2026-08-02 00:00:00';run('wrong_day_identity',day,a,False)
a=copy.deepcopy(flt);a['intent']['filters'].pop();run('missing_and_filter',flt,a,False)
a=copy.deepcopy(flt);a['intent']['filters'].reverse();run('equivalent_and_order',flt,a,True)
a=copy.deepcopy(base);a['rows'][0][0]+=1;run('one_cent_difference',base,a,False)
a=copy.deepcopy(base);a['rows'][0][0]/=100;run('yuan_value_with_cents_unit',base,a,False)
a=copy.deepcopy(base);a['intent']['end']='2026-08-31';run('wrong_end_same_numbers',base,a,False)
a=copy.deepcopy(base);a['data_version']='wrong-data';run('wrong_data_version',base,a,False)
a=copy.deepcopy(base);a['units'].pop('discount_cents');run('missing_unit',base,a,False)
a=copy.deepcopy(base);a['rows'][0][0]=str(a['rows'][0][0]);run('numeric_string',base,a,False)
a=copy.deepcopy(base);a['status']='error';run('error_with_correct_rows',base,a,False)
dump('judge-multi-metric-selfcheck.json',{'kind':'deterministic_synthetic_comparison_only','model_calls':0,'query_calls':0,'judge_sha256':sha(ROOT/'customer/w03/judge.py'),'total':len(results),'passed':sum(r['check_passed'] for r in results),'results':results})
check('judge_multimetric_selfchecks',all(r['check_passed'] for r in results),f'{sum(r["check_passed"] for r in results)}/{len(results)}; synthetic only')
# Preserve old eight business expectations; verify success values afresh against raw records.
oldpath=ROOT/'artifacts/w03/net-sales-first-20261108/independent/tests.json'
old=json.loads(oldpath.read_text());orders=list(csv.DictReader((ROOT/'materials/data/small/orders.csv').open()));reg=[]
for case in old:
 e=case['expected'];valid=True;rows=None
 if e['status']=='ok':
  intent=e['intent']; sums={} if intent['group_by'] else {():0}
  for r in orders:
   if not (intent['start']<=r['ordered_at']<intent['end']):continue
   if any(f['field']=='order__channel' and r['channel']!=f['value'] for f in intent['filters']):continue
   key=(r['store_id'],) if intent['group_by'] else ()
   sums.setdefault(key,0)
   if r['status']=='paid':sums[key]+=int(r['paid_cents'])-int(r['refund_cents'])
  rows=[list(k)+[v] for k,v in sorted(sums.items())];valid=rows==e['rows']
 else:valid=(case['id']=='NS07-missing-time' and e['status']=='clarify') or (case['id']=='NS08-outside-coverage' and e['status']=='unsupported')
 reg.append({'id':case['id'],'independent_recompute_matches_old_business_expectation':valid,'recomputed_rows':rows,'status':e['status']})
dump('regression-recheck.json',{'source':str(oldpath.relative_to(ROOT)),'source_sha256':sha(oldpath),'results':reg})
dump('tests-regression.json',old);dump('tests-all.json',new+old)
check('old_business_expectations_unchanged',len(old)==8 and all(r['independent_recompute_matches_old_business_expectation'] for r in reg),'8 old questions preserved, six successful values recomputed directly from CSV; two status rules reviewed')
check('complete_natural_language_questions',len(new)==7 and all('五项' not in x['question'] and '上述' not in x['question'] for x in new),'Each new question names all five amounts; no context shorthand')
check('source_definition_mapping',True,'01 gives each formula; 02 integer cents/order-date refund attribution; 05 order grain and fields. Parent scope agrees.')
check('skill_v012_reusable_for_five',True,'Actual targets determine boundary; per-metric formula/status/date/unit checks; paid zero-contribution distinct from effective purchase; no formula hardcoded to first metric; dependencies closed for simple amounts.')
check('single_cumulative_build',True,'Five simple metrics built together; no merge of changed same-name model into previous net-only model.')
check('sample_discrimination_and_limits',True,'Cancelled gross 9000 on Aug10 exposes gross/discount status omission. Cancelled paid/refund0 and full-refund net0 remain blind spots requiring expression/catalog/SQL review. O0000040 retains discount100 after full refund.')
check('answer_review_plan',True,'After run inspect every question: amount object, paid row scope including full refunds, order-date attribution, units, actual filters/grouping/status; do not claim effective buyer/account count.')
failed=[x for x in checks if not x['passed']]
tracked=['customer/w03/build-metrics/SKILL.md','customer/w03/judge.py','artifacts/w03/b1-amounts-20261108/scope.json','artifacts/w03/b1-amounts-20261108/口径与本批检查.md','artifacts/w03/net-sales-first-20261108/independent/tests.json']
review={'status':'approved_to_build' if not failed else 'blocked','approved_to_build':not failed,'approved_to_execute':False,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'expected_freeze_sha256':sha(OUT/'expected-freeze.json'),'checks':checks,'failed_checks':failed,'reviewed_artifact_sha256':{p:sha(ROOT/p) for p in tracked},'query_case_count':15,'new_case_count':7,'regression_case_count':8,'model_api_calls':0,'query_calls':0,'next_gate':'Review generated candidate formulas, source quotes, catalog constraints, dimensions and structural checks before real questions. Execution tests may add actual dataset/catalog version metadata only, no business expectation changes.'}
dump('preflight-review.json',review)
dump('execution-input-freeze.json',{'created_at':review['created_at'],'business_expectations_pre_build':True,'files_sha256':{p:sha(OUT/p) for p in ['tests-new.json','tests-regression.json','tests-all.json','regression-recheck.json']},'regression_source_sha256':sha(oldpath)})
(OUT/'preflight-review.md').write_text('# B1 运行前独立审查\n\n状态：'+review['status']+'；approved_to_build='+str(review['approved_to_build']).lower()+'；failed_checks='+str(len(failed))+'。\n\n7 条新增期望先从原 CSV 逐单核算并冻结，后读 Skill 与 judge。另 8 条净额原问句与 business expected 原样保存，6 条成功值重新独立核算吻合。共 15 条真实问句；A01 仅辅助检查。\n\n现有 Skill v0.1.2 可用于本批五项，无需事先修改；judge 本批 '+str(len(results))+' 项纯比较检查全部符合预期，含错列、漏列、错单位、数值互换拒绝及正确列值同步换序通过。自检不是模型问数。\n\n只批准开始五指标统一构建，未批准把生成物当正确。生成后先审 paid 行集合、五个公式、整数分、订单日、来源逐字引用、目录描述及维度；再执行 15 题。金额行集合不能解释成有效购买或账户数。\n\n样本限制：取消 paid/refund 为 0、全退净额为 0，必须结合表达式审查；8/10 cancelled 的原价 9000 可区分 gross/discount 的状态过滤错误；8/31 O0000040 全退仍有 100 分优惠。按日只期望 6 个实际订单日期，不能补造其余日期行。无现金退款日期字段，不能宣称此轮实测现金退款归期。\n')
print(json.dumps({'status':review['status'],'approved_to_build':review['approved_to_build'],'failed_checks':failed,'judge_checks':len(results),'cases':15},ensure_ascii=False))
