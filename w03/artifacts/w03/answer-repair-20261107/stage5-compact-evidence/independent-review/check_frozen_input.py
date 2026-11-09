"""Independent read-only input audit; writes only review artifacts. No model access."""
from pathlib import Path
import json, hashlib, datetime, importlib.util, sys
sys.dont_write_bytecode=True
ROOT=Path.cwd();BASE=ROOT/'artifacts/w03/answer-repair-20261107';P=BASE/'stage5-compact-evidence';OLD=BASE/'stage4-evidence-trace';R=P/'independent-review'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ts=lambda s:hashlib.sha256(s.encode()).hexdigest();jsha=lambda v:ts(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')))
checks=[]
def ck(i,v):checks.append({'id':i,'passed':bool(v)})
runner=BASE/'support/run_batch.py';spec=importlib.util.spec_from_file_location('frozen_runner_review',runner);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def prohibited(*a,**k):raise AssertionError('No model/credential construction allowed in review')
m.Agent=m.ContextModel=m.read_key=prohibited
context=m.prepare(P);pre=load(P/'preflight.json');manifest=load(P/'input/manifest.json');oldmanifest=load(OLD/'input/manifest.json');cases=context['cases'];ids=list(cases);oldrequests={x['id']:x['question'] for x in load(OLD/'input/requests.json')['requests']};originals={x['id']:x for x in load(P/'input/original_questions.json')['cases']};controls={x['id']:x for x in load(P/'input/controls.json')['cases']};origins={x['id']:x for x in load(P/'input/request_origins.json')['cases']};pre_cases={x['id']:x for x in pre['cases']}
ck('read_only_prepare_exact_preflight',context['preflight']==pre)
ck('exact22_ids_order',ids==oldmanifest['case_ids']==manifest['case_ids'] and len(ids)==22)
ck('manifest_exact_input_inventory',set(manifest['files'])=={f.relative_to(P).as_posix() for f in (P/'input').rglob('*') if f.is_file() and f.name!='manifest.json'})
for rel,expected in manifest['files'].items():ck('frozen:'+rel,sha(P/rel)==expected)
changed={'input/knowledge_prompt.txt','input/knowledge.json'}
for rel in set(manifest['files'])-changed:ck('unchanged_stage4:'+rel,(P/rel).read_bytes()==(OLD/rel).read_bytes())
ck('model_expected_baseline',sha(P/'input/business_model.md')=='dafadf82edf23d0cd7482a9dbd3e2db6f76c750a207a496b39a0d22a99d37906')
ck('original_questions_expected_baseline',sha(P/'input/original_questions.json')=='bc13834679927f7f1efba9fe00f2e7153e55fd5e28481e901c945c7cff2d7343')
ck('expectations_expected_baseline',sha(P/'input/reviewer_expectations.json')=='470210fab17b5cebd9460fe32e84cd6e4c2188550cb6b1c948ed0efd989c7151')
for rel,h in load(P/'input/protected.json').items():ck('protected:'+rel,sha(ROOT/rel)==h)
oldconfig=load(OLD/'input/knowledge.json');config=load(P/'input/knowledge.json');expectedconfig=dict(oldconfig)
for field in ['business_model','prompt']:expectedconfig[field]=expectedconfig[field].replace('stage4-evidence-trace','stage5-compact-evidence')
ck('config_only_isolated_paths',config==expectedconfig)
ck('runner_unchanged_audited',sha(runner)=='a594b197a85587c26b0686d21c93d9e7bfb421edc13c12827930176d223040d8'==pre['runner_sha256'])
ck('runtime_policy_unchanged',manifest['runtime_plan']==m.POLICY==load(OLD/'preflight.json')['runtime_policy']==pre['runtime_policy'])
ck('max_concurrency2',pre['max_concurrency']==2)
ck('expectations_declared_not_sent',manifest['reviewer_expectations_sent'] is False and pre['reviewer_expectations_sent'] is False)
for key in ['native_source_hashes','implementation_hashes']:
 for rel,h in pre[key].items():ck(key+':'+rel,sha(ROOT/rel)==h)
a=(OLD/'input/knowledge_prompt.txt').read_text();b=context['prompt'];start='仅当题目要求';tail='仅当回答涉及金额、比率或多个判定条件时'
ck('only_evidence_branch_changed',a[:a.index(start)]==b[:b.index(start)] and a[a.index(tail):]==b[b.index(tail):])
ck('prompt_really_new',a!=b)
cr=load(R/'candidate-review.json');nr=load(R/'numeric-mechanism-review.json')
ck('source_candidate_announced_hash',sha(R/'candidate-review.json')=='728fea488768120c1909c94d79d0e2ffbd05fde43b7dd5ceec148e6dd82df53d')
ck('source_criteria_announced_hash',sha(R/'source-answer-criteria.json')=='9f768f9a32d5df6a514abbf9cfc64e7377d38a1bd5520eb323a1e916793beeb0')
for name,d in [('source_candidate',cr),('numeric_mechanism',nr)]:
 ck(name+':all_checks',not d['failed_checks'] and all(x['passed'] for x in d['checks']))
 ck(name+':same_prompt',d['candidate_prompt_sha256']==sha(P/'input/knowledge_prompt.txt'))
 ck(name+':only_design_approval',d['status']=='approved_for_frozen_input_review' and not d['approved_for_execution'] and not d['run_allowed'])
ca=load(P/'input/new_control_approval.json');design=load(ROOT/ca['reviewer_approval'])
ck('control_design_hash_matches',sha(ROOT/ca['reviewer_approval'])==ca['reviewer_approval_sha256'])
ck('control_design_approved_consistent',ca['approved'] is True and design['approved'] is True and ca['failed_checks']==design['failed_checks']==[] and all(x['passed'] for x in design['checks']))
ck('six_controls_hash_matches',sha(P/'input/controls.json')==ca['controls_sha256']==design['controls_sha256'])
ck('control_expectations_unchanged',sha(OLD/'independent-review/controls_expectations.json')=='0ffec813232510aeb658bc9986d352f4bdce1408f127328c8242895e8ecb1b32')
ck('prior_criteria_reused_not_rewritten',load(R/'source-answer-criteria.json')['cases']==load(OLD/'independent-review/source-answer-criteria.json')['cases'])
summary_cases=[]
for i,c in cases.items():
 q=context['requests'][i]['question'];pc=pre_cases[i];origin=origins[i];oldoutput=load(OLD/'output'/f'{i}.json');oldnative=load(ROOT/oldoutput['result']['run']);oldrequest=load(ROOT/oldnative['request']['path']);messages=m.messages_for(context['document'],b,q,True)
 ck(i+':metadata_original_or_control',c==(originals|controls)[i])
 ck(i+':actual_question_exact_stage4',q==oldrequests[i])
 ck(i+':question_hash',ts(q)==pc['question_sha256']==origin['question_sha256'])
 ck(i+':prior_native_user_question',json.loads(oldrequest['messages'][1]['content'])['question']==q)
 ck(i+':user_body_exact_stage4',messages[1]==oldrequest['messages'][1])
 ck(i+':system_only_prompt_change',oldrequest['messages'][0]['content'].count(a)==1 and messages[0]['content']==oldrequest['messages'][0]['content'].replace(a,b,1))
 ck(i+':exact_two_roles',len(messages)==2 and [x['role'] for x in messages]==['system','user'])
 body=json.loads(messages[1]['content'])
 ck(i+':only_business_model_question',set(body)=={'business_model','question'} and body['business_model']==context['document'])
 ck(i+':expected_tools_never_added',pc['expected_sent'] is False and pc['tools']==[] and 'expected' not in body and 'tools' not in body)
 ck(i+':actual_message_hash',jsha(messages)==pc['messages_sha256'])
 ck(i+':context_within_budget',len(json.dumps(messages,ensure_ascii=False))==pc['context_chars']<=config['max_context_chars'])
 if 'previous_request' in origin:
  fp=ROOT/origin['previous_request'];ck(i+':historical_origin_hash',sha(fp)==origin['previous_request_sha256']);ck(i+':historical_origin_question',json.loads(load(fp)['messages'][1]['content'])['question']==q)
 else:ck(i+':independent_control_unchanged',i in controls and q==oldrequests[i])
 summary_cases.append({'id':i,'input_track':c['input_track'],'question_sha256':ts(q),'question_chars':len(q),'control':i in controls})
prior=load(OLD/'independent-review/review.json')
ck('stage4_final_result_hash',sha(OLD/'independent-review/review.json')=='627079f872f869d60fba2386313f1a2845ca690305bd0db3ca865cb406c6d1a6')
ck('stage4_failures_preserved',prior['candidate_passed'] is False and prior['summary']['semantic_failed_ids']==['U05','TRACECTRL01'] and prior['summary']['not_assessable_network_ids']==['E01'])
ck('stage4_recovery_not_performed',prior['network_failure']['recovery_calls']==0 and not prior['network_failure']['recovery_approved'])
ck('no_output_or_reserved_case',not list((P/'output').glob('*')))
ck('no_native_for_new_config',not any(load(f).get('config_path')==context['config_path'] for f in (ROOT/'artifacts/w02/knowledge_runs').glob('*/settings.json')))
ck('preflight_zero_calls',pre['actual_model_calls']==0)
ck('no_gate_signed_before_review',not (P/'gate_acceptance.json').exists())
failed=[x['id'] for x in checks if not x['passed']]
if failed:
 print(json.dumps({'status':'needs_revision','failed_checks':failed,'checks':len(checks)},ensure_ascii=False));sys.exit(1)
d={'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'approved_for_execution','approved':True,'approved_for_execution':True,'run_allowed':True,'failed_checks':[],'status_checks_prose_consistent':True,'checks':checks,'summary':{'cases':22,'original_cases':16,'original_failures_included':11,'controls':6,'new_controls':0,'checks_passed':len(checks),'checks_failed':0,'reviewer_api_calls':0},'cases':summary_cases,'candidate_prompt_sha256':sha(P/'input/knowledge_prompt.txt'),'model_sha256':sha(P/'input/business_model.md'),'runner_sha256':sha(runner),'manifest_sha256':sha(P/'input/manifest.json'),'preflight_sha256':sha(P/'preflight.json'),'requests_sha256':sha(P/'input/requests.json'),'candidate_review_sha256':sha(R/'candidate-review.json'),'numeric_mechanism_review_sha256':sha(R/'numeric-mechanism-review.json'),'source_criteria_sha256':sha(R/'source-answer-criteria.json'),'control_design_review_sha256':ca['reviewer_approval_sha256'],'controls_expectations_sha256':sha(OLD/'independent-review/controls_expectations.json'),'prior_result_sha256':sha(OLD/'independent-review/review.json'),'review_assignment':{'numeric_date_format':['DQ10','B05','DQ09','FMTCTRL01'],'source_business':'来源评审负责其他18题，按同判据逐条完整审本版新原答。','native':'本评审核全22 native、实际HTTP和严格格式并合并。'},'stop_rule':'22题各一次新原生run；只允许既定框架length扩容，若发生单记HTTP。语义/格式不重抽，网络无答另审，不在此自动授权。','prose':'批准当前冻结22题各执行一次。Stage4两语义失败及E01网络无答已经固定，是新机制测试的触发；不以旧版通过作本版本成绩。仅证据审查输出结构变更，原题、原期望、业务正文、数学/日期/JSON及运行策略保持。','human_decisions':[]}
(R/'input-review.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(R/'input-review.md').write_text('# Stage5 执行前独立门禁\n\n**批准当前冻结22题各执行一次。** `status=approved_for_execution`，`approved=true`、`approved_for_execution=true`、`run_allowed=true`；'+str(len(checks))+'项检查全部通过，`failed_checks=[]`。\n\nStage4已固定为19通过、U05/TRACECTRL01两语义失败、E01网络无答；同版恢复0调用。旧失败保留，不把旧版通过拼作新版本通过。\n\n本次16道原题+6控制与Stage4逐题实际question、fixture、指定原文和元数据相同，原82题及预期hash未变。只替换证据审查输出分支；模型、来源通则、数学检查、日期模板、严格JSON、未改解析器与固定运行策略保持。来源15项及数学/格式12项机制审核齐备；原控制设计与判据未放宽。\n\n独立只读prepare与冻结preflight精确一致；逐题实际messages仅system中审核过的提示替换，user中的正文与问题字节一致。无预期、旧答案或tools进入输入。全部保护文件、实现hash、隔离配置、并发2及8192/16384固定length策略核对通过。签门禁时本批0调用、0输出、0预占题；不得覆盖原答。\n\n执行后分工18+4完整复审新原答，独立核全22原生记录。语义/格式失败不重抽；无答网络恢复须另审。本门禁不是模型实答通过、正式替换或客户采纳。\n')
print(json.dumps({'status':d['status'],'checks':len(checks),'input_review_sha256':sha(R/'input-review.json'),'md_sha256':sha(R/'input-review.md'),'manifest_sha256':d['manifest_sha256'],'preflight_sha256':d['preflight_sha256']},ensure_ascii=False))
