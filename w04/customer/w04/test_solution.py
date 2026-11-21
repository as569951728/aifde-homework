"""Learner-owned tests: add real inputs, independent expectations and failure cases.

期望值一律从原始 CSV 独立算出来，不从 adapt() 的输出倒推——否则测的是"实现等于实现"。
原始数据在工程根上一层的 数据/qinghe-w04-v1.1/；找不到就跳过，避免换机器直接崩。
"""
import csv
import sys
import unittest
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next((p for p in [ROOT.parent / '数据/qinghe-w04-v1.1',
                         ROOT / 'materials/data/qinghe-w04-v1.1'] if p.is_dir()), None)
TAGS = ['高价值', '价格敏感', '宠物', '生鲜偏好', '母婴-0到3岁', '母婴-3到6岁', '周末家庭', '学生',
        '企业团购', '流失预警', '积分达人', '门店偏好', '夜间购物', '会员日活跃', '小程序偏好', '银发族']
MISSING = {'', 'NULL', '-', '无'}
FILES = {'member': 'crm_member_export.csv', 'order': 'crm_order_export.csv',
         'card': 'crm_card_export.csv', 'shop': 'crm_shop.csv'}


def load(name):
    with (DATA / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


@unittest.skipIf(DATA is None, '原始数据不在预期位置')
class CustomerAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT.parent / '工程/fde-agent-w04/platform'))
        from fde_product.w04.harness import implementation
        from fde_product.w04.io import load_rules, read_inputs
        cls.module = implementation(ROOT / 'customer/w04/solution.py')
        cls.rules = load_rules(ROOT / 'artifacts/w04/cleaning_rules.yaml')
        cls.tables = read_inputs(DATA)
        cls.result = cls.module.adapt(cls.tables, cls.rules,
                                      {'source': str(DATA), 'rules_dir': str(ROOT / 'artifacts/w04'),
                                       'data_version': cls.rules['data_version']})
        cls.members = load('crm_member_export.csv')
        cls.orders = load('crm_order_export.csv')

    # ---------- 一、四类对账等式 ----------
    def test_reconciliation_equation_holds_for_every_type(self):
        for kind, value in self.result['record_counts'].items():
            with self.subTest(kind=kind):
                self.assertEqual(value['read'],
                                 value['accepted'] + value['quarantined'] + value['deduplicated'])
                self.assertEqual(value['read'], len(self.tables[FILES[kind]]['rows']))

    def test_accepted_rows_match_emitted_tables(self):
        pairs = {'member': 'members', 'order': 'orders', 'card': 'cards', 'shop': 'stores'}
        for kind, table in pairs.items():
            with self.subTest(kind=kind):
                self.assertEqual(self.result['record_counts'][kind]['accepted'],
                                 len(self.result['tables'][table]))
                self.assertEqual(self.result['record_counts'][kind]['quarantined'],
                                 sum(1 for q in self.result['tables']['quarantine']
                                     if q['record_type'] == kind))

    # ---------- 二、红线：触达限制一个不能少 ----------
    def test_do_not_contact_set_equals_source_scan(self):
        expected = {row['hy_id'] for row in self.members
                    if '勿打电话' in (row['tag'] or '') or '勿发短信' in (row['tag'] or '')}
        got = {note['member_id'] for note in self.result['tables']['member_notes']
               if note['category'] == '触达限制'}
        self.assertEqual(len(expected), 443, '源数据里"包含"匹配应为 443 人')
        self.assertEqual(expected - got, set(), '漏掉的触达限制会员')
        self.assertEqual(got - expected, set(), '凭空多出的触达限制会员')

    def test_do_not_contact_not_narrowed_to_cell_start(self):
        """按"整格开头"实现会只剩 266 人——这条锁住匹配口径，防止第 7 步被改坏。"""
        cell_start = {row['hy_id'] for row in self.members
                      if (row['tag'] or '').strip().startswith(('勿打电话', '勿发短信'))}
        self.assertEqual(len(cell_start), 266)
        got = {note['member_id'] for note in self.result['tables']['member_notes']
               if note['category'] == '触达限制'}
        self.assertGreater(len(got), len(cell_start), '混写在中间的会员被漏掉了')

    # ---------- 三、标签：16 个、连字符不拆、备注不丢原文 ----------
    def test_only_sixteen_legal_tags_and_hyphen_kept_whole(self):
        tags = Counter(item['tag'] for item in self.result['tables']['member_tags'])
        self.assertEqual(set(tags), set(TAGS))
        self.assertNotIn('母婴', tags, '母婴-0到3岁 被按连字符拆碎了')
        self.assertEqual(tags['母婴-0到3岁'], 5566)
        self.assertEqual(tags['母婴-3到6岁'], 5257)

    def test_tag_pairs_equal_independent_scan(self):
        expected = set()
        for row in self.members:
            if (row['tag'] or '').strip() in MISSING:
                continue
            for tag in TAGS:
                if tag in row['tag']:
                    expected.add((row['hy_id'], tag))
        got = {(item['member_id'], item['tag']) for item in self.result['tables']['member_tags']}
        self.assertEqual(len(expected), 56215)
        self.assertEqual(expected, got)

    def test_notes_keep_raw_cell_and_never_empty(self):
        raw = {row['hy_id']: row['tag'] for row in self.members}
        for note in self.result['tables']['member_notes']:
            with self.subTest(member=note['member_id']):
                self.assertEqual(note['raw_text'], raw[note['member_id']])
                self.assertTrue(note['note_text'].strip())
                self.assertNotIn(note['note_text'], MISSING)
                self.assertIn(note['category'], ('触达限制', '客户关系', '卡务', '联系状态', '其他'))

    def test_confirmed_card_note_keeps_internal_comma(self):
        """小林 MSG-05263 明确说这个逗号属于同一条备注。"""
        expected = '卡务-11月办卡，门店留有登记'
        sources = {i for i, row in enumerate(self.members, 1) if expected in row['tag']}
        self.assertTrue(sources)
        for source_row in sources:
            got = [note for note in self.result['tables']['member_notes']
                   if note['source_row'] == source_row]
            self.assertEqual(len(got), 1)
            self.assertIn(expected, got[0]['note_text'])

    def test_unconfirmed_contact_effect_not_upgraded(self):
        """效力待核的词单独出现不能直接变成禁止触达。"""
        for text in ('仅保留到店服务', '这阵子不方便接听'):
            self.assertNotEqual(self.module._category(text), '触达限制')
        self.assertEqual(self.module._category('勿打电话-这阵子不方便接听'), '触达限制')

    def test_missing_tag_cell_emits_nothing(self):
        """整格是 ''/NULL/-/无 的 77,049 行不能变成备注，否则 category 会被压成"其他"。"""
        blank = {row['hy_id'] for row in self.members if (row['tag'] or '').strip() in MISSING}
        self.assertEqual(len(blank), 77049)
        touched = {note['member_id'] for note in self.result['tables']['member_notes']} & blank
        self.assertEqual(touched, set())

    # ---------- 四、金额与状态映射 ----------
    def test_money_is_yuan_times_hundred_without_float_drift(self):
        paid = {row['ord_no']: row['amt_pay'] for row in self.orders}
        for order in self.result['tables']['orders'][:200]:
            with self.subTest(order=order['order_id']):
                self.assertEqual(order['paid_cents'], int(Decimal(paid[order['order_id']]) * 100))
                self.assertIsInstance(order['paid_cents'], int)

    def test_full_refund_maps_to_paid_not_cancelled(self):
        """指标库 valid_order_count 写"取消和全退不计"→ 全退必须落 paid 才用得上金额条件。"""
        status = {row['ord_no']: row['ord_stat'] for row in self.orders}
        fields = list(self.orders[0])
        members = {row['hy_id'] for row in self.members}
        # 期望值独立复算：源表 13,147 条全额退款／25,841 条已取消，
        # 去掉被去重的重复行与悬挂单后才是入库口径
        seen, expected_full, expected_cancel = set(), 0, 0
        for row in self.orders:
            key = tuple(row[name] for name in fields)
            if key in seen or row['hy_id'] not in members:
                continue
            seen.add(key)
            if row['ord_stat'] == '全额退款':
                expected_full += 1
            elif row['ord_stat'] == '已取消':
                expected_cancel += 1
        self.assertEqual(sum(1 for r in self.orders if r['ord_stat'] == '全额退款'), 13147)
        self.assertEqual(expected_full, 13106)
        self.assertEqual(expected_cancel, 25770)

        got = [o for o in self.result['tables']['orders'] if status[o['order_id']] == '全额退款']
        self.assertEqual(len(got), expected_full)
        self.assertTrue(all(o['status'] == 'paid' for o in got), '全额退款没落到 paid')
        cancelled = [o for o in self.result['tables']['orders'] if o['status'] == 'cancelled']
        self.assertEqual(len(cancelled), expected_cancel)

    # ---------- 五、隔离与去重 ----------
    def test_orphan_orders_quarantined_not_accepted(self):
        members = {row['hy_id'] for row in self.members}
        expected = {row['ord_no'] for row in self.orders if row['hy_id'] not in members}
        self.assertEqual(len(expected), 168)
        accepted = {o['order_id'] for o in self.result['tables']['orders']}
        self.assertEqual(accepted & expected, set(), '悬挂订单混进了 accepted')
        codes = Counter(q['reason_code'] for q in self.result['tables']['quarantine'])
        self.assertEqual(codes['UNLINKED_ACCOUNT'], 168)

    def test_exact_duplicates_counted_once(self):
        fields = list(self.orders[0])
        seen, redundant = set(), []
        for row in self.orders:
            key = tuple(row[name] for name in fields)
            if key in seen:
                redundant.append(key)
            seen.add(key)
        self.assertEqual(len(redundant), 336)
        self.assertEqual(self.result['record_counts']['order']['deduplicated'], 336)
        self.assertEqual(len(self.result['tables']['orders']), 168253 - 336 - 168)

    def test_card_types_collapsed_to_five(self):
        kinds = Counter(card['card_type'] for card in self.result['tables']['cards'])
        self.assertEqual(set(kinds), {'悦享年卡', '家庭季卡', '异业联名卡', '体验卡', '员工内购'})
        self.assertEqual(kinds['悦享年卡'], 8178 + 1201, '悦享卡（年）没并进悦享年卡')
        self.assertEqual(kinds['员工内购'], 299)


class GuardTests(unittest.TestCase):
    """不依赖原始数据的规则防线。"""

    def setUp(self):
        sys.path.insert(0, str(ROOT.parent / '工程/fde-agent-w04/platform'))
        from fde_product.w04.io import load_rules
        self.rules = load_rules(ROOT / 'artifacts/w04/cleaning_rules.yaml')

    def test_delimiters_never_include_slash_or_space(self):
        for value in self.rules['tag_cleaning']['delimiters']:
            self.assertNotIn(value, ('/', ' '), '斜杠或空格被当分隔符会切碎混写行')

    def test_duplicate_rule_records_deduplication_not_quarantine(self):
        rule = {item['rule_id']: item for item in self.rules['abnormal_records']}['exact_duplicate_order']
        self.assertEqual(rule['action'], 'deduplicate')
        # Source wording changes when later evidence arrives; the disposition
        # contract stays fixed. Real-input tests above check actual dedup counts.
        self.assertEqual(rule['reason_code'], 'EXACT_DUPLICATE')

    def test_orphan_rule_quarantines(self):
        rule = {item['rule_id']: item for item in self.rules['abnormal_records']}['orphan_order']
        self.assertEqual(rule['action'], 'quarantine')
        self.assertEqual(rule['reason_code'], 'UNLINKED_ACCOUNT')


if __name__ == '__main__':
    unittest.main()
