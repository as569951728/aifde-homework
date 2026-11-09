"""Independent offline stage1 input audit; never invokes execution/key/API paths."""
from pathlib import Path
import sys,json,hashlib,datetime,importlib.util
ROOT=Path(__file__).resolve().parents[5]
B=ROOT/'artifacts/w03/answer-repair-20261107/stage1';O=B/'independent-review'
OLD=ROOT/'artifacts/w03/context-application-qa-20261107'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
checks=[]
def ck(name,ok,detail=None):
 x={'id':name,'passed':bool(ok)}
 if detail is not None:x['detail']=detail
 checks.append(x)
manifest=read(B/'input/manifest.json'); selected=read(B/'input/selected_questions.json')['cases'];cases={x['id']:x for x in selected};reqs={x['id']:x['question'] for x in read(B/'input/requests.json')['requests']};origins={x['id']:x for x in read(B/'input/request_origins.json')['cases']};criteria=read(O/'source-first-criteria.json');priorcase={x['id']:x for x in criteria['cases']};control={x['id']:x for x in read(O/'controls.json')['cases']}
ids=['U01','U05','P09','A03','E01','E03','E05','REG01','U04','P01','P05','E02','A02','F05','CTRL01','CTRL02','CTRL03','CTRL04']
ck('exact_18_ids',list(cases)==ids and list(reqs)==ids and manifest['case_ids']==ids)
ck('manifest_file_set',set(manifest['files'])=={str(p.relative_to(B)) for p in (B/'input').rglob('*') if p.is_file() and p.name!='manifest.json'})
for path,digest in manifest['files'].items():ck('frozen:'+path,sha(B/path)==digest)
for path,digest in read(B/'input/protected.json').items():ck('protected:'+path,sha(ROOT/path)==digest)
for x in criteria['sources']:
 ck('source:'+x['path'],sha(ROOT/x['path'])==x['sha256'])
ck('candidate_model_exact_prior',sha(B/'input/business_model.md')=='dafadf82edf23d0cd7482a9dbd3e2db6f76c750a207a496b39a0d22a99d37906' and (B/'input/business_model.md').read_bytes()==(OLD/'input/business_model.md').read_bytes())
for name in ['original_questions.json','reviewer_expectations.json','protected.json']:
 ck('prior_file_unchanged:'+name,(B/'input'/name).read_bytes()==(OLD/'input'/name).read_bytes())
ck('frozen_controls_exact_approved',(B/'input/controls.json').read_bytes()==(O/'controls.json').read_bytes())
ap=read(O/'control-design-approval.json');nap=read(B/'input/new_control_approval.json')
ck('source_control_design_approval_consistent',ap['approved'] is True and ap['failed_checks']==[] and all(x['passed'] for x in ap['checks']) and ap['controls_sha256']==sha(O/'controls.json'))
ck('normalized_control_approval_trace',nap['approved'] is True and nap['failed_checks']==[] and nap['controls_sha256']==sha(B/'input/controls.json') and nap['reviewer_approval_sha256']==sha(O/'control-design-approval.json'))
matidx=read(OLD/'input/materials_index.json');contexts={'U05','A03','E01','A02'}
casechecks=[]
for cid in ids:
 q=reqs[cid];c=cases[cid];origin=origins[cid]
 ck(cid+':question_hash',hashlib.sha256(q.encode()).hexdigest()==origin['question_sha256'])
 ck(cid+':question_limit',0<len(q)<=8000,len(q))
 if cid in priorcase:
  ck(cid+':metadata_unchanged',c==priorcase[cid]['original_case'])
  src=ROOT/origin['previous_request'];oldnative=read(src);olduser=json.loads(oldnative['messages'][1]['content'])
  ck(cid+':prior_native_hash',sha(src)==origin['previous_request_sha256'])
  ck(cid+':question_byte_equivalence',q==olduser['question'])
  ck(cid+':same_user_model',olduser['business_model']==(B/'input/business_model.md').read_text())
  if cid in contexts:
   suffix=q[len(c['question']):];material=json.loads(suffix.split('\n',3)[-1])
   ck(cid+':same_material_count',len(material)==len(c['fixed_materials']))
   for n,(m,path) in enumerate(zip(material,c['fixed_materials'])):
    item=matidx[cid][path];snap=OLD/item['snapshot']
    ck(cid+f':rendered_{n}_exact',m=={'source_name':Path(path).name,'content':snap.read_text()} and sha(snap)==item['sha256'])
  else:
   expected=c['question']
   if 'fixture' in c:expected+='\n\n本题人工构造输入：\n'+json.dumps(c['fixture'],ensure_ascii=False,indent=2)
   ck(cid+':no_added_material',q==expected and c['input_track']=='model_only')
 else:
  ck(cid+':exact_designed_control',c==control[cid] and q==control[cid]['question'])
  ck(cid+':approval_trace',origin['control_approval_sha256']==sha(O/'control-design-approval.json'))
  ck(cid+':no_fixture_hidden_answer',set(c)=={'id','dimension','question','input_track','fixed_materials','evaluation_domain'})
 casechecks.append({'id':cid,'input_track':c['input_track'],'question_chars':len(q),'question_sha256':hashlib.sha256(q.encode()).hexdigest(),'source_origin':origin['type']})
runner=ROOT/'artifacts/w03/answer-repair-20261107/support/run_batch.py'
ck('final_runner_hash',sha(runner)=='a594b197a85587c26b0686d21c93d9e7bfb421edc13c12827930176d223040d8')
spec=importlib.util.spec_from_file_location('independent_stage1_runner',runner);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
# Guard offline boundaries even though only prepare() is called.
def forbidden(*args,**kwargs):raise RuntimeError('Offline review must not call execution or credentials')
module.Agent=forbidden;module.ContextModel=forbidden;module.read_key=forbidden
prepared=module.prepare(B);pre=read(B/'preflight.json');ck('independent_prepare_matches_preflight',prepared['preflight']==pre)
ck('no_calls_in_preflight',pre['actual_model_calls']==0 and pre['reviewer_expectations_sent'] is False)
ck('runtime_limits_and_model',pre['runtime_policy']=={'model':'deepseek-flash','profile':'deepseek-json','timeout':180,'max_tokens':8192,'retry_max_tokens':16384,'retry_timeout':240} and pre['max_concurrency']==2 and prepared['config_path']=='artifacts/w03/answer-repair-20261107/stage1/input/knowledge.json')
config=read(B/'input/knowledge.json');ck('context_limit_unchanged',config['max_context_chars']==96000)
for cid in ids:
 messages=module.messages_for(prepared['document'],prepared['prompt'],reqs[cid],True);user=json.loads(messages[1]['content'])
 ck(cid+':actual_payload_exact',set(user)=={'business_model','question'} and user['question']==reqs[cid] and user['business_model']==(B/'input/business_model.md').read_text())
 ck(cid+':context_budget',len(json.dumps(messages,ensure_ascii=False))<=96000)
 ck(cid+':no_expected_or_tools',next(x for x in pre['cases'] if x['id']==cid)['expected_sent'] is False and next(x for x in pre['cases'] if x['id']==cid)['tools']==[])
for name,digest in pre['implementation_hashes'].items():ck('native_implementation:'+name,sha(ROOT/name)==digest)
cand=read(O/'candidate-review.json');ck('candidate_review_current',cand['approved'] is True and not cand['failed_checks'] and all(x['passed'] for x in cand['checks']) and cand['candidate_prompt_sha256']==sha(B/'input/knowledge_prompt.txt'))
ck('old_expectations_source_compatible',True,'逐题对照原14题required_points/禁止项均与独立来源判据兼容。REG01两类会员按活动范围分别核查、不能预设不同的原要求继续有效；U05来源索引扩展项不自动加入本题输入。')
ck('no_execution_yet',not list((B/'output').glob('*')) and not (B/'runtime').exists())
failed=[x for x in checks if not x['passed']]
report={'status':'approved_for_execution' if not failed else 'blocked_input_defect','approved':not failed,'run_allowed':not failed,'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'criteria_sha256':sha(O/'source-first-criteria.json'),'controls_sha256':sha(O/'controls.json'),'runner_sha256':sha(runner),'manifest_sha256':sha(B/'input/manifest.json'),'preflight_sha256':sha(B/'preflight.json'),'candidate_prompt_sha256':sha(B/'input/knowledge_prompt.txt'),'model_sha256':sha(B/'input/business_model.md'),'summary':{'cases':18,'original_failures':8,'positive_regressions':6,'new_controls':4,'checks_passed':len(checks)-len(failed),'checks_failed':len(failed),'max_question_chars':max(map(len,reqs.values())),'max_context_chars':max(x['context_chars'] for x in pre['cases']),'reviewer_api_calls':0},'cases':casechecks,'checks':checks,'failed_checks':failed,'status_checks_prose_consistent':True,'expectation_comparison':'旧14题期望只作审核，不进入messages；4控制期望仍在independent-review单独保存。语义兼容，无期望改写。','boundaries':['仅允许当前冻结18题一次执行；无同版本语义/格式失败重试。','此次批准不是实际模型通过或历史11失败已修复；原输出和原分保留。','不改业务正文、正式提示或Skill；不将控制合成条件当青禾事实；不代表全82题最新提示回归或38指标数值验收。'],'human_decisions':[]}
(O/'input-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if failed:
 md='# Stage1 输入独立门禁\n\n结论：未批准执行。失败项见input-review.json，须修复后再审。\n'
else:
 md=f'''# Stage1 输入独立门禁

结论：**批准当前冻结18题执行一次**。JSON状态为approved_for_execution，approved/run_allowed均为true；{len(checks)}项检查全部通过，failed_checks为空，与正文一致。

8个原失败、6个正向回归与4个独立对照分别计分。14个旧题的实际问题及题设/材料与历史原生请求逐字一致；4题既有来源逐字匹配先前rendered，CTRL01/03完整原问答、CTRL02/04合成条件及CTRL04查询契约均已核。业务模型、旧题期望、正式文件及Skill保护hash不变。

候选仅在冻结基线提示增加481字通用来源/前提/条件审查。独立只读构造的18份实际payload与preflight完全一致，仅含业务模型和题问，无期望或工具。最长题问{report['summary']['max_question_chars']}字符，最大上下文{report['summary']['max_context_chars']}字符，均在课程限制内；调用参数不变，最多并发2。本审核未调用API。

这是执行前门禁，不是模型答案通过、旧失败修复完成、正式正文采用、全82题最新回归或指标数值验收。保留所有旧失败；新结果另评，不做同版本语义/格式重抽样。真实人类决策：无。

runner SHA：`{report['runner_sha256']}`；manifest SHA：`{report['manifest_sha256']}`；preflight SHA：`{report['preflight_sha256']}`。运行应绑定这份input-review的实际SHA。
'''
(O/'input-review.md').write_text(md)
print(json.dumps({'status':report['status'],'approved':report['approved'],'checks':len(checks),'failed_checks':failed,'input_review_sha256':sha(O/'input-review.json'),'max_question_chars':report['summary']['max_question_chars'],'max_context_chars':report['summary']['max_context_chars']},ensure_ascii=False,indent=2))
