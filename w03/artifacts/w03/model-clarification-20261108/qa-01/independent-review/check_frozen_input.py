"""Read-only independent input audit. Never constructs a model or reads credentials."""
from pathlib import Path
import json,hashlib,datetime,importlib.util,sys
sys.dont_write_bytecode=True
ROOT=Path.cwd();B=ROOT/'artifacts/w03/model-clarification-20261108';P=B/'qa-01';R=P/'independent-review';OLD=ROOT/'artifacts/w03/answer-repair-20261107/stage5-compact-evidence';SUP=ROOT/'artifacts/w03/answer-repair-20261107/support'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ts=lambda s:hashlib.sha256(s.encode()).hexdigest();jsha=lambda v:ts(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')))
checks=[]
def ck(i,v):checks.append({'id':i,'passed':bool(v)})
runner=B/'support/run_batch.py';spec=importlib.util.spec_from_file_location('isolated_read_only_runner',runner);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def prohibited(*a,**k):raise AssertionError('API and credential access forbidden in review')
m.Agent=m.ContextModel=m.read_key=prohibited
ct=m.prepare(P);pre=load(P/'preflight.json');man=load(P/'input/manifest.json');scope=load(B/'scope.json');criteria=load(R/'source-first-criteria.json');ids=['U01','U05','E03','REG01','P01','CTRL02'];cases=ct['cases'];ocs={c['id']:c for c in load(OLD/'input/selected_questions.json')['cases']};ors={c['id']:c for c in load(OLD/'input/requests.json')['requests']};origins={c['id']:c for c in load(P/'input/request_origins.json')['cases']};pcs={c['id']:c for c in pre['cases']}
ck('selected_exact_six',list(cases)==ids==man['case_ids'])
ck('prepare_exact_frozen_preflight',ct['preflight']==pre)
ck('manifest_complete_inventory',set(man['files'])=={f.relative_to(P).as_posix() for f in (P/'input').rglob('*') if f.is_file() and f.name!='manifest.json'})
for rel,h in man['files'].items():ck('frozen:'+rel,sha(P/rel)==h)
for name in ['controls.json','new_control_approval.json','original_questions.json','reviewer_expectations.json','protected.json','knowledge_prompt.txt']:ck('unchanged_stage5:'+name,(P/'input'/name).read_bytes()==(OLD/'input'/name).read_bytes())
ck('original_question_baseline',sha(P/'input/original_questions.json')=='bc13834679927f7f1efba9fe00f2e7153e55fd5e28481e901c945c7cff2d7343')
ck('original_expectation_baseline',sha(P/'input/reviewer_expectations.json')=='470210fab17b5cebd9460fe32e84cd6e4c2188550cb6b1c948ed0efd989c7151')
ck('stage5_prompt_exact',sha(P/'input/knowledge_prompt.txt')=='703da892e1c284843f499b60efad2e95d60849bd5d22595f71270382df607bfe')
for file in ['run_batch.py','audit_results.py']:ck('support_original_bytes:'+file,(B/'support'/file).read_bytes()==(SUP/file).read_bytes())
ck('runner_expected_hash',sha(runner)=='a594b197a85587c26b0686d21c93d9e7bfb421edc13c12827930176d223040d8')
ck('runner_root_adapted_without_edit',m.ROOT==ROOT and m.REPAIR==B)
for rel,h in load(P/'input/protected.json').items():ck('protected:'+rel,sha(ROOT/rel)==h)
for src in criteria['source_hash_checks']:ck('original_source:'+src['path'],sha(ROOT/src['path'])==src['sha256'] and src['matches_prior_source_hash'])
ck('same_criteria',criteria['criteria_changed'] is False and criteria['case_ids']==ids)
ck('prior_sourcecriteria_hash',sha(ROOT/criteria['original_criteria_path'])==criteria['original_criteria_sha256'])
ck('old_stage5_scores_retained',sha(OLD/'independent-review/review.json')=='10f196e8e078115e813f09a6ecaba71fc4d6d8085511f78e39b2f22e2cc7e299')
oldtext=(OLD/'input/business_model.md').read_text();newtext=ct['document'];transformed=oldtext
for c in scope['changes']:
 ck('unique_declared_model_change:'+str(scope['changes'].index(c)+1),transformed.count(c['before'])==1);transformed=transformed.replace(c['before'],c['after'],1)
ck('only_three_declared_changes',len(scope['changes'])==3 and transformed==newtext)
ck('candidate_exact_frozen_input',(B/'candidate/business_model.md').read_bytes()==(P/'input/business_model.md').read_bytes())
ck('scope_model_hash',sha(P/'input/business_model.md')==scope['candidate_model_sha256']==man['candidate_model_sha256']=='5fb4beed511b19c78333c38252f331c6a2aa159ec654a98eec8703f48d79ffe9')
ck('scope_original_hash',sha(OLD/'input/business_model.md')==scope['original_model_sha256']==man['original_model_sha256'])
config=load(P/'input/knowledge.json');oldconfig=load(OLD/'input/knowledge.json');expected=dict(oldconfig)
for field,name in [('business_model','business_model.md'),('prompt','knowledge_prompt.txt')]:expected[field]=(P/'input'/name).relative_to(ROOT).as_posix()
ck('only_config_isolated_paths',config==expected)
ck('runtime_unchanged',m.POLICY==man['runtime_plan']==pre['runtime_policy']==load(OLD/'preflight.json')['runtime_policy'] and pre['max_concurrency']==2)
for key in ['native_source_hashes','implementation_hashes']:
 for rel,h in pre[key].items():ck(key+':'+rel,sha(ROOT/rel)==h)
controls={c['id']:c for c in load(P/'input/controls.json')['cases']};approval=load(P/'input/new_control_approval.json');design=load(ROOT/approval['reviewer_approval'])
ck('full_control_registry_unchanged',len(controls)==6 and set(controls)&set(ids)=={'CTRL02'})
ck('control_design_frozen_hash',sha(ROOT/approval['reviewer_approval'])==approval['reviewer_approval_sha256'] and sha(P/'input/controls.json')==approval['controls_sha256']==design['controls_sha256'])
ck('control_design_approved',approval['approved'] and design['approved'] and not approval['failed_checks'] and not design['failed_checks'] and all(x['passed'] for x in design['checks']))
ck('requests_only_selected_six',list(ct['requests'])==ids)
review_cases=[]
for i,c in cases.items():
 q=ct['requests'][i]['question'];origin=origins[i];fp=ROOT/origin['previous_request'];oldreq=load(fp);messages=m.messages_for(newtext,ct['prompt'],q,True);body=json.loads(messages[1]['content']);oldbody=json.loads(oldreq['messages'][1]['content']);pc=pcs[i]
 ck(i+':metadata_fixture_materials_exact',c==ocs[i])
 ck(i+':question_exact_stage5',q==ors[i]['question']==oldbody['question'])
 ck(i+':origin_request_hash',sha(fp)==origin['previous_request_sha256'])
 ck(i+':question_hash',ts(q)==origin['question_sha256']==pc['question_sha256'])
 ck(i+':system_prompt_exact',messages[0]==oldreq['messages'][0])
 ck(i+':only_model_variable_in_user',body=={'business_model':newtext,'question':oldbody['question']} and oldbody=={'business_model':oldtext,'question':q})
 ck(i+':only_two_messages',len(messages)==2 and [x['role'] for x in messages]==['system','user'])
 ck(i+':message_hash',jsha(messages)==pc['messages_sha256'])
 ck(i+':within_context_budget',len(json.dumps(messages,ensure_ascii=False))==pc['context_chars']<=config['max_context_chars'])
 ck(i+':no_expected_or_tools',pc['expected_sent'] is False and pc['tools']==[] and set(body)=={'business_model','question'})
 review_cases.append({'id':i,'input_track':c['input_track'],'actual_question_sha256':ts(q),'control':i in controls})
ck('control02_unmodified_comparability_conditions',cases['CTRL02']==controls['CTRL02'] and ct['requests']['CTRL02']['question']==controls['CTRL02']['question'])
ck('original_expectations_not_sent',man['reviewer_expectations_sent'] is False and pre['reviewer_expectations_sent'] is False)
ck('preflight_zero_calls',pre['actual_model_calls']==0)
ck('no_output_or_started_marker',not list((P/'output').glob('*')))
ck('no_native_for_new_config',not any(load(f).get('config_path')==ct['config_path'] for f in (ROOT/'artifacts/w02/knowledge_runs').glob('*/settings.json')))
ck('no_gate_signed_yet',not (P/'gate_acceptance.json').exists())
failed=[x['id'] for x in checks if not x['passed']]
crpath=B/'independent-review/candidate-review.json'
if failed or not crpath.exists():
 print(json.dumps({'status':'needs_revision' if failed else 'mechanical_pass_pending_candidate_review','checks':len(checks),'failed_checks':failed,'approved_for_execution':False,'run_allowed':False,'candidate_review_exists':crpath.exists()},ensure_ascii=False));sys.exit(1 if failed else 0)
cr=load(crpath)
print('CANDIDATE_REVIEW',json.dumps({'keys':list(cr),'status':cr.get('status'),'sha256':sha(crpath)},ensure_ascii=False))
# Final approval is written only after the reviewer reads and confirms this exact candidate report.
print(json.dumps({'status':'mechanical_pass_ready_for_candidate_report_confirmation','checks':len(checks),'failed_checks':[],'candidate_review_sha256':sha(crpath),'manifest_sha256':sha(P/'input/manifest.json'),'preflight_sha256':sha(P/'preflight.json')},ensure_ascii=False))
ck('candidate_review_announced_hash',sha(crpath)=='279b11cf32fbb7bd22963ab2238a190aafd8a5a607c156ddbbf45c45d3683c8b')
ck('candidate_source_approval_consistent',cr['status']=='source_review_pass' and not cr['failed_checks'] and not cr['blocking_findings'] and not cr['requires_candidate_revision'] and not cr['requires_new_business_decision'])
ck('candidate_semantic_checks_pass',all(x['status']=='pass' for x in cr['checks']) and all(cr['mechanical_checks'].values()))
ck('candidate_review_exact_model',cr['candidate']['sha256']==sha(P/'input/business_model.md') and cr['baseline']['sha256']==sha(OLD/'input/business_model.md'))
ck('fresh_source_criteria_bound',sha(B/'independent-review/source-criteria.json')==cr['source_criteria']['sha256'])
ck('candidate_diff_bound',sha(B/'candidate/model.diff')==cr['author_diff']['sha256'])
ck('candidate_does_not_prejudge_live_result',cr['new_test_results'] is None and cr['model_api_calls']==0 and cr['execution_approval'].startswith('not_assessed'))
failed=[x['id'] for x in checks if not x['passed']]
assert not failed,failed
d={'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'client_date':'2026-11-08','status':'approved_for_execution','approved':True,'approved_for_execution':True,'run_allowed':True,'status_checks_prose_consistent':True,'failed_checks':[],'checks':checks,'summary':{'selected_cases':6,'original_cases':5,'selected_controls':1,'registered_control_metadata':6,'checks_passed':len(checks),'checks_failed':0,'reviewer_api_calls':0},'cases':review_cases,'model_sha256':sha(P/'input/business_model.md'),'candidate_prompt_sha256':sha(P/'input/knowledge_prompt.txt'),'runner_sha256':sha(runner),'audit_support_sha256':sha(B/'support/audit_results.py'),'manifest_sha256':sha(P/'input/manifest.json'),'preflight_sha256':sha(P/'preflight.json'),'requests_sha256':sha(P/'input/requests.json'),'candidate_review_path':crpath.relative_to(ROOT).as_posix(),'candidate_review_sha256':sha(crpath),'source_criteria_sha256':sha(B/'independent-review/source-criteria.json'),'reused_qa_criteria_sha256':sha(R/'source-first-criteria.json'),'control_design_review_sha256':approval['reviewer_approval_sha256'],'prior_score_report_sha256':sha(OLD/'independent-review/review.json'),'sole_tested_variable':'Only business-model text: title/date, existing three population names listed, source-attributed 80万/120万 statement distinguished from concrete statistical properties pending verification.','execution_contract':'Each selected case one fresh native run; expected empty; no tools or old answers. Native confirmed length expansion only under unchanged8192/16384 and180/240 policy, counted as HTTP separately. No semantic/format rerun. Network no-answer recovery requires separate review.','prose':'批准当前冻结的U01/U05/E03/REG01/P01/CTRL02六题各执行一次。候选来源审核通过不代表问答通过；新正文所有新原答须完整独立判读。未改提示、题目/fixture/材料、原预期、模型API参数或原生解析器。六control只为不变注册表，实际只发送CTRL02，不发送其他五题或预期。','limitations':['六题为有界针对性回归，不代表新正文82题通过或未见题泛化。','附带原文/合成题分轨，不计正文独立记忆或客户事实。','正式v0.4、现用提示、Skill和11月7日封包及分数保留。'],'human_decisions':[]}
(R/'input-review.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(R/'input-review.md').write_text('# QA-01 执行前独立门禁\n\n**批准冻结的U01/U05/E03/REG01/P01/CTRL02六题各执行一次。** `status=approved_for_execution`，`approved/approved_for_execution/run_allowed=true`，'+str(len(checks))+'项检查全部通过，`failed_checks=[]`；签前0调用、0输出。\n\n唯一测试变量是正文三处澄清：标题日期、原三类人群列表化、已取得角色说法与统计属性待核分开。新的独立来源评审通过，模型hash与审查hash已绑定。原六题实际question、fixture及附加原文、Stage5提示、原82题与预期均未改；两支运行/审计脚本逐字复制，只有相对路径自然指向新隔离目录。\n\n独立只读prepare与preflight一致。逐题system消息与Stage5相同，user消息只有business_model变量变化；expected/预期及tools不进入请求。六个control元数据原样保留，但只选择并发送CTRL02；不存在六个control都被执行的问题。12个正式保护文件及17份判据原材料hash核对通过，旧Stage5成绩不变。\n\n执行后逐题审整份原答和原生请求/格式，按实际HTTP次数记账。框架原定length扩容另计；语义/格式不重抽，无答网络恢复另审。六题结果不能证明全82题回归、正式采用或生产效果。\n')
print(json.dumps({'status':d['status'],'checks':len(checks),'failed_checks':[],'input_review_sha256':sha(R/'input-review.json'),'md_sha256':sha(R/'input-review.md'),'runner_sha256':d['runner_sha256'],'manifest_sha256':d['manifest_sha256'],'preflight_sha256':d['preflight_sha256']},ensure_ascii=False))
