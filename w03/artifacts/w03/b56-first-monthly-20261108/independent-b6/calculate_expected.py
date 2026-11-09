#!/usr/bin/env python3
"""B6独立期望：stdlib CSV逐账户/月核算；不导入工程/模型，不执行SQL/Agent。"""
import csv
import hashlib
import json
import shutil
from collections import defaultdict
from datetime import date
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SMALL = ROOT / 'materials/data/small'
METRICS = ['monthly_buyer_count', 'monthly_repeat_buyer_count', 'monthly_repeat_rate']
UNITS = dict(zip(METRICS, ['count', 'count', 'ratio']))
TABLES = ['orders', 'members', 'stores', 'cards']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

def csv_read(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))

def month_list(start, end):
    year, month = map(int, start[:7].split('-'))
    while f'{year:04d}-{month:02d}-01' < end:
        yield f'{year:04d}-{month:02d}'
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)

def check_data(path):
    manifest = json.loads((path / 'manifest.json').read_text())
    tables = {t: csv_read(path / (t + '.csv')) for t in TABLES}
    for t, rows in tables.items():
        assert sha(path / (t + '.csv')) == manifest['sha256'][t + '.csv']
        assert len(rows) == manifest['counts'][t]
        key = {'orders':'order_id', 'members':'member_id', 'stores':'store_id', 'cards':'card_id'}[t]
        assert len({r[key] for r in rows}) == len(rows) and all(r[key] for r in rows)
    members = {r['member_id'] for r in tables['members']}
    registered_at = {r['member_id']: r['registered_at'] for r in tables['members']}
    stores = {r['store_id'] for r in tables['stores']}
    assert all(r['member_id'] in members for t in ['orders', 'cards'] for r in tables[t])
    assert all(r['store_id'] in stores for r in tables['orders'])
    assert all(r['home_store_id'] in stores for r in tables['members'])
    start, end = manifest['coverage']
    for r in tables['orders']:
        assert start <= r['ordered_at'] < end
        assert registered_at[r['member_id']] <= r['ordered_at']
        date.fromisoformat(r['ordered_at'])
        assert r['status'] in ['paid', 'cancelled']
        assert 0 <= int(r['refund_cents']) <= int(r['paid_cents'])
    return manifest, tables

def effective(r):
    return r['status'] == 'paid' and int(r['paid_cents']) - int(r['refund_cents']) > 0

def reason(r):
    if r['status'] != 'paid':
        return 'cancelled非paid，排除'
    if int(r['paid_cents']) - int(r['refund_cents']) <= 0:
        return 'paid实付减累计退款不大于0，排除'
    return 'paid且实付减累计退款大于0，纳入'

def calculate(path, label):
    manifest, tables = check_data(path)
    orders = defaultdict(list)
    card_ids = defaultdict(list)
    for c in tables['cards']:
        card_ids[c['member_id']].append(c['card_id'])
    for line, r in enumerate(tables['orders'], 2):
        orders[(r['ordered_at'][:7], r['member_id'])].append({**r, 'csv_line': line})
    ledger = []
    summary = {}
    for month in month_list(*manifest['coverage']):
        buyers, repeaters = [], []
        for member in tables['members']:
            mid = member['member_id']
            rows = sorted(orders[(month, mid)], key=lambda r:(r['ordered_at'], r['order_id']))
            valid = [r for r in rows if effective(r)]
            if valid:
                buyers.append(mid)
            if len(valid) >= 2:
                repeaters.append(mid)
            ledger.append({'dataset':label, 'month':month, 'member_id':mid,
                'tier_context_only':member['tier'], 'card_ids_context_only':';'.join(card_ids[mid]),
                'all_order_ids':';'.join(r['order_id'] for r in rows),
                'effective_order_ids':';'.join(r['order_id'] for r in valid),
                'excluded_order_ids':';'.join(r['order_id'] for r in rows if not effective(r)),
                'order_decisions':json.dumps([{'id':r['order_id'],'csv_line':r['csv_line'],
                    'date':r['ordered_at'],'status':r['status'],'paid_cents':int(r['paid_cents']),
                    'refund_cents':int(r['refund_cents']),'reason':reason(r)} for r in rows],ensure_ascii=False),
                'effective_count':len(valid),'buyer':int(bool(valid)),'repeat_buyer':int(len(valid)>=2)})
        summary[month] = {'buyer_ids':buyers, 'repeat_buyer_ids':repeaters,
            'monthly_buyer_count':len(buyers), 'monthly_repeat_buyer_count':len(repeaters),
            'monthly_repeat_rate':len(repeaters)/len(buyers) if buyers else None,
            'ratio_derivation':f'{len(repeaters)}/{len(buyers)}' if buyers else '0/0，分母零未定义',
            'all_order_count':sum(len(v) for (m,_),v in orders.items() if m==month)}
    with (OUT / f'ledger-{label}.csv').open('w', newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(ledger[0]));w.writeheader();w.writerows(ledger)
    save(OUT / f'monthly-summary-{label}.json', summary)
    return manifest, tables, summary

def make_fixture():
    fixture = OUT / 'fixture-data'
    fixture.mkdir(exist_ok=True)
    for t in ['members','stores','cards']:
        shutil.copyfile(SMALL / (t+'.csv'), fixture / (t+'.csv'))
    fields = list(csv_read(SMALL / 'orders.csv')[0])
    # 七条人工订单；无真实客户事实。M00001有两张卡但仅一笔有效单。
    entries = [
        ('FXB6-001','M00001','2026-08-01','paid',1000,0,'S01','门店'),
        ('FXB6-002','M00001','2026-08-15','paid',1000,1000,'S02','小程序'),
        ('FXB6-003','M00001','2026-08-31','cancelled',0,0,'S01','门店'),
        ('FXB6-004','M00002','2026-08-01','paid',1000,0,'S01','门店'),
        ('FXB6-005','M00002','2026-08-31','paid',2000,500,'S02','小程序'),
        ('FXB6-006','M00003','2026-08-31','paid',1000,0,'S03','门店'),
        ('FXB6-007','M00004','2026-08-05','cancelled',0,0,'S01','小程序')]
    rows=[]
    for oid,mid,d,status,paid,refund,store,channel in entries:
        rows.append(dict(zip(['order_id','member_id','ordered_at','status','paid_cents','refund_cents','store_id','channel'],
                             [oid,mid,d,status,paid,refund,store,channel]),gross_cents=max(paid,1000),quantity=1))
    with (fixture/'orders.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    original=json.loads((SMALL/'manifest.json').read_text())
    manifest={'id':'qinghe-w03-b6-independent-fixture-20261108-v1','synthetic':True,
        'coverage':original['coverage'],'timezone':original['timezone'],'reference_date':'2026-09-01',
        'generator_version':'independent-b6-hand-authored-seven-orders-v1',
        'counts':{t:len(csv_read(fixture/(t+'.csv'))) for t in TABLES},
        'sha256':{t+'.csv':sha(fixture/(t+'.csv')) for t in TABLES},
        'source_manifest_id':original['id'],
        'purpose':'人工隔离R01，仅orders为7条自拟边界；其他3张表逐字节复制small并保持外键，不是课程规模数据或客户事实'}
    save(fixture/'manifest.json',manifest)
    return fixture

def ok_case(id,question,start,end,months,summary,manifest,source):
    grouped=len(months)>1
    cols=(['metric_time__month'] if grouped else [])+METRICS
    rows=[]
    for m in months:
        s=summary[m]
        rows.append(([m+'-01 00:00:00'] if grouped else [])+[s[k] for k in METRICS])
    return {'id':id,'question':question,'expected':{'status':'ok',
        'intent':{'metrics':METRICS,'start':start,'end':end,'group_by':['metric_time__month'] if grouped else [],'filters':[]},
        'columns':cols,'rows':rows,'units':UNITS,
        'data_version':manifest['id']},'expected_source':source}

def main():
    small_manifest, small_tables, small = calculate(SMALL,'small')
    fixture=make_fixture()
    fixture_manifest, fixture_tables, fx = calculate(fixture,'fixture')
    # 人工校准锚点独立于循环结果；若源数据改变必须调查，而不是照算法改锚点。
    assert [small['2026-07'][k] for k in METRICS]==[11,1,1/11]
    assert [small['2026-08'][k] for k in METRICS]==[15,12,12/15]
    assert [small['2026-05'][k] for k in METRICS]==[0,0,None]
    assert [fx['2026-08'][k] for k in METRICS]==[3,1,1/3]
    assert small['2026-05']['all_order_count']==0
    assert 'M00005' in small['2026-07']['buyer_ids'] and 'M00005' in small['2026-08']['buyer_ids']
    assert 'M00005' not in small['2026-07']['repeat_buyer_ids']+small['2026-08']['repeat_buyer_ids']
    prefix=('依据materials/w03/03_会员运营周报.md（月内3项）与01_订单日报说明.md（有效订单）、05_数据字典.md，'
            '原small manifest与4表sha逐项验证。以paid且paid_cents-refund_cents>0选订单，再按CRM账户和自然月建订单ID集合；'
            '>=1为购买，>=2为复购；复购账户数/购买账户数，零分母null；与卡张数、会员等级、付费资格无关。')
    nsource=prefix+'2026-08购买15账户、复购12账户，12/15=0.8。明细见ledger-small.csv和monthly-summary-small.json；均按原订单日期归月。'
    msource=prefix+'2026-07为11、1、1/11；2026-08为15、12、12/15，月组须为各月月首00:00:00。M00005两月各1有效单，均非月内复购；不得合并人数、跨月凑两单或平均比率。'
    tests=[ok_case('B6-N01','请同时列出2026年8月青禾优选全门店、全渠道的月内购买会员数、月内复购会员数和月内复购率。','2026-08-01','2026-09-01',['2026-08'],small,small_manifest,nsource),
           ok_case('B6-M01','请按自然月分别列出2026年7月和8月青禾优选全门店、全渠道的月内购买会员数、月内复购会员数和月内复购率；保留各月，不给跨月合计或平均率。','2026-07-01','2026-09-01',['2026-07','2026-08'],small,small_manifest,msource),
           ok_case('B6-Z01','2026年5月青禾优选全门店、全渠道的月内购买会员数、月内复购会员数和月内复购率分别是多少？','2026-05-01','2026-06-01',['2026-05'],small,small_manifest,prefix+'manifest覆盖2024-09-01至2026-09-01（不含）；2026年5月全月原orders无行，两个集合均空，结果0、0、null（分母为零，非覆盖外）。')]
    refusals=[
        ('B6-X01','请列出2026年8月1日至8月15日（含15日）青禾优选的月内购买会员数、月内复购会员数和月内复购率。','03_会员运营周报限定完整自然月；所问半开区间[2026-08-01,2026-08-16)不是完整月，contract及engine.py:117-120也明确拒绝。不得偷偷扩到整月。'),
        ('B6-X02','请将2026年8月青禾优选的月内购买会员数、月内复购会员数和月内复购率按订单成交门店分别列出。','03_会员运营周报明确仅整月、全门店口径；contract/engine当前full_month_only拒绝成交门店分组。不能改用会员归属门店或仍返回全店数。'),
        ('B6-X03','2026年8月青禾优选仅小程序渠道的月内购买会员数、月内复购会员数和月内复购率是多少？','业务材料03未明确禁止渠道；当前contract的full_month_only明确全渠道且engine.py:118拒绝filters，因此预期unsupported是当前实现边界，不是客户原文禁止。不得静默去掉渠道筛选。')]
    tests += [{'id':i,'question':q,'expected':{'status':'unsupported'},'expected_source':s} for i,q,s in refusals]
    ftests=[ok_case('B6-R01','请同时列出2026年8月青禾优选全门店、全渠道的月内购买会员数、月内复购会员数和月内复购率。','2026-08-01','2026-09-01',['2026-08'],fx,fixture_manifest,
        prefix+'本题仅在fixture-data人工隔离数据上执行：M00001有效{FXB6-001}，FXB6-002全退及003取消排除；M00002有效{004,005}（005部分退仍有效）；M00003有效{006}；M00004仅007取消。购买{M00001,M00002,M00003}=3，复购{M00002}=1，率1/3；M00001两卡不能将1有效单变2单。其余表原small逐字节复制，人工7订单不充当客户事实或课程small。')]
    save(OUT/'tests-small.json',tests)
    save(OUT/'tests-fixture.json',ftests)
    save(OUT/'calculation-summary.json',{'stage':'independent_expected_only','native_builds':0,'native_agent_queries':0,
        'small_manifest_id':small_manifest['id'],'small_case_count':len(tests),'fixture_case_count':len(ftests),
        'small_months':{k:small[k] for k in ['2026-05','2026-07','2026-08']},'fixture_august':fx['2026-08'],
        'covered_zero_months':[m for m,s in small.items() if s['monthly_buyer_count']==0],
        'sample_gap':'原small缺同账户同月一有效加一全退组合；R01人工7订单补齐。Z01原small可覆盖，无需零月fixture。'})
    print(json.dumps({'small':{m:[small[m][k] for k in METRICS] for m in ['2026-05','2026-07','2026-08']},
        'fixture':[fx['2026-08'][k] for k in METRICS],'files_written':True},ensure_ascii=False))

if __name__=='__main__':
    main()
