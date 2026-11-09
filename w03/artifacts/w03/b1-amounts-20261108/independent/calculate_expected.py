"""Independent CSV oracle; no library, generated SQL, actual results or model calls."""
from pathlib import Path
import csv,json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
M=['payment_cents','refund_cents','net_sales_cents','gross_cents','discount_cents']
DATA=ROOT/'materials/data/small'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x): (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def read_csv(name):return list(csv.DictReader((DATA/name).open(newline='')))
orders=read_csv('orders.csv'); stores={s['store_id']:s for s in read_csv('stores.csv')}
manifest=json.loads((DATA/'manifest.json').read_text())
for name,h in manifest['sha256'].items(): assert sha(DATA/name)==h,name
for row in orders:
 for col in ['gross_cents','paid_cents','refund_cents','quantity']:row[col]=int(row[col])
assert len({r['order_id'] for r in orders})==len(orders)==48
assert all(r['store_id'] in stores for r in orders)
# This sequence is intentionally separate from the system under test.
def contribution(r):
 if r['status']!='paid':return [0,0,0,0,0]
 return [r['paid_cents'],r['refund_cents'],r['paid_cents']-r['refund_cents'],r['gross_cents'],r['gross_cents']-r['paid_cents']]
names='实付金额、退款金额、净销售额、支付订单原价金额、优惠金额'
specs=[
 ('B1-N01',f'请同时列出2026年8月青禾优选的{names}。','2026-08-01','2026-09-01',[],[]),
 ('B1-R01',f'请同时列出2026年8月10日青禾优选的{names}。','2026-08-10','2026-08-11',[],[]),
 ('B1-R02',f'请同时列出2026年8月15日青禾优选的{names}。','2026-08-15','2026-08-16',[],[]),
 ('B1-D01',f'请将2026年7月青禾优选的{names}按订单成交门店编号分别列出。','2026-07-01','2026-08-01',['store'],[]),
 ('B1-F01',f'请同时列出2026年8月青禾优选小程序渠道且订单成交地区为华东的{names}。','2026-08-01','2026-09-01',[],[{'field':'order__channel','op':'eq','value':'小程序'},{'field':'store__region','op':'eq','value':'华东'}]),
 ('B1-Z01',f'请同时列出2026年6月1日至6月29日（含首尾）青禾优选的{names}。','2026-06-01','2026-06-30',[],[]),
 ('B1-D02',f'请将2026年8月青禾优选的{names}按订单下单日期逐日列出。','2026-08-01','2026-09-01',['metric_time__day'],[]),
]
ledger=[];tests=[]; summaries=[];assertions=[]
for ident,question,start,end,group,filters in specs:
 groups={} if group else {():[0]*5}
 ids=[];excluded=[]
 for r in orders:
  in_window=start<=r['ordered_at']<end
  in_filters=not filters or (r['channel']=='小程序' and stores[r['store_id']]['region']=='华东')
  eligible=in_window and in_filters and r['status']=='paid'
  reason='included_paid' if eligible else ('outside_window' if not in_window else 'filter_excluded' if not in_filters else 'cancelled_excluded')
  vals=contribution(r) if eligible else [0]*5
  key=() if not group else (r['store_id'],) if group==['store'] else (r['ordered_at']+' 00:00:00',)
  # Observe business order dates; do not fabricate calendar-only groups.
  if in_window and in_filters:
   groups.setdefault(key,[0]*5)
   if eligible:ids.append(r['order_id'])
   else:excluded.append(r['order_id'])
   for i,v in enumerate(vals):groups[key][i]+=v
  ledger.append({'case_id':ident,**r,'transaction_region':stores[r['store_id']]['region'],'in_window':in_window,'passes_filters':in_filters,'included_paid':eligible,'reason':reason,**{'contribution_'+m:v for m,v in zip(M,vals)}})
 rows=[list(k)+v for k,v in sorted(groups.items())]
 expected={'status':'ok','intent':{'metrics':M,'start':start,'end':end,'group_by':group,'filters':filters},'columns':group+M,'rows':rows,'units':{m:'cents' for m in M},'data_version':manifest['id']}
 explanation=f"依据 materials/w03/01_订单日报说明.md、02_财务邮件.md、05_数据字典.md；数据 {manifest['id']}。原始 CSV 逐单筛 ordered_at 半开窗口 [{start}, {end})，仅 paid；原价=原始 gross，实付=原始 paid，退款=原始 refund，净额=每单 paid-refund，优惠=每单 gross-paid，不扣 refund。成交地区经 orders.store_id→stores.store_id。纳入 {','.join(ids) or '无'}；窗口与筛选内取消排除 {','.join(excluded) or '无'}；详见 order-ledger.csv。"
 tests.append({'id':ident,'question':question,'expected':expected,'expected_source':explanation})
 summaries.append({'id':ident,'question':question,'included_order_ids':ids,'cancelled_order_ids_in_scope':excluded,'columns':group+M,'rows':rows})
 for row in rows:
  p,r,n,g,d=row[len(group):]
  assertions.append({'id':'B1-A01','case_id':ident,'group':row[:len(group)],'payment_minus_refund_equals_net':p-r==n,'gross_minus_payment_equals_discount':g-p==d})
assert all(a['payment_minus_refund_equals_net'] and a['gross_minus_payment_equals_discount'] for a in assertions)
# Hand-calibrated single-record and mixed-status anchors before freeze.
assert tests[1]['expected']['rows']==[[5000,5000,0,5000,0]]
assert tests[2]['expected']['rows']==[[9000,2000,7000,10000,1000]]
assert tests[5]['expected']['rows']==[[0,0,0,0,0]]
dump('tests-new.json',tests);dump('summary.json',summaries);dump('cross-metric-assertions.json',assertions)
with (OUT/'order-ledger.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=ledger[0].keys());w.writeheader();w.writerows(ledger)
lines=['# B1 独立期望冻结','',f'数据：{manifest["id"]}；7 条新增真实问句，每条五项金额，全部单位为分。','', '顺序：实付／退款／净销售额／支付订单原价／优惠。','']
for s in summaries:lines += [f'## {s["id"]}',s['question'],'',f'结果：`{json.dumps(s["rows"],ensure_ascii=False)}`','']
lines += ['## 范围与盲点','- 只用原始 CSV 与来源规则核算；未读本轮生成物、SQL 或 actual。','- 按原订单日期归属，累计退款不是现金退款发生日流量；优惠不随退款冲减。','- 金额 paid 行集合含全退；它不是有效购买订单集合，也不是会员账户数。','- 取消单 paid/refund 为零，实付/退款/净额结果不能独立发现遗漏状态过滤；取消原价非零，gross/discount 有区分力。','- 全退净额为零，净额数值不能区分 paid 与 effective 误过滤；实付/退款/原价能区分。8 月 31 日 O0000040 全退仍贡献 100 分优惠。','- B1-D02 只列原始数据有订单的日期，不生成无订单日；日键以引擎 str(datetime) 协议为 YYYY-MM-DD 00:00:00。','- 退款原始表没有现金发生日字段，不能把此样本说成真实现金跨月退款测试。','- B1-A01 是结果恒等式辅助检查，不是第 8 条新问数，也不替代逐单期望。','- 本次只证明 small 范围；规模和完整 38 项另核。','']
(OUT/'summary.md').write_text('\n'.join(lines))
sources=['materials/w03/01_订单日报说明.md','materials/w03/02_财务邮件.md','materials/w03/05_数据字典.md','materials/data/small/manifest.json','materials/data/small/orders.csv','materials/data/small/stores.csv','materials/data/small/members.csv','materials/data/small/cards.csv','docs/w03/contract.md','docs/w03/test-guide.md','customer/w03/test-plans/metric_cases.json','platform/fde_product/metrics/engine.py']
outputs=['calculate_expected.py','tests-new.json','order-ledger.csv','summary.json','summary.md','cross-metric-assertions.json']
freeze={'status':'independently_frozen_before_build_and_actual','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'case_count':7,'query_case_ids':[t['id'] for t in tests],'auxiliary_assertion':'B1-A01','raw_manifest_hashes_verified':True,'source_sha256':{p:sha(ROOT/p) for p in sources},'expected_artifact_sha256':{p:sha(OUT/p) for p in outputs},'independence':{'generated_library_read':False,'actual_results_read':False,'tested_sql_used':False,'model_api_calls':0,'query_calls':0},'protocol_only_read':'engine.py date serialization line; expected day keys are midnight strings; no generated SQL read'}
dump('expected-freeze.json',freeze)
print(json.dumps({'count':len(tests),'summary':summaries,'freeze':str(OUT/'expected-freeze.json')},ensure_ascii=False,indent=2))
