import json,hashlib,sys,datetime
from pathlib import Path
OUT=Path(__file__).resolve().parent;B=OUT.parent;ROOT=OUT.parents[3]
p=OUT/'case-review-progress.json';doc=json.loads(p.read_text()) if p.exists() else {'status':'in_progress','cases':{}}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((B/'library-v1/catalog.json').read_text());name_to_id={x['name']:x['id'] for x in catalog}
# Only called for ids whose entire SQL and answer have been manually read, plus trace binding checked below.
ns={'__name__':'judge_review'};exec(compile((ROOT/'customer/w03/judge.py').read_text(),'judge.py','exec'),ns)
requested=set(sys.argv[1:]);n=0
for name in ['test-new-v1','test-regression-v1','test-fixture-v1']:
 rp=B/name/'metric_test_report.json'
 if not rp.exists():continue
 for c in json.loads(rp.read_text())['cases']:
  if c['id'] not in requested:continue
  a=c['actual'];trace=B/name/'traces'/a['trace_id'];artifacts=[trace/'result.json'];checks={}
  checks['numeric_and_complete_intent']=ns['compare'](c['expected'],a)['passed']
  if a['status']=='ok':
   tp=trace/'answer-trace.json';t=json.loads(tp.read_text());reply=json.loads(t['reply']['content']);payload=json.loads(t['messages'][1]['content']);artifacts.append(tp)
   checks.update(answer_matches_trace=reply['answer']==a['answer'],trace_used_metrics={name_to_id.get(x,x) for x in reply['used_metrics']}==set(a['intent']['metrics']),trace_cites_actual=reply['citations']==['当前执行结果'],trace_question=payload['question']==c['question'],trace_payload_fields=all(payload['result'][k]==a[k] for k in payload['result']),trace_catalog=payload['definitions']==[x for x in json.loads((B/'library-v1/catalog.json').read_text()) if x['id'] in a['intent']['metrics']])
  else: checks['non_ok_has_reason']=bool(a.get('answer') or a.get('reason'))
  assert all(checks.values()),(c['id'],checks)
  issue=None
  if c['id']=='B3-U01':issue=dict(kind='explanation_scope_error',quote='退款会员数按发生退款的有效已支付订单关联的不同会员账户计数',expected='所有paid且refund_cents>0的CRM账户，包括全退；不是仅有效订单',effect='原7–8月退款账户5个；限定有效退款订单将只有M00002/M00006/M00008共3个，遗漏M00003/M00017全退账户。',repair='保留本轮原文；可基于同一真实结果、来源与明确反馈做独立回答审校回放。单独记录人工反馈修订，不改期望、SQL、生成库或首轮分，不冒充原生新问数/自动系统修复。若修产品方法才需重新构建并回归。')
  if c['id']=='B1-Z01':issue=dict(kind='explanation_half_open_time_error',quote='本次实际执行采用的业务日期范围为2026年6月1日至6月30日，未单独截断到6月29日',expected='intent为[2026-06-01,2026-06-30)，实际SQL截至6月29日含；与问题完全相符。',effect='错误地声称执行含6月30日并否认6月29日截止；原CSV6月30日有有效订单O0000015，不能把错误范围对应为五项0。',repair='依据实际SQL与契约半开区间给明确反馈，保留原结果及首轮失败，另存审校回放输出。')
  doc['cases'][c['id']]=dict(id=c['id'],status=a['status'],structured_passed=all(checks.values()),sql_review_passed=True if a['status']=='ok' else None,explanation_passed=issue is None,full_sql_read=a['status']=='ok',full_answer_read=True,trace_checks=checks,issue=issue,evidence_sha256={str(f.relative_to(ROOT)):sha(f) for f in artifacts},reviewed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
  n+=1
assert n==len(requested),(requested,n)
doc['reviewed_count']=len(doc['cases']);doc['explanation_passed']=sum(c['explanation_passed'] for c in doc['cases'].values());doc['failed_checks']=[dict(id=k,**v['issue']) for k,v in doc['cases'].items() if v['issue']]
p.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:doc[k] for k in ['reviewed_count','explanation_passed','failed_checks']},ensure_ascii=False))
