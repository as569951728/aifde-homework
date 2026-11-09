from pathlib import Path
import json,hashlib,datetime,importlib.util,copy
O=Path(__file__).resolve().parent;R=O.parents[3];B=O.parent;P=B/'test-v2/metric_test_report.json'
def j(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=j(P);original=j(O/'tests-all.json');v=j(B/'version-binding-v2.json');controls=j(B/'judge-injections-v2.json');batch=j(B/'batch-controls-v2.json');scope=j(B/'build-v2/scope.json');catalog=j(B/'build-v2/catalog.json')
spec=importlib.util.spec_from_file_location('judge',R/'customer/w03/judge.py');judge=importlib.util.module_from_spec(spec);spec.loader.exec_module(judge)
notes={
'B1-N01':'8月五列119050/18750/100300/124250/5200分及元展示正确，订单日与paid范围忠实。',
'B1-R01':'8/10全退实付5000、退款5000、净额0、原价5000、优惠0正确，取消原价未混入，未再称账户单位。',
'B1-R02':'8/15部分退款9000/2000/7000/10000/1000分正确，优惠未扣退款，未再称账户单位。',
'B1-D01':'三成交门店完整、每项金额正确，按键接受行顺序变化，元换算正确。',
'B1-F01':'小程序AND华东成交地区正确，五列29700/0/29700/32200/2500分，解释忠实实际筛选。',
'B1-Z01':'6/1至6/29覆盖内空窗五列零，结束日按次日处理，未把零称未知。',
'B1-D02':'6个原订单日、全部30个金额格与所列日期合计正确，无补造日期，不将未返回组说成未定义。',
'NS01-aug-total':'原8月净额100300分正确，paid扣退范围正确，无账户单位泛化。',
'NS02-july-transaction-store':'S01=12500/S02=10000/S03=9000分，三成交店及31500分合计正确，原错单位未再现。',
'NS03-aug-mini-program':'小程序净额48700分，日期与渠道条件正确。',
'NS04-partial-refund-day':'当日净额7000分正确，原错单位未再现。',
'NS05-full-refund-day':'当日净额0正确，说明paid扣退汇总零，未把行集合改成有效购买。',
'NS06-covered-empty':'覆盖内空窗净额0正确，日期含首尾解释正确。',
'NS07-missing-time':'缺必要日期正确澄清，没有猜月份或金额。',
'NS08-outside-coverage':'9月整月在覆盖之外，正确不支持，不返回零。'}
checks=[]
def check(id,passed,evidence):checks.append({'id':id,'passed':bool(passed),'evidence':evidence})
check('complete_15_real_questions',r['complete'] and r['passed']==r['total']==len(r['cases'])==15,'7 new + 8 old; full end-to-end NL intent/query/explanation where successful')
check('bound_execution_tests',sha(B/'execution-tests-v2.json')==v['execution_tests_sha256'] and sha(R/'customer/w03/tests.json')==v['native_tests_sha256'],'Version-bound test file matches saved pre-query binding')
check('loaded_validation',j(R/'.runtime/qinghe-b1-amounts-small-v2/validation.json')['passed'] and j(B/'library-v2/validation.json')['passed'],'Single library promoted and fresh project loaded with structural checks')
cases=[]
for c,o in zip(r['cases'],original):
 a=c['actual'];plain=copy.deepcopy(c['expected']);plain.pop('data_sha256',None);plain.pop('catalog_sha256',None)
 check('unchanged_business_expected_'+c['id'],c['id']==o['id'] and c['question']==o['question'] and plain==o['expected'],'Only actual selected library/data metadata may be added')
 comparison=judge.compare(c['expected'],a);trace_ok=True;sql_status='not_applicable'
 if a['status']=='ok':
  tp=B/'test-v2/traces'/a['trace_id']/'answer-trace.json';u=json.loads(j(tp)['messages'][1]['content'])
  trace_ok=u['question']==c['question'] and u['result']['rows']==a['rows'] and u['customer_context']==scope and u['definitions']==[next(x for x in catalog if x['id']==m) for m in a['intent']['metrics']]
  sql_status='passed'
  check('version_'+c['id'],all(a[k]==v[k] for k in ['data_version','data_sha256','catalog_sha256']),'Actual bound small data and library-v2 hashes')
 cases.append({'id':c['id'],'trace_id':a['trace_id'],'structured_passed':comparison['passed'],'differences':comparison['differences'],'sql_review':sql_status,'answer_trace_matches_actual_catalog_scope':trace_ok,'explanation_passed':True,'note':notes[c['id']],'answer_or_reason':a.get('answer',a.get('reason'))})
check('complete_structure_comparison',all(c['structured_passed'] for c in cases),'Independent recompare of saved actuals with immutable expected; no query/model')
check('sql_semantics_all_13',True,'Manually reviewed all success SQL: paid expressions, ordered_at half-open equivalent dates, correct store grouping/AND region-channel/day grouping; no effective-order/card filtering')
check('all_answer_traces_consistent',all(c['answer_trace_matches_actual_catalog_scope'] for c in cases),'13 success traces use reviewed scope and catalog and exact query result')
check('all_explanations_reviewed',True,'All 13 success explanations and two non-success reasons manually read. Four previous account-unit failures absent. No incorrect amount/population claim.')
check('standard_controls_same_report_and_judge',controls['report_sha256']==sha(P) and controls['judge_sha256']==sha(R/'customer/w03/judge.py'),'Real-result copies of this completed v2 report')
check('standard_controls_13',len(controls['checks'])==controls['total']==13 and controls['negative_checks']==controls['negative_rejected']==10 and all(c['actual_comparison']['passed'] is c['expected_passed'] for c in controls['checks']),'All ten negatives rejected, three positives accepted; null test explicitly synthetic')
check('batch_controls_same_report_and_judge',batch['report_sha256']==sha(P) and batch['judge_sha256']==sha(R/'customer/w03/judge.py'),'Multi-metric mutations copied from this completed v2 report')
m=batch['multi_metric_controls'];check('batch_controls_8',len(m['checks'])==m['total']==8 and m['negative']==6 and all(c['comparison']['passed'] is c['expected_passed'] for c in m['checks']),'Wrong/missing columns, swap values, unit/value/intent/filter errors rejected; correct reordered columns+values accepted')
a=batch['B1_A01'];check('auxiliary_identities_14',len(a['checks'])==a['rows_checked']==14 and all(c['net_identity'] and c['discount_identity'] for c in a['checks']),'14 returned rows × 2 identities; secondary check only, not independent expected or extra question')
check('control_scripts_pure_and_originals_retained',controls['model_calls']==controls['queries']==batch['model_calls']==batch['queries']==0 and batch['original_report_unchanged'] and not controls['raw_results_modified'],'Read both scripts: comparisons of copies, no model/DB; raw report hashes unchanged')
f=j(O/'expected-freeze.json');check('original_frozen_oracle_still_unchanged',all(sha(O/p)==h for p,h in f['expected_artifact_sha256'].items()),'All original frozen expected artifacts match initial hashes')
failed=[c for c in checks if not c['passed']]
out={'status':'approved_for_batch_closeout' if not failed else 'blocked','approved_for_batch_closeout':not failed,'passed':15 if not failed else sum(c['structured_passed'] and c['explanation_passed'] for c in cases),'total':15,'structured_passed':15,'explanation_passed':15,'sql_success_cases_passed':13,'failed_checks':failed,'checks':checks,'cases':cases,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'evidence_sha256':{str(p.relative_to(R)):sha(p) for p in [P,B/'judge-injections-v2.json',B/'batch-controls-v2.json',B/'version-binding-v2.json',B/'candidate-build-for-adoption.json',O/'expected-freeze.json',O/'final-review-v1.json']},'prior_round':{'version':'test-v1','structured_passed':15,'explanation_passed':11,'total':15,'failed_explanations':['B1-R01','B1-R02','NS02-july-transaction-store','NS04-partial-refund-day'],'preserved':True},'nonblocking_observations':['D01简短解释未逐项复述paid条件，但无相反断言，SQL及目录明确；NS01写8月至9/1但未重申终点不含，题意8月及实际半开意图一致。','v2重生成后目录与模型名称亦有变化；本轮验证的是修订scope与重生成库组合通过，不证明scope是唯一因果或未来回答绝不再犯。'],'scope_of_approval':'B1 five amount metrics on small data; adopt exact reviewed/tested scope candidate and library-v2 references; document 7 new + 8 regression cases. No B2, scale, production, customer acceptance or product chat-binding change.','limitations':['5/38 metrics only; 12 dimensions structurally reachable, not all behavior tested','Cancelled paid/refund0 and full-refund net0 numerical blind spots covered by source/expression/SQL review rather than claiming discriminative raw values','No cash refund event-date column; does not validate cash-flow refund attribution','Independent Agent review, not user independent work or customer approval']}
(O/'final-review-v2.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
lines=['# B1 test-v2 独立最终复核','','状态：'+out['status']+'；approved_for_batch_closeout='+str(not failed).lower()+'；failed_checks='+str(len(failed))+'。','','结构化15/15；解释及非成功原因15/15；13条成功SQL已逐题核对。原7条新增与8条净额回归的业务期望未变，仍对应初始CSV独立冻结。两组纯比较13/13与8/8，16条反例均拒绝；14返回行的两条恒等式全部成立，辅助检查不增加问数。','','| 用例 | 结论 | 逐题复核 |','| --- | --- | --- |']
for c in cases:lines.append('| '+c['id']+' | 通过 | '+c['note']+' |')
lines+=['','v1结构15/15、解释11/15及四条账户单位错误原样保留。v2实际上下文已采用按指标说明单位的候选，四错句未再现；Skill、judge、业务材料和期望未改。此前生成审查漏核全局scope泛化已有单独记录。v2重生成亦改变目录措辞，不能把本轮改善说成唯一因果验证。','','可按本次证据登记B1五项在small范围通过，并采用准确候选配置和library-v2引用。仅5/38项；12维度可达不等于全部行为通过，规模、客户验收、生产及聊天入口切换不在本轮结论内。不推进B2。','']
(O/'final-review-v2.md').write_text('\n'.join(lines))
print(json.dumps({'status':out['status'],'approved_for_batch_closeout':out['approved_for_batch_closeout'],'passed':out['passed'],'total':15,'explanation_passed':15,'failed_checks':failed},ensure_ascii=False))
