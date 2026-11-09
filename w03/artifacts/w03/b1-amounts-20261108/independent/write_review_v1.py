from pathlib import Path
import json,hashlib,datetime,importlib.util
O=Path(__file__).resolve().parent;R=O.parents[3];B=O.parent;P=B/'test-v1/metric_test_report.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads(P.read_text());assert r['complete'] and len(r['cases'])==15
spec=importlib.util.spec_from_file_location('judge',R/'customer/w03/judge.py');judge=importlib.util.module_from_spec(spec);spec.loader.exec_module(judge)
notes={
'B1-N01':'8月五项金额及分转元正确；paid范围、退款原订单日及优惠不扣退忠实。',
'B1-R01':'五项金额、全退净额零及SQL正确，但解释把金额统计单位称为CRM会员账户。',
'B1-R02':'部分退款五项金额正确，但解释把金额统计单位称为CRM会员账户。',
'B1-D01':'按成交店S01/S02/S03正确分组，逐列换算正确，未换成归属店。',
'B1-F01':'华东成交地区与小程序AND筛选正确，五项金额正确，未否认实际筛选。',
'B1-Z01':'覆盖内空窗五项均零，含6月1日至29日，未将零称未知。',
'B1-D02':'6个原订单日组及全部30个金额格换算正确，不补无返回日期，不把全退排除。',
'NS01-aug-total':'原8月净额100300分正确，paid扣退订单范围忠实。',
'NS02-july-transaction-store':'三成交店净额正确，但解释把金额统计单位称为CRM会员账户。',
'NS03-aug-mini-program':'小程序净额48700分正确，解释承认实际渠道筛选。',
'NS04-partial-refund-day':'净额7000分及SQL正确，但解释把金额统计单位称为CRM会员账户。',
'NS05-full-refund-day':'净额0分正确，解释为paid汇总零，不改称只计有效购买。',
'NS06-covered-empty':'覆盖内空窗净额0分正确，不误称未定义。',
'NS07-missing-time':'正确请求补充时间，没有猜测月份或返回金额。',
'NS08-outside-coverage':'正确拒绝9月整月，没有把覆盖外答成零。'}
bad={'B1-R01','B1-R02','NS02-july-transaction-store','NS04-partial-refund-day'};cases=[]
for c in r['cases']:
 a=c['actual'];comp=judge.compare(c['expected'],a);tp=B/'test-v1/traces'/a['trace_id'];trace=tp/'answer-trace.json';agree=None
 if trace.exists():
  u=json.loads(json.loads(trace.read_text())['messages'][1]['content']);agree=u['question']==c['question'] and u['result']['rows']==a['rows'] and u['definitions']==[next(x for x in json.loads((B/'build-v1/catalog.json').read_text()) if x['id']==m) for m in a['intent']['metrics']]
 cases.append({'id':c['id'],'trace_id':a['trace_id'],'structured_passed':comp['passed'],'sql_review':'passed' if a['status']=='ok' else 'not_applicable_no_query','answer_trace_matches_actual_and_catalog':agree,'explanation_passed':c['id'] not in bad,'note':notes[c['id']],'finding':None if c['id'] not in bad else {'type':'amount_account_unit_confusion','quote':a['answer'][a['answer'].find('统计单位'):a['answer'].find('统计单位')+30]},'actual_answer_or_reason':a.get('answer',a.get('reason'))})
res={'status':'failed_explanation_review','passed':False,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'report_sha256':sha(P),'structured_passed':15,'sql_success_cases_passed':13,'explanation_or_nonok_reason_passed':11,'total':15,'failed_checks':[{'case_id':c['id'],'finding':c['finding']} for c in cases if not c['explanation_passed']],'cases':cases,'approved_as_final_batch':False,'limitations':['small合成数据范围','金额数值通过不抵消解释单位错误','取消paid/refund0和全退net0仍需结合SQL检查','本轮不验证客户验收、规模、生产或全部12维度行为'],'repair':'Only source-grounded conditional scope.statistics_unit candidate approved for one rebuild and same15 regression. Preserve this result; no rescore or actual-to-expected copy.'}
(O/'final-review-v1.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
lines=['# B1 test-v1 独立逐题审查','','状态：解释未通过；结构化 15/15；13 条成功 SQL 均正确；解释及非成功原因 11/15。四条金额回答误称统计单位为 CRM 会员账户，不能登记本批整体通过。','','| 用例 | 结构/SQL | 解释 | 说明 |','| --- | --- | --- | --- |']
for c in cases:lines.append('| '+c['id']+' | 通过 | '+('通过' if c['explanation_passed'] else '失败')+' | '+c['note']+' |')
lines+=['','四条失败的 answer-trace 均收到 scope.statistics_unit=CRM会员账户。目录和结果units正确；此前生成物审查未拦全局上下文泛化，另见scope-config-review。批准最小配置候选重建及同15题回归，不改期望、不覆盖本轮失败。','']
(O/'final-review-v1.md').write_text('\n'.join(lines))
print(json.dumps({'structured':15,'explanation_passed':11,'failed':sorted(bad),'trace_consistency':all(c['answer_trace_matches_actual_and_catalog'] is not False for c in cases)}))
