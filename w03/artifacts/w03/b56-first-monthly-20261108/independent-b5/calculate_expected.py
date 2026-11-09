#!/usr/bin/env python3
"""Independent B5 oracle: original business text + raw CSV only; no SQL/metric imports.

Run from any working directory with Python 3. Writes only beside this script.
The synthetic fixture augments small without changing any original row.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import shutil

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SMALL = ROOT / 'materials/data/small'
FIXTURE = OUT / 'fixture-data'
METRICS = ['new_member_count', 'first_buyer_count', 'first_order_sales_cents',
           'first_order_count', 'repeat_order_count']
FIRST = METRICS[1:]
SIX = METRICS + ['valid_order_count']
UNITS = {m: ('cents' if m == 'first_order_sales_cents' else 'count') for m in SIX}
SOURCE_FILES = [
    'materials/w03/01_订单日报说明.md', 'materials/w03/03_会员运营周报.md',
    'materials/w03/05_数据字典.md', 'docs/w03/business_model.md',
    'docs/w03/contract.md', 'docs/w03/test-guide.md',
    'templates/w03/dimension_targets.json',
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def read_csv(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields=None):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def make_fixture():
    FIXTURE.mkdir(exist_ok=True)
    # Irrelevant stores/cards are byte-identical to small; retain all FKs.
    for table in ('stores', 'cards'):
        shutil.copyfile(SMALL / (table + '.csv'), FIXTURE / (table + '.csv'))
    members = read_csv(SMALL / 'members.csv')
    members += [
        dict(member_id='B5F-M01', registered_at='2026-06-01', home_store_id='S03', tier='普通'),
        dict(member_id='B5F-M02', registered_at='2026-06-15', home_store_id='S02', tier='银卡'),
        dict(member_id='B5F-M03', registered_at='2026-06-16', home_store_id='S01', tier='金卡'),
    ]
    orders = read_csv(SMALL / 'orders.csv')
    def order(oid, date, status, gross, paid, refund):
        return dict(member_id='B5F-M02', store_id='S01', ordered_at=date, status=status,
                    gross_cents=str(gross), paid_cents=str(paid), refund_cents=str(refund),
                    order_id=oid, quantity='1', channel='门店')
    orders += [
        order('B5F-O001', '2026-06-16', 'cancelled', 500, 0, 0),
        order('B5F-O002', '2026-06-17', 'paid', 600, 600, 600),
        # Physical order intentionally opposes order_id on the tied date.
        order('B5F-O004', '2026-06-18', 'paid', 900, 869, 0),
        order('B5F-O003', '2026-06-18', 'paid', 300, 200, 63),
        order('B5F-O005', '2026-06-19', 'paid', 400, 333, 0),
    ]
    write_csv(FIXTURE / 'members.csv', members)
    write_csv(FIXTURE / 'orders.csv', orders)
    original_manifest = json.loads((SMALL / 'manifest.json').read_text())
    manifest = {
        'id': 'qinghe-w03-b5-independent-artificial-20261108-v1',
        'synthetic': True, 'artificial_fixture': True,
        'description': '人工最小增量：原small逐行保留，新增3账户5订单；仅用于B5测试，非客户事实或规模数据。',
        'base_manifest_id': original_manifest['id'],
        'coverage': original_manifest['coverage'], 'timezone': 'Asia/Shanghai',
        'reference_date': original_manifest['reference_date'],
        'generator_version': 'independent-b5-csv-fixture-v1',
        'counts': {t: len(read_csv(FIXTURE / (t + '.csv'))) for t in ('members', 'orders', 'cards', 'stores')},
        'sha256': {t + '.csv': digest(FIXTURE / (t + '.csv')) for t in ('members', 'orders', 'cards', 'stores')},
    }
    write_json(FIXTURE / 'manifest.json', manifest)
    (FIXTURE / 'README.md').write_text(
        '# B5 人工隔离样本\n\n原 small 的全部行保留；stores.csv 和 cards.csv 逐字复制。'
        '新增 B5F-M01（6/1注册、从未下单）、B5F-M02（6/15注册、归属S02而成交S01）、'
        'B5F-M03（6/16注册、从未下单）。\n\n'
        'B5F-M02：6/16取消；6/17全退；6/18物理先出现O004净869分，后出现较小ID O003净137分；'
        '6/19 O005净333分。正确观测期首单是B5F-O003。'
        '6/18问题排除6/19；6/1—15注册问题排除6/16。\n\n'
        '无正式数据写入，无Agent执行，无客户事实或验收含义。仅补这一条取消→全退→同日有效单序列，'
        '没有宣称所有无效顺序组合、同日跨店跨渠道组合或生产历史均已覆盖。\n', encoding='utf-8')

def load_dataset(folder):
    raw = {t: read_csv(folder / (t + '.csv')) for t in ('members', 'orders', 'cards', 'stores')}
    manifest = json.loads((folder / 'manifest.json').read_text())
    for name, sha in manifest['sha256'].items():
        assert digest(folder / name) == sha, ('manifest mismatch', name)
    for table, pk in [('members', 'member_id'), ('orders', 'order_id'), ('cards', 'card_id'), ('stores', 'store_id')]:
        keys = [r[pk] for r in raw[table]]
        assert all(keys) and len(keys) == len(set(keys)), (table, 'PK')
        assert manifest['counts'][table] == len(keys)
    members = {r['member_id']: r for r in raw['members']}
    stores = {r['store_id'] for r in raw['stores']}
    assert all(r['home_store_id'] in stores for r in raw['members'])
    assert all(r['member_id'] in members for r in raw['cards'])
    orders = []
    for position, raw_order in enumerate(raw['orders']):
        r = dict(raw_order)
        assert r['member_id'] in members and r['store_id'] in stores
        assert manifest['coverage'][0] <= r['ordered_at'] < manifest['coverage'][1]
        assert members[r['member_id']]['registered_at'] <= r['ordered_at']
        for field in ('gross_cents', 'paid_cents', 'refund_cents', 'quantity'):
            r[field] = int(r[field])
        assert 0 <= r['refund_cents'] <= r['paid_cents'] <= r['gross_cents']
        assert r['quantity'] > 0 and r['status'] in ('paid', 'cancelled')
        assert r['status'] != 'cancelled' or r['paid_cents'] == 0
        r['net_cents'] = r['paid_cents'] - r['refund_cents']
        r['valid'] = r['status'] == 'paid' and r['net_cents'] > 0
        r['physical_position'] = position + 1
        orders.append(r)
    # Establish first identities from the ENTIRE coverage, prior to any query window.
    by_member = defaultdict(list)
    for r in orders:
        if r['valid']:
            by_member[r['member_id']].append(r)
    first_ids = set()
    for values in by_member.values():
        values.sort(key=lambda r: (r['ordered_at'], r['order_id']))
        first_ids.add(values[0]['order_id'])
        for rank, r in enumerate(values, 1):
            r['valid_rank'] = rank
    cards = Counter(r['member_id'] for r in raw['cards'])
    for r in orders:
        r['valid_rank'] = r.get('valid_rank')
        r['is_observation_first'] = r['order_id'] in first_ids
        r['exclusion_reason'] = '' if r['valid'] else ('cancelled' if r['status'] == 'cancelled' else 'net_not_positive')
        r['card_count_not_used_as_weight'] = cards[r['member_id']]
    return dict(folder=folder, raw=raw, manifest=manifest, members=members, orders=orders,
                first_ids=first_ids, by_member=by_member, cards=cards)

def value_for(metric, registered, orders):
    valid = [r for r in orders if r['valid']]
    first = [r for r in valid if r['is_observation_first']]
    return {
        'new_member_count': len({r['member_id'] for r in registered}),
        'first_buyer_count': len({r['member_id'] for r in first}),
        'first_order_sales_cents': sum(r['net_cents'] for r in first),
        'first_order_count': len(first),
        'repeat_order_count': sum(not r['is_observation_first'] for r in valid),
        'valid_order_count': len(valid),
    }[metric]

def evaluate(ds, case):
    start, end = case['start'], case['end']
    member_filter = set(case.get('member_filter', []))
    accepted = lambda mid: not member_filter or mid in member_filter
    registered = [r for r in ds['raw']['members'] if start <= r['registered_at'] < end and accepted(r['member_id'])]
    orders = [r for r in ds['orders'] if start <= r['ordered_at'] < end and accepted(r['member_id'])]
    groups = case.get('group_by', [])
    metrics = case['metrics']
    if groups == ['home_store', 'member__tier']:
        buckets = defaultdict(list)
        for r in registered:
            buckets[(r['home_store_id'], r['tier'])].append(r)
        rows = [list(k) + [value_for(m, v, []) for m in metrics] for k, v in sorted(buckets.items())]
    elif groups == ['member']:
        # These selected accounts both have valid window activity; no invented zero-only groups.
        keys = sorted({r['member_id'] for r in orders if r['valid']})
        rows = [[mid] + [value_for(m, [r for r in registered if r['member_id'] == mid],
                                      [r for r in orders if r['member_id'] == mid]) for m in metrics] for mid in keys]
    else:
        assert groups == []
        rows = [[value_for(m, registered, orders) for m in metrics]]
    filters = [{'field': 'member', 'op': 'in', 'value': sorted(member_filter)}] if member_filter else []
    expected = dict(status='ok', intent=dict(metrics=metrics, start=start, end=end, group_by=groups, filters=filters),
                    columns=groups + metrics, rows=rows, units={m: UNITS[m] for m in metrics})
    selected_first = [r for r in orders if r['is_observation_first']]
    selected_repeat = [r for r in orders if r['valid'] and not r['is_observation_first']]
    detail = dict(case_id=case['id'], dataset_id=ds['manifest']['id'], interval=[start, end],
                  registered_ids=[r['member_id'] for r in registered],
                  first_orders=[dict(order_id=r['order_id'], member_id=r['member_id'], net_cents=r['net_cents']) for r in selected_first],
                  subsequent_ids=[r['order_id'] for r in selected_repeat],
                  excluded_orders=[dict(order_id=r['order_id'], reason=r['exclusion_reason']) for r in orders if not r['valid']],
                  expected=expected)
    first_note = ', '.join(f"{r['order_id']}={r['net_cents']}分" for r in selected_first) or '无'
    source = (f"独立CSV核算；规则：materials/w03/03_会员运营周报.md注册与观测期四节、"
              f"01_订单日报说明.md有效订单、05_数据字典.md字段关系；数据{ds['manifest']['id']}；"
              f"Asia/Shanghai [{start},{end})。注册按registered_at；有效为paid且paid_cents-refund_cents>0；"
              f"先全覆盖按账户/ordered_at/order_id排序，后筛窗口。窗口注册账户{len(registered)}个；"
              f"首单明细{first_note}；后续有效单{len(selected_repeat)}笔。"
              f"完整账户/订单/注册与过滤明细见本目录ledger-{case['dataset']}-cases.json#{case['id']}，"
              f"源文件hash见expected-freeze.json。卡不参与计数；金额整数分，不推终身首购。")
    return dict(id=case['id'], question=case['question'], expected=expected, expected_source=source), detail

CASES = [
    dict(id='B5-N01', dataset='small', designs=['B5-N01','B5-H01','B5-A01','B5-H03'],
         start='2026-08-01', end='2026-09-01', metrics=SIX,
         question='请同时列出2026年8月青禾优选的注册会员数、观测期首购会员数、观测期首单净销售额（单位分）、观测期首单数、观测期后续购买订单数和有效订单数。'),
    dict(id='B5-D01', dataset='small', designs=['B5-D01'],
         start='2026-07-01', end='2026-08-01', metrics=['new_member_count'], group_by=['home_store','member__tier'],
         question='2026年7月青禾优选的注册会员数按会员归属门店、会员等级列出。'),
    dict(id='B5-Z01', dataset='small', designs=['B5-Z01'],
         start='2026-06-01', end='2026-06-30', metrics=METRICS,
         question='2026年6月1日至29日（包含1日和29日），青禾优选的注册会员数、观测期首购会员数、观测期首单净销售额（单位分）、观测期首单数和观测期后续购买订单数分别是多少？'),
    dict(id='B5-H03', dataset='small', designs=['B5-H03','B5-H01','B5-A01'],
         start='2026-08-01', end='2026-09-01', metrics=FIRST + ['valid_order_count'],
         group_by=['member'], member_filter=['M00005','M00007'],
         question='只看CRM账户M00005和M00007，按会员账户分别列出2026年8月的观测期首购会员数、观测期首单净销售额（单位分）、观测期首单数、观测期后续购买订单数和有效订单数。'),
    dict(id='B5-H02-F', dataset='fixture', designs=['B5-H02','B5-A01'],
         start='2026-06-18', end='2026-06-19', metrics=FIRST + ['valid_order_count'],
         question='2026年6月18日当天，青禾优选的观测期首购会员数、观测期首单净销售额（单位分）、观测期首单数、观测期后续购买订单数和有效订单数分别是多少？'),
    dict(id='B5-Z01-F', dataset='fixture', designs=['B5-Z01','B5-D01'],
         start='2026-06-01', end='2026-06-16', metrics=METRICS,
         question='2026年6月1日至15日（包含1日和15日），青禾优选的注册会员数、观测期首购会员数、观测期首单净销售额（单位分）、观测期首单数和观测期后续购买订单数分别是多少？'),
]

def save_ledgers(ds, name, details):
    write_csv(OUT / f'ledger-{name}-orders.csv', ds['orders'])
    account_rows, registration_rows = [], []
    for mid, m in ds['members'].items():
        valid = ds['by_member'].get(mid, [])
        aug = [r for r in valid if '2026-08-01' <= r['ordered_at'] < '2026-09-01']
        first = valid[0] if valid else None
        account_rows.append(dict(member_id=mid, first_order_id=first['order_id'] if first else '',
            first_date=first['ordered_at'] if first else '', first_net_cents=first['net_cents'] if first else '',
            valid_order_count=len(valid), valid_order_ids='|'.join(r['order_id'] for r in valid),
            august_valid_order_count=len(aug), august_repeat_order_count=sum(not r['is_observation_first'] for r in aug),
            august_monthly_repeat_member=int(len(aug) >= 2),
            card_count_not_used_as_weight=ds['cards'][mid]))
        registration_rows.append(dict(**m, has_any_order=any(r['member_id']==mid for r in ds['orders']),
            has_any_valid_order=bool(valid), card_count_not_used_as_weight=ds['cards'][mid],
            selected_in_cases='|'.join(d['case_id'] for d in details if mid in d['registered_ids'])))
    write_csv(OUT / f'ledger-{name}-accounts.csv', account_rows)
    write_csv(OUT / f'ledger-{name}-registrations.csv', registration_rows)
    write_json(OUT / f'ledger-{name}-cases.json', details)

def save_design(datasets, tests, details):
    all_tests = {t['id']: t for group in tests.values() for t in group}
    plan = json.loads((ROOT / 'customer/w03/test-plans/metric_cases.json').read_text())
    entries = plan if isinstance(plan, list) else next(v for v in plan.values() if isinstance(v, list) and v and isinstance(v[0], dict) and 'batch' in v[0])
    originals = [x for x in entries if x.get('batch') == 'B5']
    assert {x['id'] for x in originals} == {'B5-N01','B5-D01','B5-H01','B5-H02','B5-H03','B5-Z01','B5-A01'}
    write_json(OUT / 'original-designs.json', originals)
    small, fixture = datasets['small'], datasets['fixture']
    aug = [r for r in small['orders'] if r['valid'] and '2026-08-01' <= r['ordered_at'] < '2026-09-01']
    window_first = {}
    for r in sorted(aug, key=lambda x:(x['ordered_at'],x['order_id'])):
        window_first.setdefault(r['member_id'], r)
    window_first_net = sum(r['net_cents'] for r in window_first.values())
    wrong_card_count = sum(max(1,small['cards'][r['member_id']]) for r in aug)
    aug_counts = Counter(r['member_id'] for r in aug)
    monthly_repeat = sum(n >= 2 for n in aug_counts.values())
    evidence = [dict(rule=p, sha256=digest(ROOT / p)) for p in SOURCE_FILES]
    definitions = {
        'B5-N01': dict(faults=['共用错误日期字段','漏指标或错单位','卡一对多膨胀','先窗口后排首次','后续订单数误作月内复购人数'],
            discrimination=f'原small8月新注册0；首购5、首单净额12800分、首单5、后续22、有效27。错误窗口首单为{len(window_first)}人、{window_first_net}分；卡数左连接放大有效单为{wrong_card_count}；月内复购账户{monthly_repeat}个不等于22笔后续单。',
            gaps=['8月注册全部为0，单题不能区分无购买注册漏计；由D01与Z01-F补','同日排序由H02-F补']),
        'B5-D01': dict(faults=['按ordered_at统计注册','把注册账户限于有效购买账户','按成交店代替归属店','按卡或订单行计注册'],
            discrimination='改用7月：M00009—M00020共12账户，S01普通4/金卡2，S02普通4/金卡2；M00017全覆盖无有效购买仍在S01普通中。M00010/12/14/20归属S02但7月成交S01，可区分店角色；没有卡的M00015也应计。',
            gaps=['原8月分组无注册记录，缺区分力，已保存原设计并将执行候选适配至7月','本期字典只给当前等级；不验证历史等级还原','未单独测注册按门店或等级筛选所有组合']),
        'B5-H01': dict(faults=['在8月重新排序','首单排在无效记录后导致首购漏计'],
            discrimination=f'N01共用问数：全覆盖首购5，错误窗口首购{len(window_first)}；H03的M00005于7月31日已首购，8月仅计1笔后续。',
            gaps=['同义问句稳定性未额外测试；H01原问句不单独提交以免重复调用']),
        'B5-H02': dict(faults=['取消单作为首单','全退paid作为首单','同日按文件顺序或降序order_id','同日并列产生重复首单','首单金额未扣退','金额按元而非分','结束日包含6月19日'],
            discrimination='人工B5F-M02先取消后全退，6/18两有效单物理O004在先但O003较小；O003净200-63=137分，O004净869分。正确首单1/金额137/后续1/有效2；文件顺序首额869；未扣退200；两首单金额1006；把6/19算入会后续2/有效3。',
            gaps=['只补取消→全退→同日两有效单这一序列，未声称穷举无效组合','未覆盖同日跨店跨渠道首单筛选语义','原small无同账户同日有效并列，不以原small证明排序规则']),
        'B5-H03': dict(faults=['窗口首购冒充观测期首购','跨月后续订单误作月内复购人数','取消后的有效购买不算首购','解释写成终身首购'],
            discrimination='H03按账户两行：M00005的O0000006在7/31首购、8/20 O0000007是后续；M00007 7/1仅取消、8/31 O0000011净3000是观测期首购。两账户8月各仅1有效单，月内复购各0，但M00005后续单1。',
            gaps=['终身首购属于解释审查项，数值judge不能单独证明文本忠实','只测这两个账户的in筛选，非任意账户/维度组合']),
        'B5-Z01': dict(faults=['订单为空时把members结果也置0','注册按下单日','结束日不半开或遗漏开始日','零值变null或漏列'],
            discrimination='small原6/1—29五项均0，单独不能抓跨事实错误。补人工6/1—15：M01于6/1、M02于6/15注册，窗口完全无订单，期望[2,0,0,0,0]；6/16注册M03不得进入。',
            gaps=['原零例仅保留空窗口零值及字段完整性控制，不虚称可区分日期来源','未验证所有覆盖端点或任意零窗口组合']),
        'B5-A01': dict(faults=['首购账户数与首单数不同','首单加后续不等有效单','各项集合错误但总数偶然相等'],
            discrimination='N01/H03/H02-F均在同一道真实候选中显式索取valid_order_count；每行核首购账户数=首单数、首单数+后续数=有效单。首单身份及不同净额另逐单保留，不只验等式。',
            gaps=['辅助恒等式不是独立业务正确性的充分条件','新增指标范围仍为B5五项；valid_order_count为已有目标的辅助列']),
    }
    designs=[]
    for original in originals:
        did=original['id']; cfg=definitions[did]
        mapped=[c for c in CASES if did in c['designs']]
        designs.append(dict(id=did, original_question_or_fixture=original['question_or_fixture'],
            candidate_ids=[c['id'] for c in mapped],
            questions_and_expected=[dict(case_id=c['id'], dataset=c['dataset'], question=all_tests[c['id']]['question'],
                expected=all_tests[c['id']]['expected'], expected_source=all_tests[c['id']]['expected_source']) for c in mapped],
            fault_to_detect=cfg['faults'], evidence=original['source_refs'], data_discrimination=cfg['discrimination'],
            gaps=cfg['gaps'], expected_status='independently_computed_pending_external_review',
            execution_status='not_run', test_status='not_tested'))
    design=dict(scope='B5 five metrics plus valid_order_count auxiliary; design only',
        author_role='independent expected/design author, not third-party final reviewer',
        sources=evidence, design_count=7, unique_query_candidates=6,
        small_query_count=4, artificial_fixture_query_count=2,
        metric_ids=METRICS, auxiliary_metric_ids=['valid_order_count'], designs=designs,
        run_plan=dict(status='not_executed', steps=[
            '先取得独立审阅Agent对本目录冻结版本的结论；当前自检不是第三方终审。',
            '后续经授权执行阶段：累计目标需含B5五项与valid_order_count；本轮不构建。',
            '各自加载原small与fixture；核dimensions可达、数据与catalog身份后另存带真实运行hash的测试副本；不改本轮冻结期望。',
            'small四题、fixture两题各真实问数一次；N01共用H01/A01，H03与H02-F再核辅助等式；不是7个设计ID各调用一次。',
            '确定性judge逐项核状态、完整意图、列/单位、整数值及分组集合；解释另审观测期、CRM账户、原订单日期、分币及非月内复购。',
            '保留真实执行与回归证据后才登记通过；本轮没有实际通过或规模结果。'],
            dimensions_pending_actual_load=['home_store','member__tier','member'],
            version_binding=dict(source_data_manifest_ids=[d['manifest']['id'] for d in datasets.values()],
                runtime_data_sha256_status='pending_load_not_fabricated',catalog_sha256_status='pending_build_and_load_not_fabricated')))
    write_json(OUT / 'design.json', design)
    # Concrete wrong hypotheses, from raw data only, to document signal strength.
    contrasts=[
        dict(case_id='B5-N01', incorrect_rule='rank_after_window', correct=[5,12800], wrong=[len(window_first),window_first_net]),
        dict(case_id='B5-N01', incorrect_rule='count_later_orders_as_monthly_repeat_accounts', correct=22, wrong=monthly_repeat),
        dict(case_id='B5-N01', incorrect_rule='left_join_cards_without_order_dedup', correct=27, wrong=wrong_card_count),
        dict(case_id='B5-H02-F', incorrect_rule='physical_order_tie', correct=137, wrong=869),
        dict(case_id='B5-H02-F', incorrect_rule='omit_first_refund', correct=137, wrong=200),
        dict(case_id='B5-H02-F', incorrect_rule='rank_all_orders_or_all_paid_before_valid_filter', correct=[1,137,1,1,2], wrong=[0,0,0,2,2]),
        dict(case_id='B5-H02-F', incorrect_rule='include_exclusive_end_date', correct=[1,137,1,1,2], wrong=[1,137,1,2,3]),
        dict(case_id='B5-Z01-F', incorrect_rule='share_empty_order_fact_for_registration', correct=2, wrong=0),
        dict(case_id='B5-Z01-F', incorrect_rule='include_registration_on_exclusive_end', correct=2, wrong=3),
        dict(case_id='B5-Z01-F', incorrect_rule='exclude_registration_on_start', correct=2, wrong=1),
    ]
    assert all(c['correct'] != c['wrong'] for c in contrasts)
    write_json(OUT / 'discrimination-checks.json', dict(kind='raw-data-derived incorrect hypotheses; not real Agent failures', checks=contrasts))
    checks=[
        ('scope', 'Only independent-b5 written; no build/query/formal test or W02 changes by this script.'),
        ('input_integrity', 'Both manifests verified against all CSV hashes; PK/FK/status/amount/date checks passed.'),
        ('coverage', 'B5 five targets and seven original designs mapped to six unique questions.'),
        ('independence', 'stdlib CSV only; no generated SQL, library, actual result, or LLM query used as answer.'),
        ('manual_calibration', 'Named August first IDs and fixture 200-63=137 checked against literal controls.'),
        ('schema', 'All six tests have exactly id/question/expected/expected_source; integer values; expected full intent/columns/rows/units.'),
        ('group_contract', 'D01 retains four groups; H03 two explicit member groups; missing/extra/duplicate groups must fail downstream judge.'),
        ('A01', 'valid_order_count is explicitly asked in N01/H03/H02-F, all expected rows satisfy both identities.'),
        ('honesty', 'No runtime data/catalog hash invented; no real execution or business acceptance claimed.'),
        ('discrimination', 'Ten specified wrong hypotheses differ from correct results; untested combinations documented.'),
    ]
    review=dict(status='author_self_check_passed_pending_independent_review', reviewer='same design/expected author',
        third_party_review=False, actual_agent_query_count=0, build_count=0,
        checks=[dict(id=i,status='pass',note=n) for i,n in checks],
        unresolved_business_decisions=[],
        remaining_execution_gates=['independent review','authorized build/load','actual dimensions and version binding','real Agent run','answer review'])
    write_json(OUT / 'preflight-review.json', review)
    (OUT / 'preflight-review.md').write_text('# B5 作者自检（不是第三方终审）\n\n'
        '状态：作者自检通过，等待独立审阅。无真实问数、无构建、无实际通过。\n\n' +
        '\n'.join(f'- {i}：{n}' for i,n in checks) + '\n\n'
        '来源已有材料足以确定本轮业务期望，无需新增业务裁决。运行维度可达性、运行数据hash及库hash待正式加载后绑定。'
        '同义问句稳定性、所有维度组合、历史等级还原、终身首购、规模性能均未验证。\n', encoding='utf-8')
    (OUT / 'summary.md').write_text('# B5 设计与独立期望\n\n'
        '只完成设计：7个设计ID映射6道候选（small 4、人工fixture 2）；未构建、未真实查数、未标实际通过。\n\n'
        '|候选|独立期望|\n|---|---|\n'
        '|B5-N01（兼H01/A01）|8月注册0；首购5；首单净额12800分；首单5；后续22；有效单27|\n'
        '|B5-D01|改7月，归属S01普通4/金卡2，S02普通4/金卡2；共12账户|\n'
        '|B5-Z01|原6/1—29五项全0，仅作空窗口控制|\n'
        '|B5-H03|M00005：[0,0,0,1,1]；M00007：[1,3000,1,0,1]（首购/首额/首单/后续/有效）|\n'
        '|B5-H02-F|人工6/18：[1,137,1,1,2]；首单B5F-O003，不是文件中先出现的O004|\n'
        '|B5-Z01-F|人工6/1—15：[2,0,0,0,0]；有注册且没有订单|\n\n'
        'fixture只新增3账户5订单，保留small全部原行；stores/cards逐字复制，PK/FK和金额约束已自检。'
        '同日不同净额、取消及全退在先、日期边界有可辨差异；未声称穷举组合。\n\n'
        '运行入口候选见tests-small.json与tests-fixture.json；逐单/账户/注册台账、design.json、错误假设差异、'
        '原设计副本、作者自检和源/产物hash已保存。catalog/data运行hash留加载后绑定。\n\n'
        '下一步：由另一个独立审阅Agent核本目录冻结版本，再决定进入后续构建与真实测试。\n', encoding='utf-8')
    data_sources={}
    for name, ds in datasets.items():
        data_sources[name] = dict(id=ds['manifest']['id'],kind='course_synthetic' if name=='small' else 'artificial_minimal_additions',
            files={str(p.relative_to(ROOT)):digest(p) for p in sorted(ds['folder'].iterdir()) if p.suffix in ('.json','.csv')})
    artifacts={str(p.relative_to(OUT)):digest(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='expected-freeze.json'}
    write_json(OUT / 'expected-freeze.json', dict(phase='design_freeze_before_execution',
        source_files={p:digest(ROOT/p) for p in SOURCE_FILES}, data_sources=data_sources, artifacts=artifacts,
        original_design_source='customer/w03/test-plans/metric_cases.json (B5 entries copied into original-designs.json)',
        generated_sql_or_actual_used=False,
        runtime_binding=dict(status='pending_actual_load', catalog_sha256=None, data_sha256=None,
            note='These nulls are freeze metadata placeholders, not unknown business expected values. Never submit fabricated runtime hashes.'),
        actual_test_status='not_run', independent_review_status='pending_external_reviewer'))

def main():
    original_hashes = {str(p.relative_to(ROOT)): digest(p) for p in SMALL.iterdir() if p.is_file()}
    make_fixture()
    datasets = {'small': load_dataset(SMALL), 'fixture': load_dataset(FIXTURE)}
    tests, details = {}, {}
    for name, ds in datasets.items():
        pairs = [evaluate(ds, c) for c in CASES if c['dataset'] == name]
        tests[name], details[name] = [p[0] for p in pairs], [p[1] for p in pairs]
        write_json(OUT / f'tests-{name}.json', tests[name])
        save_ledgers(ds, name, details[name])
    all_tests = {t['id']: t for group in tests.values() for t in group}
    # Manual controls derive from named source records; these are author checks, not a third-party audit.
    assert all_tests['B5-D01']['expected']['rows'] == [['S01','普通',4],['S01','金卡',2],['S02','普通',4],['S02','金卡',2]]
    assert all_tests['B5-Z01']['expected']['rows'] == [[0,0,0,0,0]]
    assert all_tests['B5-H03']['expected']['rows'] == [['M00005',0,0,0,1,1],['M00007',1,3000,1,0,1]]
    assert all_tests['B5-H02-F']['expected']['rows'] == [[1,137,1,1,2]]
    assert all_tests['B5-Z01-F']['expected']['rows'] == [[2,0,0,0,0]]
    # Enumerated August first identities: M7 O11, M9 O19, M15 O36, M16 O38, M18 O41.
    aug_first = {'O0000011':3000, 'O0000019':1900, 'O0000036':2500, 'O0000038':2600, 'O0000041':2800}
    actual_first = {x['order_id']:x['net_cents'] for x in details['small'][0]['first_orders']}
    assert actual_first == aug_first
    assert all_tests['B5-N01']['expected']['rows'] == [[0,5,12800,5,22,27]]
    for group in tests.values():
        for t in group:
            assert set(t) == {'id','question','expected','expected_source'}
            e=t['expected']; assert len(e['columns']) == len(set(e['columns']))
            assert all(len(row)==len(e['columns']) for row in e['rows'])
            assert all(type(v) is int for row in e['rows'] for v in row[len(e['intent']['group_by']):])
            if 'valid_order_count' in e['columns']:
                for row in e['rows']:
                    cells=dict(zip(e['columns'],row))
                    assert cells['first_buyer_count']==cells['first_order_count']
                    assert cells['first_order_count']+cells['repeat_order_count']==cells['valid_order_count']
    assert original_hashes == {str(p.relative_to(ROOT)):digest(p) for p in SMALL.iterdir() if p.is_file()}
    write_json(OUT / 'manual-controls.json', dict(status='author_self_check_passed',
        august_first_order_net_cents=aug_first, august_expected=all_tests['B5-N01']['expected']['rows'],
        fixture_first=dict(order_id='B5F-O003', paid_cents=200, refund_cents=63, net_cents=137),
        original_small_unchanged=True, cross_metric_identities='Checked on N01, H03, H02-F; no new Agent query performed.'))
    save_design(datasets, tests, details)
    print(json.dumps({name:[{'id':t['id'],'rows':t['expected']['rows']} for t in group] for name,group in tests.items()},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
