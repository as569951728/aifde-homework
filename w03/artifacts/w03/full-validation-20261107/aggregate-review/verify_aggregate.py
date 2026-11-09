from pathlib import Path
import json,hashlib,collections,datetime
root=Path('/Users/chenzhaowen/czw-code/AIFDE/W03/实操工程');repo=root.parents[1];base=root/'artifacts/w03/full-validation-20261107';out=base/'aggregate-review'
def load(p):return json.loads(Path(p).read_text())
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
comp=load(base/'completion.json');led=load(base/'execution_ledger.json');start=load(root/'artifacts/w03/operations-qa-20261107/execution_ledger.json');q=load(root/'artifacts/w03/operations-qa-20261107/input/original_questions.json');qmap={x['id']:x for x in q['cases']};checks=[];evidence={};rows=[];reviews={}
def ck(name,condition,detail=None):checks.append({'check':name,'passed':bool(condition),'detail':detail})
def file(p):p=root/p if not Path(p).is_absolute() else Path(p); evidence[str(p)]=h(p);return p
ck('85_unique_ids',len(led['cases'])==len({x['id']for x in led['cases']})==85)
ck('ids_equal_original_question_registry',{x['id']for x in led['cases']}==set(qmap))
newnames={x['batch']for x in comp['batches']};newids=set();oldids={x['id']for x in start['cases']if x.get('model_sha256')==comp['candidate_model_sha256'] and x['input_track']!='artifact_review'}
new_runs=[];new_http=0
for lc in led['cases']:
 cid=lc['id'];ck(cid+'_input_track_original',lc['input_track']==qmap[cid]['input_track'])
 if lc['input_track']=='artifact_review':continue
 rp=file(lc['evidence']);batch=rp.parent.parent
 if str(rp) not in reviews:reviews[str(rp)]=load(rp)
 rev=reviews[str(rp)];cs=rev.get('cases',rev.get('case_results',[]));rc=next(x for x in cs if x.get('id',x.get('case_id'))==cid)
 v=rc.get('verdict',rc.get('status'));norm='pass' if v in ['pass','passed'] else 'semantic_failure';norm='output_protocol_failure' if rc.get('failure_kind')=='output_protocol' else norm
 ip=file(batch/'run_index.json');idx=load(ip);ir=next(x for x in idx['cases']if x['id']==cid)
 protocol=rc.get('protocol',{});run=rc.get('native_run',rc.get('run',protocol.get('run_path',ir['run'])));runpath=file(run);runj=load(runpath)
 ck(cid+'_index_run',run==ir['run'] or (batch.name=='basic-semantics-qa-20261107' and cid=='B04'),{'review_run':run,'index_run':ir['run']})
 for z in runj.get('outputs',[]):ck(cid+'_native_output_'+Path(z['path']).name,h(file(z['path']))==z['sha256'])
 bodyinputs=[z for z in runj.get('inputs',[])if z['path'].endswith('business_model.md')]
 ck(cid+'_native_body_hash',bool(bodyinputs) and all(h(file(z['path']))==z['sha256']==comp['candidate_model_sha256'] for z in bodyinputs))
 answerpath=runpath.parent/'answer.json';accepted=answerpath.exists() and runj['status']=='succeeded'
 ck(cid+'_answer_acceptance',accepted==(norm!='output_protocol_failure'))
 op=rc.get('output_path',rc.get('original_output',protocol.get('output_path',str(batch/'output'/f'{cid}.json'))));op=file(op);oj=load(op)
 expectedhash=rc.get('output_sha256',rc.get('original_output_sha256',protocol.get('output_sha256')))
 if expectedhash:ck(cid+'_review_output_hash',h(op)==expectedhash)
 if accepted:
  raw=load(answerpath).get('answer');actual=oj.get('actual_answer');ck(cid+'_wrapper_native_answer',raw==actual)
  if 'actual_answer' in rc:ck(cid+'_review_raw_answer',raw==rc['actual_answer'])
 at=load(runpath.parent/'attempts.json');attempts=at['attempts']
 ck(cid+'_ledger_score_matches_review',('pass_in_' in lc['status'] if norm=='pass' else ('semantic_failure' in lc['status'] or 'needs_revision' in lc['status'] or 'output_protocol_failure' in lc['status'])))
 ck(cid+'_model_version_ledger',lc.get('model_sha256')==comp['candidate_model_sha256'])
 if rc.get('input_track'):ck(cid+'_review_track',rc['input_track']==lc['input_track'])
 rows.append({'id':cid,'track':lc['input_track'],'verdict':norm,'native_accepted':accepted,'run':str(runpath),'output':str(op),'review':str(rp),'batch':batch.name,'attempt_count':len(attempts)})
 if batch.name in newnames:
  newids.add(cid);new_runs.append(str(runpath));new_http+=len(attempts);ck(cid+'_new_single_attempt',len(attempts)==1 and attempts[0].get('http_status')==200 and attempts[0].get('error') is None)
tracks={}
for t in sorted({x['track']for x in rows}):
 a=[x for x in rows if x['track']==t];tracks[t]={'attempted':len(a),'native_accepted_answers':sum(x['native_accepted']for x in a),'full_pass':sum(x['verdict']=='pass'for x in a),'semantic_failures':sum(x['verdict']=='semantic_failure'for x in a),'output_protocol_failures':sum(x['verdict']=='output_protocol_failure'for x in a)}
failed=[x['id']for x in rows if x['verdict']!='pass'];counts={'attempted':len(rows),'native_accepted':sum(x['native_accepted']for x in rows),'pass':sum(x['verdict']=='pass'for x in rows),'semantic_failures':sum(x['verdict']=='semantic_failure'for x in rows),'protocol_failures':sum(x['verdict']=='output_protocol_failure'for x in rows)}
ck('recomputed_current_counts',counts=={'attempted':82,'native_accepted':81,'pass':71,'semantic_failures':10,'protocol_failures':1},counts)
ck('recomputed_tracks_equal_completion',tracks==comp['counts']['qa_tracks'],tracks)
ck('failure_ids_equal_completion',set(failed)==set(comp['counts']['current_raw_failed_ids']),failed)
ck('starting49_and_new33_disjoint_complete',len(oldids)==49 and len(newids)==33 and not oldids&newids and oldids|newids=={x['id']for x in rows})
ck('new_runs_http_33',len(new_runs)==len(set(new_runs))==new_http==33)
ck('new_raw_pass_fail_27_6',sum(x['verdict']=='pass'for x in rows if x['id']in newids)==27 and sum(x['verdict']=='semantic_failure'for x in rows if x['id']in newids)==6)
for b in comp['batches']:
 batch=root/'artifacts/w03'/b['batch'];rv=file(batch/'independent-review/review.json');ri=file(batch/'run_index.json');nv=file(batch/'independent-review/native-request-review.json');nr=load(nv)
 ck(b['batch']+'_review_hashes',h(rv)==b['review_sha256'] and h(ri)==b['run_index_sha256'] and h(nv)==b['native_review_sha256'])
 ck(b['batch']+'_actual_batch_size',sum(x['batch']==b['batch']for x in rows)==b['cases'])
 # Native audit is independent prior validation. Check every explicit failed flag without importing its semantic score.
 falses=[]
 def flags(x,path=''):
  if isinstance(x,dict):
   for k,v in x.items():
    if k=='checks' and isinstance(v,dict):falses.extend(path+'/'+n for n,z in v.items() if z is False)
    elif k=='failed_checks' and isinstance(v,list) and v:falses.append(path+'/failed_checks')
    else:flags(v,path+'/'+k)
  elif isinstance(x,list):
   for i,v in enumerate(x):flags(v,path+f'/{i}')
 flags(nr);ck(b['batch']+'_native_audit_no_failed_checks',not falses,falses)
sp=file(base/'static-review/review.json');sr=load(sp)
ck('static_current_three_pass',sr['reviewed_candidate']['sha256']==comp['candidate_model_sha256'] and len(sr['case_results'])==3 and all(x['verdict']=='pass'for x in sr['case_results']) and sr['failed_checks']==[] and h(sp)==comp['static_review_sha256'])
for p in comp['protected_files']:ck('protected_'+p['path'],h(file(p['path']))==p['before']==p['after'])
sess=load(file('artifacts/w02/workflows/WF-8d2ebffec9d94a25bc164ae489fe13a0/session.json'));ck('native_still_awaiting_apply',sess.get('status')=='awaiting_apply',{'status':sess.get('status'),'step':sess.get('step')})
pp=file(comp['native_workflow']['pending_proposal']);ck('pending_proposal_old_hash',h(pp)==comp['native_workflow']['pending_proposal_sha256'])
mentorchecks=[]
for m in comp['new_mentor_working_copies']:
 mp=file(m['path']);mrp=file(m['review_path']);mr=load(mrp);cid=m['case_id'];mrc=next((x for x in mr.get('cases',[])if x.get('case_id',x.get('id'))==cid),mr)
 ok=h(mp)==m['sha256'] and h(mrp)==m['review_sha256'] and m['counts_as_model_pass'] is False and cid in failed and not mrc.get('failed_checks')
 ck('mentor_'+cid+'_preserved_and_separate',ok,{'review_status':mrc.get('status',mr.get('status')),'verdict':mrc.get('verdict')});mentorchecks.append({'id':cid,'path':str(mp),'review_path':str(mrp),'review_status':mrc.get('status',mr.get('status')),'counts_as_model_pass':False,'hashes_match':ok})
ck('six_new_mentor_ids',len(mentorchecks)==6 and {x['id']for x in mentorchecks}==newids&set(failed))
for cid,p in [('P09','artifacts/w03/qualification-qa-20261106/independent-review/review-r1.json'),('DQ10','artifacts/w03/date-boundary-qa-20261106/independent-review/review.json')]:
 rp=file(p);hist=load(rp);cs=hist.get('cases',hist.get('case_results',[]));cs=list(cs.values())if isinstance(cs,dict)else cs;rc=next(x for x in cs if x.get('id',x.get('case_id'))==cid);ck('historical_extra_'+cid,rc.get('verdict')in['pass','passed'] and cid in failed,{'path':str(rp),'verdict':rc.get('verdict')})
ck('history73_not_current_pass',comp['counts']['qa_any_historical_full_pass']==counts['pass']+2 and set(comp['counts']['historical_extra_pass_case_ids'])=={'P09','DQ10'})
startcomp=load(file(comp['starting_completion']));ck('cumulative_calls_128_plus33',startcomp['cumulative_model_qa_calls']==128 and comp['cumulative_model_qa_calls']==128+len(new_runs))
for x in comp.get('continuity_updates',[]):
 p=repo/x['path'];backup=base/'before-continuity'/x['path'];ck('continuity_'+x['path'],p.exists() and backup.exists() and h(file(p))==x['after'] and h(file(backup))==x['before'])
ck('ledger_completion_counts_identical',led['counts']==comp['counts']);ck('ledger_hash_matches_completion',h(file(base/'execution_ledger.json'))==comp['execution_ledger_sha256'])
raw={'verified_at':datetime.datetime.now().astimezone().isoformat(),'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'counts':counts,'tracks':tracks,'failed_case_ids':failed,'new_ids':sorted(newids),'new_runs':len(new_runs),'new_http':new_http,'case_evidence':rows,'mentor_copies':mentorchecks,'evidence_hashes':evidence,'audited_completion_sha256':h(base/'completion.json'),'audited_summary_sha256':h(base/'结果速览.md'),'cumulative_call_verification':'Accepted operations baseline128 + independently checked new33 =161; did not re-audit all historical128 requests.'}
(out/'aggregate-check-details.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'counts':counts,'tracks':tracks,'checks':len(checks),'failed_checks':raw['failed_checks'],'new_runs':len(new_runs),'new_http':new_http,'mentor':mentorchecks},ensure_ascii=False,indent=2))
