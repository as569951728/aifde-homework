#!/usr/bin/env python3
"""Independent raw-CSV oracle. No SQL, generated library, model, or actual query inputs.

Run once to freeze; refuses to overwrite a freeze. All writes remain beside this file.
"""
import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SMALL = ROOT / 'materials/data/small'
METRICS = ['order_count', 'paid_order_count', 'valid_order_count', 'cancelled_order_count',
           'refund_order_count', 'partial_refund_order_count', 'full_refund_order_count']
NAMES = '创建订单数、支付订单数、有效订单数、取消订单数、退款订单数、部分退款订单数、全额退款订单数'
RULES = {
    'order_count': '窗口内每个唯一订单号一次，包含取消单',
    'paid_order_count': 'status=paid，包含全退与零实付paid',
    'valid_order_count': 'status=paid 且 paid_cents-refund_cents>0',
    'cancelled_order_count': 'status=cancelled',
    'refund_order_count': 'status=paid 且 refund_cents>0',
    'partial_refund_order_count': 'status=paid 且 0<refund_cents<paid_cents',
    'full_refund_order_count': 'status=paid 且 paid_cents>0 且 refund_cents=paid_cents',
}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def read_csv(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields=None):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def parse_orders(data):
    rows = read_csv(data / 'orders.csv')
    for row in rows:
        for name in ('gross_cents', 'paid_cents', 'refund_cents', 'quantity'):
            row[name] = int(row[name])
    assert len(rows) == len({r['order_id'] for r in rows})
    assert all(r['status'] in {'paid', 'cancelled'} and 0 <= r['refund_cents'] <= r['paid_cents'] for r in rows)
    assert all(r['quantity'] > 0 for r in rows)
    assert all(r['paid_cents'] == 0 for r in rows if r['status'] == 'cancelled')
    members = {m['member_id'] for m in read_csv(data / 'members.csv')}
    stores = {s['store_id'] for s in read_csv(data / 'stores.csv')}
    assert all(r['member_id'] in members and r['store_id'] in stores for r in rows)
    return rows

def flags(r):
    p, f, paid = r['paid_cents'], r['refund_cents'], r['status'] == 'paid'
    return dict(zip(METRICS, [True, paid, paid and p-f > 0, r['status'] == 'cancelled',
                             paid and f > 0, paid and 0 < f < p, paid and p > 0 and f == p]))

def key_for(r, group):
    if not group:
        return ()
    if group == ['order__status']:
        return (r['status'],)
    if group == ['metric_time__day']:
        return (r['ordered_at'] + ' 00:00:00',)
    if group == ['store']:
        return (r['store_id'],)
    raise ValueError(group)

def count_case(case_id, question, start, end, group, data, dataset_id, ledger):
    orders = parse_orders(data)
    buckets = {} if group else {(): {m:set() for m in METRICS}}
    included = {m:[] for m in METRICS}
    for r in orders:
        inside = start <= r['ordered_at'] < end
        values = flags(r)
        if inside:
            bucket = buckets.setdefault(key_for(r, group), {m:set() for m in METRICS})
            for m in METRICS:
                if values[m]:
                    bucket[m].add(r['order_id'])
                    included[m].append(r['order_id'])
        ledger.append({'case_id':case_id, 'dataset_id':dataset_id, **r,
                       'in_window':int(inside),
                       **{m:int(inside and values[m]) for m in METRICS},
                       'reason': '窗口内；各列按独立条件计入' if inside else '窗口外排除全部指标'})
    result_rows = [list(k)+[len(v[m]) for m in METRICS] for k,v in sorted(buckets.items())]
    source = (f'原始依据 materials/w03/01_订单日报说明.md 七项订单定义、05_数据字典.md 一行一单/日期/状态/整数分；'
              f'docs/w03/contract.md 与 test-guide.md 查询及空窗契约。数据 {dataset_id}；'
              f'orders.csv SHA256={sha(data / "orders.csv")}；Asia/Shanghai ordered_at 半开窗口 [{start},{end})。'
              '每项独立筛唯一order_id，创建含取消、支付只看paid、有效需实付减退款>0、取消只看cancelled、退款需paid且退款>0、'
              '部分退需0<退款<实付、全退需paid且实付>0且退款=实付。单位单(count)。'
              f'按 {group or "整体"} 分组；逐单归属见本目录order-ledger.csv的{case_id}。'
              f'各项入选订单号：{json.dumps(included, ensure_ascii=False)}。')
    if case_id == 'B2-E01':
        source += '覆盖内窗口无订单；不分组七计数为一行全0，不是无覆盖、null或空行。'
    if case_id == 'B2-Z01':
        source += '人工隔离边界fixture，非青禾经营事实；5天各1单，按日逐条验证，不能仅核总和。'
    return {'id':case_id, 'question':question,
            'expected':{'status':'ok', 'intent':{'metrics':METRICS, 'start':start, 'end':end, 'group_by':group, 'filters':[]},
                        'columns':group+METRICS, 'rows':result_rows, 'units':{m:'count' for m in METRICS}, 'data_version':dataset_id},
            'expected_source':source}

def b1_review(cases, orders):
    stores = {r['store_id']:r for r in read_csv(SMALL / 'stores.csv')}
    reports = []
    for c in cases:
        e = c['expected']
        if e['status'] != 'ok':
            wanted = {'NS07-missing-time':'clarify', 'NS08-outside-coverage':'unsupported'}[c['id']]
            reports.append({'id':c['id'], 'passed':e == {'status':wanted}, 'basis':'问句缺日期须澄清；9月超manifest覆盖须unsupported，分别核原问句与契约'})
            continue
        i = e['intent']
        buckets = {} if i['group_by'] else {():[]}
        for r in orders:
            if not (i['start'] <= r['ordered_at'] < i['end']):
                continue
            vals = {'order__channel':r['channel'], 'store__region':stores[r['store_id']]['region']}
            if any((vals[f['field']] != f['value']) if f['op']=='eq' else (vals[f['field']] not in f['value']) for f in i['filters']):
                continue
            buckets.setdefault(key_for(r, i['group_by']), []).append(r)
        result = []
        for k, rs in sorted(buckets.items()):
            paid = [r for r in rs if r['status']=='paid']
            vals = {'payment_cents':sum(r['paid_cents'] for r in paid), 'refund_cents':sum(r['refund_cents'] for r in paid),
                    'net_sales_cents':sum(r['paid_cents']-r['refund_cents'] for r in paid),
                    'gross_cents':sum(r['gross_cents'] for r in paid), 'discount_cents':sum(r['gross_cents']-r['paid_cents'] for r in paid)}
            result.append(list(k)+[vals[m] for m in i['metrics']])
        ok = result == e['rows'] and e['columns'] == i['group_by']+i['metrics'] and e['units']=={m:'cents' for m in i['metrics']}
        reports.append({'id':c['id'], 'passed':ok, 'csv_recalculation':result, 'basis':'原CSV按原问句/意图重算五项金额；没有读取实际结果'})
    assert all(r['passed'] for r in reports)
    return {'passed':True, 'total':len(cases), 'question_and_intent_manual_review':True, 'original_case_objects_unchanged':True, 'cases':reports}

def main():
    assert not (OUT / 'expected-freeze.json').exists(), 'Freeze already exists; do not overwrite.'
    manifest = json.loads((SMALL / 'manifest.json').read_text())
    assert all(sha(SMALL / p)==v for p,v in manifest['sha256'].items())
    orders = parse_orders(SMALL)
    fixture = OUT / 'fixture-data'
    fixture.mkdir(exist_ok=True)
    for name in ('members.csv', 'stores.csv', 'cards.csv'):
        shutil.copyfile(SMALL / name, fixture / name)
    fields = list(read_csv(SMALL / 'orders.csv')[0])
    fixture_rows=[]
    for day, status, gross, paid, refund, suffix in [
        (21,'paid',1000,0,0,'ZERO'), (22,'paid',1000,1000,0,'POS'),
        (23,'paid',1000,1000,400,'PART'), (24,'paid',1000,1000,1000,'FULL'),
        (25,'cancelled',1000,0,0,'CANCEL')]:
        fixture_rows.append(dict(member_id='M00001', store_id='S01', ordered_at=f'2026-08-{day}', status=status,
                                 gross_cents=gross, paid_cents=paid, refund_cents=refund, order_id='B2FIX-'+suffix, quantity=1, channel='门店'))
    write_csv(fixture / 'orders.csv', fixture_rows, fields)
    fixture_id = 'qinghe-w03-b2-isolated-boundaries-20261108'
    fixture_manifest = {**manifest, 'id':fixture_id, 'synthetic':True, 'generator_version':'independent-b2-five-row-fixture-v1',
                        'counts':{**manifest['counts'], 'orders':5}, 'sha256':{n:sha(fixture/n) for n in manifest['sha256']},
                        'purpose':'人工隔离技术边界fixture，非青禾经营事实；原small不修改；只用于B2五类逐日单数边界。'}
    write_json(fixture / 'manifest.json', fixture_manifest)
    ledger=[]
    specs=[('B2-N01',f'请同时列出2026年8月青禾优选的{NAMES}。','2026-08-01','2026-09-01',[]),
           ('B2-R01',f'请同时列出2026年8月10日青禾优选的{NAMES}。','2026-08-10','2026-08-11',[]),
           ('B2-R02',f'请同时列出2026年8月15日青禾优选的{NAMES}。','2026-08-15','2026-08-16',[]),
           ('B2-D01',f'请将2026年8月青禾优选的{NAMES}按订单状态分别列出。','2026-08-01','2026-09-01',['order__status']),
           ('B2-D02',f'请将2026年6月30日至7月1日（含首尾）青禾优选的{NAMES}按订单下单日期逐日列出。','2026-06-30','2026-07-02',['metric_time__day']),
           ('B2-E01',f'请同时列出2026年6月1日至6月29日（含首尾）青禾优选的{NAMES}。','2026-06-01','2026-06-30',[])]
    small_cases=[count_case(*spec,SMALL,manifest['id'],ledger) for spec in specs]
    fixture_cases=[count_case('B2-Z01',f'请将2026年8月21日至8月25日（含首尾）青禾优选的{NAMES}按订单下单日期逐日列出。',
                              '2026-08-21','2026-08-26',['metric_time__day'],fixture,fixture_id,ledger)]
    # Hand-calibrated five single-order truth vectors; independent of aggregation.
    assert [r[1:] for r in fixture_cases[0]['expected']['rows']] == [[1,1,0,0,0,0,0],[1,1,1,0,0,0,0],
                                                                  [1,1,1,0,1,1,0],[1,1,0,0,1,0,1],[1,0,0,1,0,0,0]]
    baseline=json.loads((ROOT/'customer/w03/tests.json').read_text())
    assert len(baseline)==15
    write_json(OUT/'b1-original-expected-review.json', b1_review(baseline,orders))
    write_json(OUT/'tests-new-small.json',small_cases)
    write_json(OUT/'tests-small-all.json',small_cases+baseline)
    write_json(OUT/'tests-fixture.json',fixture_cases)
    write_csv(OUT/'order-ledger.csv',ledger)
    aux=[]
    for c in small_cases+fixture_cases:
        offset=len(c['expected']['intent']['group_by'])
        for row in c['expected']['rows']:
            vals=dict(zip(METRICS,row[offset:]))
            aux.append({'case_id':c['id'],'group':row[:offset],
                        'created_equals_paid_plus_cancelled':vals['order_count']==vals['paid_order_count']+vals['cancelled_order_count'],
                        'refund_equals_partial_plus_full':vals['refund_order_count']==vals['partial_refund_order_count']+vals['full_refund_order_count']})
    assert all(a['created_equals_paid_plus_cancelled'] and a['refund_equals_partial_plus_full'] for a in aux)
    write_json(OUT/'auxiliary-A01.json', {'is_native_query':False,'scope':'仅在已独立核对各分量后检查恒等式；不新增问数题', 'rows':aux})
    inspection={'small_order_count':len(orders),'paid_zero_order_ids':[r['order_id'] for r in orders if r['status']=='paid' and r['paid_cents']==0],
                'status_counts':dict(Counter(r['status'] for r in orders)), 'rules':RULES,
                'fixture_required':True,'small_new_queries':6,'b1_regression_queries':15,'fixture_queries':1,
                'scope':'课程small干净合成数据及另列人工fixture；不证明生产、规模、B3或客户验收',
                'august_repeated_paid_amounts':{str(k):v for k,v in ((p,[r['order_id'] for r in orders if r['ordered_at'].startswith('2026-08') and r['status']=='paid' and r['paid_cents']==p]) for p in sorted({r['paid_cents'] for r in orders})) if len(v)>1}}
    write_json(OUT/'sample-and-scope.json',inspection)
    inputs=['materials/w03/01_订单日报说明.md','materials/w03/02_财务邮件.md','materials/w03/05_数据字典.md','docs/w03/contract.md','docs/w03/test-guide.md',
            'templates/w03/dimension_targets.json','customer/w03/test-plans/metric_cases.json','customer/w03/tests.json']
    inputs += ['materials/data/small/'+n for n in ['orders.csv','members.csv','stores.csv','cards.csv','manifest.json']]
    outputs=[p for p in OUT.rglob('*') if p.is_file()]
    freeze={'frozen_at_utc':datetime.now(timezone.utc).isoformat(), 'phase':'expected_before_build_before_actual_before_skill_and_judge_review',
            'no_generated_library_sql_or_actual_results_read':True, 'input_hashes':{p:sha(ROOT/p) for p in inputs},
            'artifact_hashes':{str(p.relative_to(OUT)):sha(p) for p in outputs},
            'small_new_count':6,'small_with_regression_count':21,'fixture_count':1,
            'business_values_frozen':True,'catalog_and_dataset_hash_pinning':'After load may add only verified version metadata to separate file; no intent/value changes.'}
    write_json(OUT/'expected-freeze.json',freeze)
    print(json.dumps({'frozen':freeze['frozen_at_utc'],'small':[(c['id'],c['expected']['rows']) for c in small_cases],
                      'fixture':fixture_cases[0]['expected']['rows'],'b1_rechecked':15},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
