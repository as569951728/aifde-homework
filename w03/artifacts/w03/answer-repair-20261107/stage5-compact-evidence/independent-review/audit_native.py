"""Independent frozen-request/native-output integrity and strict-format audit; no API."""
import sys,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
R=Path.cwd();A=R/'artifacts/w03/answer-repair-20261107';B=A/'stage5-compact-evidence';O=B/'independent-review';sys.path.insert(0,str(R/'platform'))
from fde_product.natural_knowledge import check_run,check_answer,messages_for,Workspace

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
cs={c['id']:c for c in read(B/'input/selected_questions.json')['cases']};ids=list(cs)
missing=[c for c in ids if not (B/'output'/f'{c}.json').exists()]
if missing:
 print(json.dumps({'status':'pending_outputs','missing':missing}));raise SystemExit(0)
checks=[]
def ck(i,p):checks.append({'id':i,'passed':bool(p)})
reqs={c['id']:c['question'] for c in read(B/'input/requests.json')['requests']};model=(B/'input/business_model.md').read_text();prompt=(B/'input/knowledge_prompt.txt').read_text();index=read(B/'run_index.json');gate=read(B/'gate_acceptance.json');review=read(O/'input-review.json')
ck('all22_complete',index['completed_case_records']==index['total_selected']==22 and not index['pending_case_ids'] and [c['id'] for c in index['cases']]==ids)
ck('gate_signature_exact',gate['approved'] and not gate['failed_checks'] and gate['input_review_sha256']==sha(O/'input-review.json') and review['run_allowed'] and review['approved_for_execution'] and review['failed_checks']==[])
for n,h in read(B/'input/manifest.json')['files'].items():ck('frozen:'+n,sha(B/n)==h)
for n,h in read(B/'input/protected.json').items():ck('protected:'+n,sha(R/n)==h)
summary={'native_runs':0,'http_attempts':0,'native_successes':0,'format_failures':0,'no_public_response':0,'framework_length_expansions':0,'semantic_retries':0}
case_results=[]
for cid in ids:
 out=B/'output'/f'{cid}.json';d=read(out);p=R/d['result']['run'];run,settings,_,_=check_run(Workspace(R),d['result']['run']);request=read(p.parent/'request.json');ats=read(p.parent/'attempts.json')['attempts'];msgs=messages_for(model,prompt,reqs[cid],True)
 summary['native_runs']+=1;summary['http_attempts']+=len(ats);summary['native_successes']+=run['status']=='succeeded'
 ck(cid+':native_live_structure',run['mode']=='live' and d['native_structure_check']=='passed' and not d['runner_errors'])
 ck(cid+':case_identity',d['question']==cs[cid]['question'] and d['fixture']==cs[cid].get('fixture') and d['fixed_materials']==cs[cid]['fixed_materials'])
 ck(cid+':exact_question',settings['question']==reqs[cid]);ck(cid+':empty_expected_no_tools',settings['expected']=='' and settings['include_knowledge'] is True and not request.get('tools'))
 ck(cid+':messages_exact',request['messages']==msgs);ck(cid+':fresh_config_runtime',settings['config_path']=='artifacts/w03/answer-repair-20261107/stage5-compact-evidence/input/knowledge.json' and (B/'runtime'/cid).exists())
 ck(cid+':profile_unchanged',request['model']=='deepseek-flash' and request['max_tokens']==8192 and request['response_format']=={'type':'json_object'} and request['reasoning_effort']=='low' and request['thinking']=={'type':'enabled'})
 ck(cid+':attempt_count_policy',1<=len(ats)<=2)
 if len(ats)==2:
  permitted=ats[0]['finish_reason']=='length' and ats[0].get('error')=='MODEL_OUTPUT_TRUNCATED'
  ck(cid+':only_declared_length_expansion',permitted);summary['framework_length_expansions']+=bool(permitted)
 for i,at in enumerate(ats):
  expected=dict(request);expected['max_tokens']=8192 if i==0 else 16384
  ck(cid+f':attempt_{i+1}_request_policy',at['request']==expected and at['max_tokens']==expected['max_tokens'] and at['timeout_seconds']==(180 if i==0 else 240))
 ck(cid+':gate_before_start',datetime.fromisoformat(review['reviewed_at'])<=datetime.fromisoformat(gate['signed_at'])<datetime.fromisoformat(d['started_at']))
 ck(cid+':run_index_hash',sha(p)==d['native_run_sha256'] and sha(out)==next(x for x in index['cases'] if x['id']==cid)['output_sha256'])
 for name,h in d['native_files'].items():ck(cid+':native_file:'+name,sha(R/name)==h)
 response_path=p.parent/'response.json';answer_path=p.parent/'answer.json';strict=False;format_error=None
 if response_path.exists():
  response=read(response_path)
  try:
   answer=check_answer(response['message']);strict=True
  except Exception as e:
   format_error=getattr(e,'code',type(e).__name__);summary['format_failures']+=1
  if strict:
   ck(cid+':strict_answer_equals_native_output',answer_path.exists() and answer==read(answer_path) and answer['answer']==d['actual_answer'] and run['status']=='succeeded')
  else:ck(cid+':format_failure_preserved',not answer_path.exists() and d['actual_answer'] is None and run['status']=='failed')
 else:
  summary['no_public_response']+=1;ck(cid+':no_public_response_preserved',not answer_path.exists() and d['actual_answer'] is None and run['status']=='failed')
 case_results.append({'id':cid,'run':d['result']['run'],'run_sha256':sha(p),'output_sha256':sha(out),'request_sha256':sha(p.parent/'request.json'),'response_sha256':sha(response_path) if response_path.exists() else None,'native_status':run['status'],'strict_format_passed':strict,'format_error':format_error,'http_attempts':len(ats),'attempt_outcomes':[{k:at.get(k) for k in ['http_status','finish_reason','error','max_tokens','timeout_seconds']} for at in ats]})
failed=[c['id'] for c in checks if not c['passed']];summary.update(checks_passed=len(checks)-len(failed),checks_failed=len(failed))
report={'status':'passed' if not failed else 'needs_revision','reviewed_at':datetime.now(timezone.utc).isoformat(),'summary':summary,'cases':case_results,'checks':checks,'failed_checks':failed,'run_index_sha256':sha(B/'run_index.json'),'candidate_prompt_sha256':sha(B/'input/knowledge_prompt.txt'),'model_sha256':sha(B/'input/business_model.md'),'strict_parser_unchanged':True,'reviewer_api_calls':0,'scope':'输入、原生完整性和原始公开response严格格式；语义另按两名独立评审分工判读。格式失败不从正确JSON前缀取答，不修改raw。'}
(O/'native-request-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(O/'native-request-review.md').write_text('# 最终阶段原生输入与严格格式独立核查\n\n'+json.dumps(summary,ensure_ascii=False)+'\n\n输入完整性失败项：'+json.dumps(failed,ensure_ascii=False)+'。逐题核实际model/question/prompt、expected空、无tools、每次HTTP参数和原生文件SHA；原始公开response由未改严格解析器核验，不裁剪尾部或修答案。该报告不代替语义判断，评审0API。\n')
print(json.dumps({'status':report['status'],'summary':summary,'native_review_sha256':sha(O/'native-request-review.json')},ensure_ascii=False))
