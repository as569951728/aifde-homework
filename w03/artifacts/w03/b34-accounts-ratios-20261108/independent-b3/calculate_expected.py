"""Independent raw-CSV ledger. No tested library, database, SQL or actual result input."""
import csv,json,hashlib,datetime
from pathlib import Path
from collections import defaultdict,Counter
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
DATA=ROOT/'materials/data/small'
B2=ROOT/'artifacts/w03/b2-order-counts-20261108/independent'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,v): (OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def load(data):
    rows=list(csv.DictReader((data/'orders.csv').open()))
    for r in rows:
        for k in ['gross_cents','paid_cents','refund_cents','quantity']:r[k]=int(r[k])
    return rows,{r['store_id']:r for r in csv.DictReader((data/'stores.csv').open())},{r['member_id']:r for r in csv.DictReader((data/'members.csv').open())}
orders,stores,members=load(DATA)
cards=list(csv.DictReader((DATA/'cards.csv').open()))
cardids=defaultdict(list)
for c in cards:cardids[c['member_id']].append(c['card_id'])
manifest=json.loads((DATA/'manifest.json').read_text())
assert all(sha(DATA/k)==v for k,v in manifest['sha256'].items())
B3=['buyer_count','refund_buyer_count','selling_store_count','valid_order_items']
B1=['payment_cents','refund_cents','net_sales_cents','gross_cents','discount_cents']
B2IDS=['order_count','paid_order_count','valid_order_count','cancelled_order_count','refund_order_count','partial_refund_order_count','full_refund_order_count']
def eligible(r):return r['status']=='paid' and r['paid_cents']>r['refund_cents']
def refund(r):return r['status']=='paid' and r['refund_cents']>0
def values(rs):
    p=[r for r in rs if r['status']=='paid'];v=[r for r in rs if eligible(r)];f=[r for r in rs if refund(r)]
    return dict(payment_cents=sum(r['paid_cents'] for r in p),refund_cents=sum(r['refund_cents'] for r in p),net_sales_cents=sum(r['paid_cents']-r['refund_cents'] for r in p),gross_cents=sum(r['gross_cents'] for r in p),discount_cents=sum(r['gross_cents']-r['paid_cents'] for r in p),order_count=len({r['order_id'] for r in rs}),paid_order_count=len({r['order_id'] for r in p}),valid_order_count=len({r['order_id'] for r in v}),cancelled_order_count=len({r['order_id'] for r in rs if r['status']=='cancelled'}),refund_order_count=len({r['order_id'] for r in f}),partial_refund_order_count=len({r['order_id'] for r in p if 0<r['refund_cents']<r['paid_cents']}),full_refund_order_count=len({r['order_id'] for r in p if r['paid_cents']>0 and r['refund_cents']==r['paid_cents']}),buyer_count=len({r['member_id'] for r in v}),refund_buyer_count=len({r['member_id'] for r in f}),selling_store_count=len({r['store_id'] for r in v}),valid_order_items=sum(r['quantity'] for r in v))
def dimension(r,k,ss,mm):
    if k=='store':return r['store_id']
    if k=='member':return r['member_id']
    if k=='home_store':return mm[r['member_id']]['home_store_id']
    if k=='metric_time__day':return r['ordered_at']+' 00:00:00'
    if k=='metric_time__month':return r['ordered_at'][:7]+'-01 00:00:00'
    pre,field=k.split('__')
    if pre=='order':return r[field]
    if pre=='store':return ss[r['store_id']][field]
    if pre=='member':return mm[r['member_id']][field]
    if pre=='home_store':return ss[mm[r['member_id']]['home_store_id']][field]
    raise ValueError(k)
ledger=[];account_ledger=[];store_ledger=[]
def calc(cid,intent,data=DATA,keep=True):
    rr,ss,mm=load(data);selected=[]
    for r in rr:
        window=intent['start']<=r['ordered_at']<intent['end']
        filters=all((dimension(r,f['field'],ss,mm)==f['value'] if f['op']=='eq' else dimension(r,f['field'],ss,mm) in f['value']) for f in intent['filters'])
        take=window and filters
        if take:selected.append(r)
        if keep:ledger.append(dict(case_id=cid,**r,home_store_id=mm[r['member_id']]['home_store_id'],in_window=window,passes_filters=filters,in_scope=take,valid_order=eligible(r),refund_order=refund(r),buyer_key=r['member_id'] if take and eligible(r) else '',refund_buyer_key=r['member_id'] if take and refund(r) else '',selling_store_key=r['store_id'] if take and eligible(r) else '',quantity_contribution=r['quantity'] if take and eligible(r) else 0,card_ids='|'.join(cardids[r['member_id']]) if data==DATA else ''))
    groups=defaultdict(list)
    if not intent['group_by']:groups[()]=selected
    else:
        for r in selected:groups[tuple(dimension(r,k,ss,mm) for k in intent['group_by'])].append(r)
    if keep:
        for member in sorted({r['member_id'] for r in selected}):
            rs=[r for r in selected if r['member_id']==member]
            account_ledger.append(dict(case_id=cid,member_id=member,orders='|'.join(r['order_id'] for r in rs),valid_orders='|'.join(r['order_id'] for r in rs if eligible(r)),refund_orders='|'.join(r['order_id'] for r in rs if refund(r)),valid_stores='|'.join(sorted({r['store_id'] for r in rs if eligible(r)})),**values(rs)))
        for store in sorted({r['store_id'] for r in selected}):
            rs=[r for r in selected if r['store_id']==store]
            store_ledger.append(dict(case_id=cid,store_id=store,valid_members='|'.join(sorted({r['member_id'] for r in rs if eligible(r)})),refund_members='|'.join(sorted({r['member_id'] for r in rs if refund(r)})),orders='|'.join(r['order_id'] for r in rs),**values(rs)))
    return [list(key)+[values(rs)[m] for m in intent['metrics']] for key,rs in sorted(groups.items())],selected
names='购买会员数、退款会员数、成交门店数和有效订单商品件数'
specs=[('B3-N01','请同时列出2026年8月青禾优选的'+names+'。','2026-08-01','2026-09-01',[],[]),('B3-D01','请将2026年7月青禾优选的'+names+'按订单成交门店编号分别列出。','2026-07-01','2026-08-01',['store'],[]),('B3-R01','请同时列出2026年8月15日青禾优选的'+names+'。','2026-08-15','2026-08-16',[],[]),('B3-R02','请同时列出2026年8月10日青禾优选的'+names+'。','2026-08-10','2026-08-11',[],[]),('B3-U01','请同时列出2026年7月1日至8月31日（含首尾）青禾优选的'+names+'。','2026-07-01','2026-09-01',[],[]),('B3-F01','请同时列出2026年8月青禾优选小程序渠道的'+names+'。','2026-08-01','2026-09-01',[],[dict(field='order__channel',op='eq',value='小程序')])]
new=[]
for cid,q,start,end,group,filters in specs:
    intent=dict(metrics=B3,start=start,end=end,group_by=group,filters=filters)
    rows,selected=calc(cid,intent)
    source=f'依据materials/w03/01_订单日报说明.md购买会员数、退款会员数、成交门店数、有效订单商品件数；02_财务邮件.md有效订单及归属日期；05_数据字典.md一行一单、CRM账户、订单成交门店、quantity原始件数；docs/w03/contract.md与test-guide.md。原small CSV {manifest["id"]}，orders SHA256={sha(DATA/"orders.csv")}。Asia/Shanghai ordered_at半开窗口[{start},{end})，先筛窗口及{json.dumps(filters,ensure_ascii=False)}；有效单paid且paid_cents>refund_cents，购买账户按member_id去重，成交店按orders.store_id去重；退款账户另筛paid且refund_cents>0再按member_id去重；件数逐有效单累加原quantity，不由退款金额推净销量；卡表不参与筛选或连接。单位count，前三项业务量纲账户/账户/门店，末项业务量纲件，均整数。逐单、逐账户、逐成交门店归属见本目录order-ledger.csv/account-ledger.csv/store-ledger.csv中{cid}。'
    new.append(dict(id=cid,question=q,expected=dict(status='ok',intent=intent,columns=group+B3,rows=rows,units={m:'count' for m in B3},data_version=manifest['id']),expected_source=source))
# Preserve original objects byte-for-byte in standalone snapshot; only compare recalculations.
oldpath=ROOT/'customer/w03/tests.json';old=json.loads(oldpath.read_text());assert len(old)==21
(OUT/'tests-regression-original21.json').write_bytes(oldpath.read_bytes())
reg=[]
for t in old:
    e=t['expected']
    if e['status']=='ok':
        rows,rs=calc(t['id'],e['intent']);units={m:('cents' if m in B1 else 'count') for m in e['intent']['metrics']}
        check=dict(id=t['id'],rows_recomputed=rows,expected_rows=e['rows'],passed=(rows==e['rows'] and units==e['units'] and e['data_version']==manifest['id'] and e['columns']==e['intent']['group_by']+e['intent']['metrics']),independent_order_ids=[r['order_id'] for r in rs])
    else:check=dict(id=t['id'],passed=((t['id']=='NS07-missing-time' and e['status']=='clarify') or (t['id']=='NS08-outside-coverage' and e['status']=='unsupported')),basis='Question lacks dates, or requested September outside [2024-09-01,2026-09-01); inspected independently against source and contract.')
    reg.append(check)
assert all(c['passed'] for c in reg)
fixture=json.loads((B2/'tests-fixture.json').read_text());fixture_checks=[]
for t in fixture:
    rows,rs=calc(t['id'],t['expected']['intent'],B2/'fixture-data')
    fixture_checks.append(dict(id=t['id'],passed=rows==t['expected']['rows'],rows_recomputed=rows))
assert all(x['passed'] for x in fixture_checks)
(OUT/'tests-fixture-b2-unchanged.json').write_bytes((B2/'tests-fixture.json').read_bytes())
for name,data in [('tests-new-small.json',new),('tests-small-all.json',new+old),('original21-expected-review.json',reg)]:dump(name,data)
for name,rows in [('order-ledger.csv',ledger),('account-ledger.csv',account_ledger),('store-ledger.csv',store_ledger)]:
    with (OUT/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
july=[r for r in orders if '2026-07-01'<=r['ordered_at']<'2026-08-01'];both=[r for r in orders if '2026-07-01'<=r['ordered_at']<'2026-09-01'];aug=[r for r in both if r['ordered_at']>='2026-08-01']
aux={}
for label,rs in [('july',july),('july_august',both),('august',aug)]:
    per={s:values([r for r in rs if r['store_id']==s]) for s in sorted({r['store_id'] for r in rs})}
    aux[label]=dict(overall={m:values(rs)[m] for m in B3},by_store={s:{m:v[m] for m in B3} for s,v in per.items()},sum_group_buyers=sum(v['buyer_count'] for v in per.values()),nonadditive_buyers=values(rs)['buyer_count']!=sum(v['buyer_count'] for v in per.values()))
# Explicit counterexamples and limitation: no original account has both multiple cards and repeated refund orders.
wrong=dict(jul_aug_count_valid_orders_as_buyers=values(both)['valid_order_count'],jul_aug_count_refund_orders_as_refund_buyers=values(both)['refund_order_count'],aug_sum_quantity_after_card_left_join=sum(r['quantity']*max(1,len(cardids[r['member_id']])) for r in aug if eligible(r)),aug_sum_quantity_distinct=sum({r['quantity'] for r in aug if eligible(r)}),aug_all_paid_quantity=sum(r['quantity'] for r in aug if r['status']=='paid'),jul_aug_count_distinct_paid_amount_as_buyers=len({r['paid_cents'] for r in both if eligible(r)}))
dump('auxiliary-nonadditivity.json',aux)
dump('sample-and-scope.json',dict(b3_questions=6,original21_unchanged=True,new_fixture_required=False,old_fixture_reused=True,units={m:'count' for m in B3},business_dimensions=['CRM账户','CRM账户','成交门店','原始购买件'],counterexamples=wrong,limitations=['U01各边界由不同账户独立覆盖；没有同一账户同时多卡和多退款的交叉样本。','July按店购买账户无重叠，D01单独不能以数值证明非可加；July-August辅助去重总数与门店数之和不同。','原样本没有自然人身份表，不能验证跨系统自然人去重，指标仅CRM账户。','本批不是规模、客户验收或提交证据。']))
dump('fixture-b2-reuse.json',dict(source=str(B2.relative_to(ROOT)),tests_sha256=sha(B2/'tests-fixture.json'),data_sha256={p.name:sha(p) for p in sorted((B2/'fixture-data').glob('*')) if p.is_file()},checks=fixture_checks))
freeze_files=['tests-new-small.json','tests-small-all.json','tests-regression-original21.json','tests-fixture-b2-unchanged.json','order-ledger.csv','account-ledger.csv','store-ledger.csv','calculate_expected.py','original21-expected-review.json','fixture-b2-reuse.json','auxiliary-nonadditivity.json','sample-and-scope.json']
dump('expected-freeze.json',dict(frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),state='frozen_before_reading_tested_library_sql_or_actual',method='raw CSV only, no LLM/database calls',files={f:sha(OUT/f) for f in freeze_files},sources={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'materials/w03/01_订单日报说明.md',ROOT/'materials/w03/02_财务邮件.md',ROOT/'materials/w03/05_数据字典.md',ROOT/'docs/w03/contract.md',ROOT/'docs/w03/test-guide.md',*sorted(DATA.glob('*'))] if p.is_file()},original21_sha256=sha(oldpath)))
print(json.dumps(dict(new={t['id']:t['expected']['rows'] for t in new},regression_passed=sum(x['passed'] for x in reg),fixture_checks=fixture_checks,aux=aux,wrong=wrong),ensure_ascii=False,indent=2))
