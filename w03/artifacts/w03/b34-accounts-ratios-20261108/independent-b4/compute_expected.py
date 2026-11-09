"""Independent B4 oracle: Python CSV arithmetic only, no generated library/SQL/result inputs."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DATA = ROOT / 'materials/data/small'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

definitions = {
    'avg_order_value': ('有效订单均额','net_sales_cents','valid_order_count','cents_per_order'),
    'avg_buyer_value': ('购买会员人均消费','net_sales_cents','buyer_count','cents_per_member'),
    'purchase_frequency': ('购买频次','valid_order_count','buyer_count','orders_per_member'),
    'refund_amount_rate': ('退款金额占比','refund_cents','payment_cents','ratio'),
    'cancel_rate': ('取消率','cancelled_order_count','order_count','ratio'),
    'refund_order_rate': ('退款订单率','refund_order_count','paid_order_count','ratio'),
    'discount_rate': ('优惠率','discount_cents','gross_cents','ratio'),
    'items_per_order': ('单均商品件数','valid_order_items','valid_order_count','items_per_order'),
}
metrics = list(definitions)
names = '、'.join(x[0] for x in definitions.values())
orders = list(csv.DictReader((DATA/'orders.csv').open()))
for o in orders:
    for k in ('gross_cents','paid_cents','refund_cents','quantity'): o[k] = int(o[k])
assert len(orders)==len({o['order_id'] for o in orders})==48

def calculate(oo):
    paid=[o for o in oo if o['status']=='paid']
    valid=[o for o in paid if o['paid_cents']>o['refund_cents']]
    refunded=[o for o in paid if o['refund_cents']>0]
    cancelled=[o for o in oo if o['status']=='cancelled']
    values={
        'net_sales_cents':sum(o['paid_cents']-o['refund_cents'] for o in paid),
        'valid_order_count':len(valid),
        'buyer_count':len({o['member_id'] for o in valid}),
        'refund_cents':sum(o['refund_cents'] for o in paid),
        'payment_cents':sum(o['paid_cents'] for o in paid),
        'cancelled_order_count':len(cancelled),
        'order_count':len(oo),
        'refund_order_count':len(refunded),
        'paid_order_count':len(paid),
        'discount_cents':sum(o['gross_cents']-o['paid_cents'] for o in paid),
        'gross_cents':sum(o['gross_cents'] for o in paid),
        'valid_order_items':sum(o['quantity'] for o in valid),
    }
    sets={n:sorted(o['order_id'] for o in rows) for n,rows in [('all_orders',oo),('paid_orders',paid),('valid_orders',valid),('refund_orders',refunded),('cancelled_orders',cancelled)]}
    sets.update(buyer_accounts=sorted({o['member_id'] for o in valid}), refund_accounts=sorted({o['member_id'] for o in refunded}), valid_stores=sorted({o['store_id'] for o in valid}))
    ratios={}
    for m,(_,n,d,u) in definitions.items():
        f=Fraction(values[n],values[d]) if values[d] else None
        ratios[m]={'numerator_id':n,'denominator_id':d,'numerator':values[n],'denominator':values[d],'exact_fraction':str(f) if f is not None else None,'value':float(f) if f is not None else None,'unit':u}
    return {'components':values,'sets':sets,'ratios':ratios}

scenarios=[
 ('B4-N01','2026-08-01','2026-09-01',[],[],f'请同时列出2026年8月青禾优选的{names}。'),
 ('B4-Z01','2026-06-01','2026-06-30',[],[],f'请同时列出2026年6月1日至29日（含首尾）青禾优选的{names}。'),
 ('B4-R01','2026-08-10','2026-08-11',[],[],f'请同时列出2026年8月10日青禾优选的{names}。'),
 ('B4-D01-store','2026-07-01','2026-08-01',['store'],[],f'请按成交门店列出2026年7月青禾优选的{names}。'),
 ('B4-D01-all','2026-07-01','2026-08-01',[],[],f'请列出2026年7月青禾优选全店整体的{names}。'),
 ('B4-F01','2026-08-01','2026-09-01',[],[{'field':'order__channel','op':'eq','value':'小程序'}],f'请同时列出2026年8月青禾优选小程序渠道的{names}。'),
]
tests=[]; ledgers={}
for cid,start,end,groups,filters,question in scenarios:
    oo=[o for o in orders if start<=o['ordered_at']<end and (not filters or o['channel']=='小程序')]
    selections={s:[o for o in oo if o['store_id']==s] for s in sorted({o['store_id'] for o in oo})} if groups else {'overall':oo}
    ledgers[cid]={key:calculate(selected) for key,selected in selections.items()}
    rows=[([key] if groups else [])+[v['ratios'][m]['value'] for m in metrics] for key,v in ledgers[cid].items()]
    tests.append({'id':cid,'question':question,'expected':{'status':'ok','intent':{'metrics':metrics,'start':start,'end':end,'group_by':groups,'filters':filters},'columns':groups+metrics,'rows':rows,'units':{m:d[3] for m,d in definitions.items()},'data_version':'qinghe-w03-20260923-small'},'expected_source':f'独立从materials/data/small/orders.csv逐行核算，原文件SHA256={sha(DATA/"orders.csv")}。时间[{start},{end})，成交门店来自orders.store_id，小程序条件仅在F01应用于全部组成量。01_订单日报说明.md规定paid金额/有效订单/购买CRM账户/件数；02_财务邮件.md规定八比率分别的分子分母、分母0未定义；05_数据字典.md规定订单粒度、覆盖和字段。每组入选订单、有效/paid/取消/退款订单集合、购买账户、全部整数分子分母和精确分数见ratio-ledger.json的{cid}。先在窗口及筛选内分别聚合分子分母再除，不取逐订单或门店比率的平均；有效订单原始件数不扣推算退货件数。所有有限比率存JSON浮点，零分母为null。'})

# Hand anchors from three physical orders, independently readable in original CSV.
r=ledgers['B4-R01']['overall']
assert r['sets']['all_orders']==['O0000004','O0000005']
assert [r['ratios'][m]['value'] for m in metrics]==[None,None,None,1.0,0.5,1.0,0.0,None]
assert all(v['value'] is None for v in ledgers['B4-Z01']['overall']['ratios'].values())
july=ledgers['B4-D01-store']
overall=ledgers['B4-D01-all']['overall']
mean_controls={}
for m in metrics:
    vv=[g['ratios'][m]['value'] for g in july.values() if g['ratios'][m]['value'] is not None]
    wrong=sum(vv)/len(vv)
    correct=overall['ratios'][m]['value']
    mean_controls[m]={'unweighted_store_mean_wrong_method':wrong,'correct_whole_window':correct,'distinguishes':wrong!=correct}

dump('tests.json',tests)
dump('ratio-ledger.json',ledgers)
dump('raw-order-ledger.json',[dict(o, effective=o['status']=='paid' and o['paid_cents']>o['refund_cents']) for o in orders])
dump('aggregation-counterexamples.json',mean_controls)
dump('review-contract.json',{
 'metrics':definitions,'query_count':6,'answer_review':'B4-U01 applies to all six actual answers; no extra query',
 'comparison':{'float_rel_tol':1e-9,'float_abs_tol':1e-7,'null':'only equal to JSON null; not 0, string or unsupported','float':'all eight ratios are JSON floats when defined, including 0.0 and 1.0; values never multiplied by 100 in rows','integer_components':'exact; source amounts in integer cents'},
 'display_units':{'cents_per_order':'分/单; 若展示元/单除以100','cents_per_member':'分/CRM账户; 若展示元/账户除以100','orders_per_member':'单/CRM账户，不是自然人','ratio':'无量纲原始比率；文字展示百分数才乘100','items_per_order':'件/单，有效订单的原始件数，不是净商品销量'},
 'coverage_limits':['July per-store discount rates are all zero; that metric alone cannot distinguish averaging store rates','July buyer sets are disjoint across stores; D01 alone cannot detect summing cross-store distinct accounts; B3 separately covers account aggregation','Small data contains no paid zero-amount order; prior B2 isolated fixture is separate evidence, not part of these six expected results'],
 'source_boundary':'Only original CSVs, original business material, targets, case design and interface/test contract read before freezing. No generated library, SQL, actual result or B3 agent oracle used.',
})
inputs=[ROOT/'materials/w03'/f for f in ('01_订单日报说明.md','02_财务邮件.md','05_数据字典.md')]+[DATA/f for f in ('orders.csv','members.csv','stores.csv','cards.csv','manifest.json')]+[ROOT/f for f in ('docs/w03/contract.md','docs/w03/test-guide.md','customer/w03/targets.json','customer/w03/dimension_targets.json','customer/w03/test-plans/metric_cases.json')]
dump('frozen.json',{'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'stage':'before build and before actual results; oracle frozen','inputs_sha256':{str(p.relative_to(ROOT)):sha(p) for p in inputs},'outputs_sha256':{p.name:sha(p) for p in OUT.glob('*') if p.is_file() and p.name!='frozen.json'},'api_calls':0,'sql_calls':0,'model_calls':0})
print(json.dumps({'query_count':len(tests),'normal':tests[0]['expected']['rows'],'full_refund_day':tests[2]['expected']['rows'],'mean_controls':mean_controls},ensure_ascii=False))
