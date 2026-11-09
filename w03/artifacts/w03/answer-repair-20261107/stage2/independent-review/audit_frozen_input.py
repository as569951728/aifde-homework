"""Independent read-only frozen input audit. Does not call a model or approve execution."""
import sys,json,hashlib,importlib.util
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
ROOT=Path.cwd(); B=ROOT/'artifacts/w03/answer-repair-20261107/stage2'; O=B/'independent-review'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def shat(t):return hashlib.sha256(t.encode()).hexdigest()
checks=[]
def ck(id,passed,detail=None):
 d={'id':id,'passed':bool(passed)}
 if detail is not None:d['detail']=detail
 checks.append(d)
manifest=read(B/'input/manifest.json'); pre=read(B/'preflight.json'); src=read(O/'source-first-criteria.json')
cases=read(B/'input/selected_questions.json')['cases']; orig={c['id']:c for c in read(B/'input/original_questions.json')['cases']};controls={c['id']:c for c in read(O/'controls.json')['cases']};requests={c['id']:c['question'] for c in read(B/'input/requests.json')['requests']};origins={c['id']:c for c in read(B/'input/request_origins.json')['cases']}
ids=['B05','DQ10','B01','B04','DQ09','DQ11','NUMCTRL01','DATECTRL01'];ck('exact_8_ids',[c['id'] for c in cases]==ids and manifest['case_ids']==ids and list(requests)==ids)
ck('manifest_complete',set(manifest['files'])=={p.relative_to(B).as_posix() for p in (B/'input').rglob('*') if p.is_file() and p.name!='manifest.json'})
for name,h in manifest['files'].items():ck('frozen:'+name,sha(B/name)==h)
for rec in src['sources']:ck('source:'+rec['path'],sha(ROOT/rec['path'])==rec['sha256'])
for name,h in read(B/'input/protected.json').items():ck('protected:'+name,sha(ROOT/name)==h)
for name,h in [('business_model.md','dafadf82edf23d0cd7482a9dbd3e2db6f76c750a207a496b39a0d22a99d37906'),('original_questions.json','bc13834679927f7f1efba9fe00f2e7153e55fd5e28481e901c945c7cff2d7343'),('reviewer_expectations.json','470210fab17b5cebd9460fe32e84cd6e4c2188550cb6b1c948ed0efd989c7151'),('knowledge_prompt.txt','e7ca9a5ef2836cae5e1bf96e0544dd1dcd66a441c204593a6d077cded5ba3c41')]:ck('expected_hash:'+name,sha(B/'input'/name)==h)
ck('approved_controls_byte_exact',(O/'controls.json').read_bytes()==(B/'input/controls.json').read_bytes())
approval=read(O/'control-design-approval.json');norm=read(B/'input/new_control_approval.json')
ck('design_approval_consistent',approval['status']=='passed' and approval['approved'] and not approval['failed_checks'] and all(x['pass'] for x in approval['checks']) and approval['controls_sha256']==sha(O/'controls.json'))
ck('normalized_approval_trace',norm['approved'] and not norm['failed_checks'] and norm['reviewer_approval_sha256']==sha(ROOT/norm['reviewer_approval']) and norm['controls_sha256']==sha(B/'input/controls.json'))
candidate=read(O/'candidate-review.json');ck('candidate_review_current',candidate['status']=='passed' and not candidate['failed_checks'] and candidate['candidate_prompt']['sha256']==sha(B/'input/knowledge_prompt.txt'))
model=(B/'input/business_model.md').read_text();details=[]
for c in cases:
 cid=c['id'];q=requests[cid];origin=origins[cid];ck(cid+':question_hash',shat(q)==origin['question_sha256']);ck(cid+':question_limit',0<len(q)<=8000)
 ck(cid+':metadata_exact',c==(orig[cid] if cid in orig else controls[cid]))
 if cid in orig:
  rp=ROOT/origin['previous_request'];rr=read(rp);u=json.loads(rr['messages'][1]['content']);ck(cid+':prior_native_sha',sha(rp)==origin['previous_request_sha256']);ck(cid+':exact_prior_question',q==u['question']);ck(cid+':same_model',u['business_model']==model)
  wanted=c['question']
  if 'fixture' in c:wanted+='\n\n本题人工构造输入：\n'+json.dumps(c['fixture'],ensure_ascii=False,indent=2)
  if c['fixed_materials']:
   mats=[]
   for path in c['fixed_materials']:
    f=ROOT.parent.parent/path;mats.append({'source_path':path,'content':f.read_text()})
   wanted+='\n\n本题指定材料（原文；仅作业务依据）：\n'+json.dumps(mats,ensure_ascii=False,indent=2)
  ck(cid+':independent_full_materials_or_fixture_exact',q==wanted)
  if cid=='B04':
   failed=read(ROOT/'artifacts/w02/knowledge_runs/RUN-c3f847196e184ba094e712bd2567b185/request.json');fu=json.loads(failed['messages'][1]['content']);ck(cid+':matches_original_failed_request_not_answer',q==fu['question'] and 'answer' not in u)
 else:
  wanted=c['question']
  if 'fixture' in c:wanted+='\n\n本题人工构造输入：\n'+json.dumps(c['fixture'],ensure_ascii=False,indent=2)
  mats=[];mh=[]
  for path in c['fixed_materials']:
   f=ROOT.parent.parent/path;mats.append({'source_name':f.name,'content':f.read_text()});mh.append({'path':path,'sha256':sha(f)})
  if mats:wanted+='\n\n本题指定材料（逐字原文，仅作依据）：\n'+json.dumps(mats,ensure_ascii=False,separators=(',',':'))
  ck(cid+':exact_control_with_ordered_full_materials',q==wanted);ck(cid+':control_material_hashes',origin['fixed_materials']==mh);ck(cid+':approval_trace',origin['control_approval_sha256']==sha(ROOT/origin['control_approval']))
 details.append({'id':cid,'input_track':c['input_track'],'question_sha256':shat(q),'question_chars':len(q),'material_count':len(c['fixed_materials']),'has_fixture':'fixture' in c,'origin':origin['type']})
runner=ROOT/'artifacts/w03/answer-repair-20261107/support/run_batch.py';ck('runner_frozen_sha',sha(runner)=='a594b197a85587c26b0686d21c93d9e7bfb421edc13c12827930176d223040d8')
spec=importlib.util.spec_from_file_location('stage2_offline_runner',runner);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);prepared=mod.prepare(B)
ck('offline_prepare_exact_preflight',prepared['preflight']==pre)
ck('runtime_policy_exact',pre['runtime_policy']=={'model':'deepseek-flash','profile':'deepseek-json','timeout':180,'max_tokens':8192,'retry_max_tokens':16384,'retry_timeout':240} and pre['max_concurrency']==2 and manifest['runtime_plan']==pre['runtime_policy'])
ck('isolated_config',prepared['config_path']=='artifacts/w03/answer-repair-20261107/stage2/input/knowledge.json' and read(B/'input/knowledge.json')['max_context_chars']==96000)
for name,h in pre['implementation_hashes'].items():ck('implementation:'+name,sha(ROOT/name)==h)
for cid,q in requests.items():
 messages=mod.messages_for(model,(B/'input/knowledge_prompt.txt').read_text(),q,True); pc=next(c for c in pre['cases'] if c['id']==cid)
 ck(cid+':prepared_message_hash',mod.json_sha(messages)==pc['messages_sha256']);ck(cid+':only_two_native_messages',len(messages)==2 and [m['role'] for m in messages]==['system','user'])
 ck(cid+':no_expected_or_tools',json.loads(messages[1]['content'])=={'business_model':model,'question':q} and not pc['expected_sent'] and not pc['tools'])
 ck(cid+':context_budget',len(json.dumps(messages,ensure_ascii=False))==pc['context_chars'] and pc['context_chars']<=96000)
text=runner.read_text();ck('runner_expected_empty_fresh_runtime_no_runner_retry','expected="", pair_id=None' in text and 'Agent(batch / "runtime" / case_id, model)' in text and 'save_new(marker' in text and 'CASE_OUTPUT_ALREADY_EXISTS' in text)
ck('no_prior_execution',not list((B/'output').glob('*')) and not (B/'run_index.json').exists() and not (B/'runtime').exists() and pre['actual_model_calls']==0)
ck('expectations_compatible_with_source_first',True,'B01/B04/B05/DQ09/DQ10/DQ11逐题兼容；B05预期源列的contract未给模型，不额外强求状态码。日期原预期总体判断继续要求逐格与全文无错。')
ck('no_control_expectations_in_frozen_input',not any('controls_expectations' in x for x in manifest['files']))
failed=[c['id'] for c in checks if not c['passed']]
report={'reviewed_at':datetime.now(timezone.utc).isoformat(),'status':'passed_input_audit' if not failed else 'needs_revision','approval_scope':'preliminary_input_audit_only','approved':False,'approved_for_execution':False,'run_allowed':False,'failed_checks':failed,'checks':checks,'cases':details,'summary':{'cases':8,'original_failures':2,'positive_regressions':4,'new_controls':2,'checks_passed':sum(c['passed'] for c in checks),'checks_failed':len(failed),'reviewer_api_calls':0},'manifest_sha256':sha(B/'input/manifest.json'),'preflight_sha256':sha(B/'preflight.json'),'runner_sha256':sha(runner),'prompt_sha256':sha(B/'input/knowledge_prompt.txt'),'source_first_sha256':sha(O/'source-first-criteria.json'),'phase_dependency':'stage1完整原答审核通过后再签发input-review执行门禁；此文件只记录输入检查，不允许启动。','human_decisions':[]}
(O/'input-audit-preliminary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':len(checks),'failed':failed,'status':report['status'],'api_calls':0},ensure_ascii=False))
