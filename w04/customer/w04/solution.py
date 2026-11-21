"""Qinghe CRM (qinghe-w04-v1.1) profiling. Workbooks are never profiled or assumed."""
import csv
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

CONTRACT_VERSION = 'w04-0.1.0'
MISSING = {'', 'NULL', '-', '无'}
ROLES = {'crm_member_export.csv': 'member', 'crm_order_export.csv': 'order',
         'crm_card_export.csv': 'card', 'crm_shop.csv': 'shop'}
DATE_RE = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
DATETIME_RE = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$')
INT_RE = re.compile(r'^-?[0-9]+$')
DEC_RE = re.compile(r'^-?[0-9]+\.[0-9]+$')
TAG_SEPARATORS = (',', ';', '，', '；')


def norm_code(value):
    """Full-width -> half-width, strip, upper. Used for reference checks only."""
    return unicodedata.normalize('NFKC', value).strip().upper()


def decimal_or_none(value):
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def infer_type(present):
    if not present:
        return 'string'
    if all(DATETIME_RE.match(v) for v in present):
        return 'datetime'
    if all(DATE_RE.match(v) for v in present):
        return 'date'
    if all(INT_RE.match(v) for v in present):
        return 'integer'
    if all(DEC_RE.match(v) for v in present):
        return 'decimal'
    return 'string'


def field_stat(filename, field, values):
    present = [v for v in values if v not in MISSING]
    kind = infer_type(present)
    stat = {'source_file': filename, 'field': field, 'inferred_type': kind,
            'total_count': len(values),
            'missing_count': len(values) - len(present)}
    distinct = sorted(set(present))
    if distinct and len(distinct) <= 30:
        counts = Counter(present)
        stat['distribution'] = [{'value': v, 'count': counts[v]} for v in distinct]
    elif kind in ('integer', 'decimal'):
        numbers = [Decimal(v) for v in present]
        stat['range'] = {'min': str(min(numbers)) if numbers else None,
                         'max': str(max(numbers)) if numbers else None}
    else:
        stat['range'] = {'min': distinct[0] if distinct else None,
                         'max': distinct[-1] if distinct else None}
    return stat


def anomaly(pattern, source_file, rows):
    if not rows:
        return None
    return {'pattern': pattern,
            'evidence': {'source_file': source_file, 'sample_rows': rows[:20]}}


def difference(source_file, field, claim, actual, impact):
    return {'source_file': source_file, 'field': field,
            'dictionary_claim': claim, 'actual': actual, 'impact': impact}


def parse_dict_list(dictionary, field,sep='、'):
    """Extract the enumeration a dictionary table row claims, e.g. card kinds."""
    match = re.search(r'\|\s*`' + field + r'`.*\|([^|\n]+)\|', dictionary)
    if not match:
        return []
    return [v.strip() for v in match.group(1).split(sep) if v.strip()]


def profile(tables, dictionary, context):
    """Return profile_report: field statistics, anomalies and dictionary comparison."""
    by_role = {ROLES[name]: tables[name] for name in ROLES if name in tables}
    fields, anomalies, differences = [], [], []

    # ---- 逐字段统计（fields[]）----
    for name, table in sorted(tables.items()):
        if name not in ROLES:
            continue  # 工作账只对照不剖析；存在与否都不影响
        for field in table['fields']:
            values = [r['raw'][field] for r in table['rows']]
            fields.append(field_stat(name, field, values))

    member = by_role.get('member', {}).get('rows', [])
    order = by_role.get('order', {}).get('rows', [])
    card = by_role.get('card', {}).get('rows', [])
    shop = by_role.get('shop', {}).get('rows', [])
    member_ids = {r['raw']['hy_id'] for r in member}
    shop_codes = {norm_code(r['raw']['shop_cd']) for r in shop}

    # ---- 异常（anomalies[]），全部现算，证据=来源文件＋记录序号 ----
    for name in ROLES.values():
        rows = by_role.get(name, {}).get('rows', [])
        seen, dup_rows = set(), []
        for r in rows:
            key = tuple(r['raw'].items())
            if key in seen:
                dup_rows.append(r['source_row'])
            seen.add(key)
        item = anomaly(f'整行完全重复：{len(dup_rows)} 条记录与前面行完全相同',
                       dict((v, k) for k, v in ROLES.items())[name], dup_rows)
        if item:
            anomalies.append(item)

    # 主键重复（同号不同内容）——与整行重复分开报
    ord_groups = {}
    for r in order:
        ord_groups.setdefault(r['raw']['ord_no'], []).append(r)
    conflict_rows = [r['source_row'] for g in ord_groups.values() if len(g) > 1
                     and len({tuple(x['raw'].items()) for x in g}) > 1 for r in g]
    item = anomaly(f'订单号重复且内容不同：{len(conflict_rows)} 条', 'crm_order_export.csv', conflict_rows)
    if item:
        anomalies.append(item)

    # 订单→会员 悬挂引用（孤儿订单／关联不上）
    dangling = [r['source_row'] for r in order if r['raw']['hy_id'] not in member_ids]
    item = anomaly(f'孤儿订单（订单关联的会员在会员表中不存在）：{len(dangling)} 条',
                   'crm_order_export.csv', dangling)
    if item:
        anomalies.append(item)

    # 会员卡→会员 悬挂引用
    dangling_card = [r['source_row'] for r in card if r['raw']['hy_id'] not in member_ids]
    item = anomaly(f'会员卡引用会员表中不存在的会员：{len(dangling_card)} 条',
                   'crm_card_export.csv', dangling_card)
    if item:
        anomalies.append(item)

    # 退款大于实付
    rfd_rows = []
    for r in order:
        pay, rfd = decimal_or_none(r['raw']['amt_pay']), decimal_or_none(r['raw']['amt_rfd'])
        if pay is not None and rfd is not None and rfd > pay:
            rfd_rows.append(r['source_row'])
    item = anomaly(f'退款金额大于实付金额：{len(rfd_rows)} 条', 'crm_order_export.csv', rfd_rows)
    if item:
        anomalies.append(item)

    # 注册日期非 ISO 写法（ASCII 口径，防全角数字）
    join_rows = [r['source_row'] for r in member
                 if r['raw']['join_dt'] not in MISSING
                 and not re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', r['raw']['join_dt'])]
    item = anomaly(f'注册日期非 YYYY-MM-DD 写法（YYYY/M/D 与 YYYYMMDD 并存）：{len(join_rows)} 条',
                   'crm_member_export.csv', join_rows)
    if item:
        anomalies.append(item)

    # 门店码：首尾空白（含全角空格）
    for filename, rows, column in (('crm_member_export.csv', member, 'reg_shop'),
                                    ('crm_order_export.csv', order, 'shop_cd'),
                                    ('crm_shop.csv', shop, 'shop_cd')):
        padded = [r['source_row'] for r in rows
                  if r['raw'][column] not in MISSING and r['raw'][column] != r['raw'][column].strip()]
        item = anomaly(f'门店码含首尾空白（含全角空格）：{len(padded)} 条', filename, padded)
        if item:
            anomalies.append(item)

    # 门店码：非 4 位 ASCII 数字（字母编码、全角数字、变体）
    for filename, rows, column in (('crm_member_export.csv', member, 'reg_shop'),
                                    ('crm_order_export.csv', order, 'shop_cd'),
                                    ('crm_shop.csv', shop, 'shop_cd')):
        lettered = [r['source_row'] for r in rows
                    if r['raw'][column] not in MISSING
                    and not re.match(r'^[0-9]{4}$', r['raw'][column].strip())]
        item = anomaly(f'门店码非 4 位 ASCII 数字（字母编码/全角数字等）：{len(lettered)} 条',
                       filename, lettered)
        if item:
            anomalies.append(item)

    # 门店码：归一后可对上门店表的变体写法（空格/全角/小写）
    for filename, rows, column in (('crm_member_export.csv', member, 'reg_shop'),
                                    ('crm_order_export.csv', order, 'shop_cd')):
        variant = [r['source_row'] for r in rows
                   if r['raw'][column] not in MISSING
                   and norm_code(r['raw'][column]) != r['raw'][column]
                   and norm_code(r['raw'][column]) in shop_codes]
        item = anomaly(f'门店码变体写法（空格填充/全角/小写，归一后指向门店表已有门店）：{len(variant)} 条',
                       filename, variant)
        if item:
            anomalies.append(item)

    # tag 分隔符混用（分号/全角逗号）
    sep_rows = [r['source_row'] for r in member
                if r['raw']['tag'] not in MISSING
                and any(s in r['raw']['tag'] for s in (';', '；', '，'))]
    item = anomaly(f'标签分隔符混用（除半角逗号外还使用分号/全角逗号）：{len(sep_rows)} 条',
                   'crm_member_export.csv', sep_rows)
    if item:
        anomalies.append(item)

    # tag 内叙述性手记（超长片段）
    note_rows = []
    for r in member:
        tag = r['raw']['tag']
        if tag in MISSING:
            continue
        pieces = re.split(r'[,;，；]', tag)
        if any(len(p.strip()) > 12 for p in pieces):
            note_rows.append(r['source_row'])
    item = anomaly(f'标签列混入叙述性手记（片段超过 12 字）：{len(note_rows)} 条',
                   'crm_member_export.csv', note_rows)
    if item:
        anomalies.append(item)

    # reg_dev 解析陷阱（形如 8861e48147070391，float() 会得到 inf 或错误量级）
    trap_rows = [r['source_row'] for r in member
                 if r['raw']['reg_dev'] not in MISSING
                 and re.match(r'^[0-9]+[eE][0-9]+$', r['raw']['reg_dev'])]
    item = anomaly(f'设备号形如数字e数字（float() 会解析为 inf 或错误量级的陷阱值）：{len(trap_rows)} 条',
                   'crm_member_export.csv', trap_rows)
    if item:
        anomalies.append(item)

    # 手机号掩码
    masked = [r['source_row'] for r in member if '*' in r['raw']['mobile']]
    item = anomaly(f'手机号为掩码形态（如 135****7967）：{len(masked)} 条',
                   'crm_member_export.csv', masked)
    if item:
        anomalies.append(item)

    # 空值多种写法（NULL/-/无，非真空）
    for name in ('crm_member_export.csv', 'crm_card_export.csv'):
        rows = by_role.get(ROLES.get(name, ''), {}).get('rows', [])
        styled = [r['source_row'] for r in rows
                  if any(r['raw'][f] in ('NULL', '-', '无') for f in
                         (by_role.get(ROLES.get(name, ''), {}).get('fields') or []))]
        item = anomaly(f'空值使用 NULL/-/无 等写法（与真空值并存）：{len(styled)} 条', name, styled)
        if item:
            anomalies.append(item)

    # ---- 字典差异（dictionary_differences[]），actual 全部现算 ----
    if '1 普通，2 银卡，3 金卡' in dictionary:
        values = Counter(r['raw']['lv'] for r in member if r['raw']['lv'] not in MISSING)
        differences.append(difference(
            'crm_member_export.csv', 'lv', '代码：1 普通，2 银卡，3 金卡',
            '中文文本：' + '、'.join(f'{v}×{n}' for v, n in values.most_common()),
            '等级映射须按中文取值建立；按字典数字代码读会整列失败'))
    if '1 正常，2 冻结，3 注销' in dictionary:
        extra = Counter(r['raw']['stat'] for r in member
                        if r['raw']['stat'] not in ('1', '2', '3', ) and r['raw']['stat'] not in MISSING)
        if extra:
            differences.append(difference(
                'crm_member_export.csv', 'stat', '代码：1 正常，2 冻结，3 注销',
                '存在字典外取值：' + '、'.join(f'{v}×{n}' for v, n in extra.most_common()),
                '状态 0 等新值的业务含义须访谈确认后才能定去留'))
    if '门店、小程序、商城' in dictionary:
        extra = Counter(r['raw']['src_ch'] for r in member
                        if r['raw']['src_ch'] not in ('门店', '小程序', '商城', ''))
        if extra:
            differences.append(difference(
                'crm_member_export.csv', 'src_ch', '门店、小程序、商城',
                '存在字典外渠道：' + '、'.join(f'{v}×{n}' for v, n in extra.most_common()),
                '系统导入会员无设备号；渠道维度须扩枚举'))
    if '11 位' in dictionary:
        masked_n = sum(1 for r in member if '*' in r['raw']['mobile'])
        if masked_n:
            differences.append(difference(
                'crm_member_export.csv', 'mobile', '11 位手机号',
                f'{masked_n} 条为掩码形态（3 位＋****＋4 位）',
                '手机号不可用于触达；脱敏设置与原件去向须访谈确认'))
    if '4 位数字' in dictionary:
        bad = sum(1 for r in member if r['raw']['reg_shop'] not in MISSING
                  and not re.match(r'^[0-9]{4}$', r['raw']['reg_shop'].strip()))
        if bad:
            differences.append(difference(
                'crm_member_export.csv', 'reg_shop', '门店编码，4 位数字，见门店表',
                f'{bad} 条为字母编码、全角数字或空格填充变体',
                '清洗须去空白＋全角转半角＋大写后关联门店表，不能按数字解析'))
    if '注册日期' in dictionary:
        fmts = Counter('YYYYMMDD' if re.match(r'^[0-9]{8}$', r['raw']['join_dt'])
                       else ('YYYY/M/D' if '/' in r['raw']['join_dt'] else 'YYYY-MM-DD')
                       for r in member if r['raw']['join_dt'] not in MISSING)
        if len(fmts) > 1:
            differences.append(difference(
                'crm_member_export.csv', 'join_dt', '日期（未规定格式）',
                '多种格式并存：' + '、'.join(f'{k}×{v}' for k, v in fmts.most_common()),
                '入库前须按多格式显式解析归一为 ISO 日期'))
    for column in ('create_tm', 'reg_dev'):
        if f'`{column}`' not in dictionary and any(
                column in (t or {}).get('fields', []) for t in [by_role.get('member')]):
            differences.append(difference(
                'crm_member_export.csv', column, '（字典无此字段）',
                f'数据实际存在该字段，共 {len(member)} 条',
                '字段含义与口径须访谈确认；reg_dev 含 float() 陷阱值，只能按文本处理'))
    if '附录' in dictionary and '标签' in dictionary:
        claimed = parse_dict_tags(dictionary)
        tokens = Counter()
        for r in member:
            tag = r['raw']['tag']
            if tag in MISSING:
                continue
            for piece in re.split(r'[,;，；]', tag):
                piece = piece.strip()
                if piece:
                    tokens[piece] += 1
        unknown = {t: n for t, n in tokens.items() if t not in claimed}
        if claimed and (unknown or len(tokens) > len(claimed)):
            differences.append(difference(
                'crm_member_export.csv', 'tag',
                f'多个标签用逗号分隔，取值见附录标签表（{len(claimed)} 个）',
                f'独立标签 {len(tokens)} 个，其中字典外 {len(unknown)} 个；'
                f'分隔符混用（分号/全角逗号）；混入叙述性手记',
                '附录标签表严重不全；标签拆分须兼容多分隔符，手记须完整保留为备注，未知标签不删除'))
    if '单位：分' in dictionary:
        for filename, rows, column in (('crm_order_export.csv', order, 'amt_total'),
                                       ('crm_order_export.csv', order, 'amt_pay'),
                                       ('crm_order_export.csv', order, 'amt_rfd'),
                                       ('crm_card_export.csv', card, 'pay_amt')):
            decimals = sum(1 for r in rows if '.' in r['raw'][column])
            if decimals:
                example = next(r['raw'][column] for r in rows if '.' in r['raw'][column])
                differences.append(difference(
                    filename, column, '整数，单位：分',
                    f'{decimals} 条带小数（如 {example}），量级为元',
                    '金额换算须按 Decimal ×100 转分，否则全部金额指标错 100 倍'))
                break  # 三列同源，报一次代表，其余在清洗规则逐列处理
    if '唯一' in dictionary:
        dup_groups = sum(1 for g in ord_groups.values() if len(g) > 1)
        if dup_groups:
            differences.append(difference(
                'crm_order_export.csv', 'ord_no', '唯一',
                f'{dup_groups} 个订单号重复出现（均整行相同）',
                '导入须去重，否则订单数与金额指标虚增'))
    claimed_kinds = parse_dict_list(dictionary, 'card_kind')
    if claimed_kinds:
        extra = Counter(r['raw']['card_kind'] for r in card
                        if r['raw']['card_kind'] not in claimed_kinds)
        if extra:
            differences.append(difference(
                'crm_card_export.csv', 'card_kind', '、'.join(claimed_kinds),
                '存在字典外卡种：' + '、'.join(f'{v}×{n}' for v, n in extra.most_common()),
                '悦享年卡与悦享卡（年）疑似同物异写，须访谈确认后合并映射'))
    if '华东、华南、华北' in dictionary:
        extra = Counter(r['raw']['area'] for r in shop
                        if r['raw']['area'] not in ('华东', '华南', '华北', ''))
        if extra:
            differences.append(difference(
                'crm_shop.csv', 'area', '华东、华南、华北',
                '存在字典外大区：' + '、'.join(f'{v}×{n}' for v, n in extra.most_common()),
                '大区维度须扩枚举，报表分组不能按字典三区硬编码'))
    if '4 位数字' in dictionary:
        bad = sum(1 for r in shop if not re.match(r'^[0-9]{4}$', r['raw']['shop_cd'].strip()))
        if bad:
            differences.append(difference(
                'crm_shop.csv', 'shop_cd', '4 位数字，唯一',
                f'{bad} 家为字母编码（新店）、全角数字或空格填充',
                '门店码解析不能假定纯 ASCII 数字；新店编码体系须访谈确认'))

    return {'contract_version': CONTRACT_VERSION,
            'data_version': context['data_version'],
            'fields': fields,
            'anomalies': anomalies,
            'dictionary_differences': differences}


def parse_dict_tags(dictionary):
    """Extract tag names from the dictionary appendix table (the LAST '附录')."""
    appendix = dictionary.rpartition('附录')[2] if '附录' in dictionary else ''
    tags = []
    for line in appendix.splitlines():
        match = re.match(r'^\|\s*([^|]+)\|', line)
        if match:
            name = match.group(1).strip()
            if name and name != '标签' and not name.startswith('-'):
                tags.append(name)
    return tags


def adapt(tables, rules, context):
    """Execute YAML rules, map fields, record all dispositions, and write coverage.

    Return tables, record_counts, field_mapping, samples, coverage_notes.
    See examples/w04/wutong/customer/w04/solution.py for the same interface.
    """
    delimiters = rules['tag_cleaning']['delimiters']
    splitter = re.compile('|'.join(re.escape(d) for d in delimiters))
    tags = _legal_tags(context, rules['tag_cleaning']['legal_tags_source'])
    values = _value_map(context)
    missing = {}
    for setting in rules['invalid_values']:
        if setting['action'] not in ('null_out', 'null_out_and_drop'):
            raise ValueError('INVALID_VALUE_ACTION_UNSUPPORTED:' + setting['action'])
        for field in setting['source_fields']:
            missing[field] = set(setting['values'])
    config = {item['rule_id']: item for item in rules['abnormal_records']}

    result = {name: [] for name in ('members', 'orders', 'cards', 'stores',
                                    'member_tags', 'member_notes', 'quarantine')}
    counts = {kind: {'read': len(tables[filename]['rows']), 'accepted': 0,
                     'quarantined': 0, 'deduplicated': 0}
              for kind, filename in W04_FILES.items()}
    samples = []
    order_flags = []
    accepted_members = set()
    store_ids = set()
    quarantined_rows = set()
    seen_tags_notes = set()

    def isolate(kind, row, code):
        key = (row['source_file'], row['source_row'])
        if key in quarantined_rows:
            raise ValueError('QUARANTINE_KEY_CONFLICT:%s:%s' % key)
        quarantined_rows.add(key)
        counts[kind]['quarantined'] += 1
        result['quarantine'].append({'record_type': kind, 'source_file': row['source_file'],
                                     'source_row': row['source_row'], 'reason_code': code,
                                     'raw_json': json.dumps(row['raw'], ensure_ascii=False, sort_keys=True)})
        if not any(s['status'] == 'quarantined' for s in samples):
            samples.append({'source_file': row['source_file'], 'source_row': row['source_row'],
                            'status': 'quarantined',
                            'destination': 'quarantine.csv 记录 %d' % len(result['quarantine']),
                            'reason': code})

    def flag(row, code):
        order_flags.append({'order_id': row['raw']['ord_no'], 'flag': code,
                            'orig_ord_stat': row['raw']['ord_stat'],
                            'source_row': row['source_row']})

    # ---- 门店先落地：会员归属店与订单成交店都要对它 ----
    for row in tables[W04_FILES['shop']]['rows']:
        raw = row['raw']
        store_id = _store_code(raw['shop_cd'])
        if not store_id:
            isolate('shop', row, 'INVALID_STORE_CODE')
            continue
        if store_id in store_ids:
            isolate('shop', row, 'DUPLICATE_PRIMARY_KEY')
            continue
        result['stores'].append({'store_id': store_id, 'region': raw['area'].strip(),
                                 'store_name': raw['shop_nm'].strip()})
        store_ids.add(store_id)
        counts['shop']['accepted'] += 1

    # ---- 会员：扩展三列 + 标签与备注 ----
    for row in tables[W04_FILES['member']]['rows']:
        raw = row['raw']
        member_id = raw['hy_id']
        try:
            home = _store_code(raw['reg_shop'])
            if home not in store_ids:
                raise ValueError('UNLINKED_STORE')
            created = (raw['create_tm'] or '').strip()[:10]
            if not DATE_RE.match(created):
                raise ValueError('INVALID_CREATED_AT')
            mapped = {'member_id': member_id,
                      'registered_at': _date(raw['join_dt']),
                      'home_store_id': home,
                      'tier': _mapped(values, 'lv', raw['lv']),
                      'account_status': _mapped(values, 'stat', raw['stat']),
                      'registered_channel': _mapped(values, 'src_ch', raw['src_ch']),
                      'created_at': created}
        except ValueError as exc:
            isolate('member', row, str(exc))
            continue
        result['members'].append(mapped)
        accepted_members.add(member_id)
        counts['member']['accepted'] += 1
        if not any(s['status'] == 'accepted' for s in samples):
            samples.append({'source_file': row['source_file'], 'source_row': row['source_row'],
                            'status': 'accepted',
                            'destination': 'members.csv 记录 %d' % len(result['members']),
                            'reason': '门店可关联、日期三形态均解析、状态与渠道在契约白名单内'})
        _tags_and_notes(row, raw['tag'], missing.get('tag', set()), tags, splitter,
                        member_id, result, seen_tags_notes)

    # ---- 订单：先去重、再判孤儿、再映射 ----
    seen = set()
    for row in tables[W04_FILES['order']]['rows']:
        raw = row['raw']
        identity = tuple(raw[name] for name in tables[W04_FILES['order']]['fields'])
        if identity in seen:
            counts['order']['deduplicated'] += 1
            continue
        seen.add(identity)
        if raw['hy_id'] not in accepted_members:
            isolate('order', row, 'UNLINKED_ACCOUNT')
            continue
        try:
            store_id = _store_code(raw['shop_cd'])
            if store_id not in store_ids:
                raise ValueError('UNLINKED_STORE')
            order = {'order_id': raw['ord_no'],
                     'member_id': raw['hy_id'],
                     'store_id': store_id,
                     'ordered_at': _date(raw['ord_tm']),
                     'status': _mapped(values, 'ord_stat', raw['ord_stat']),
                     'gross_cents': _cents(raw['amt_total']),
                     'paid_cents': _cents(raw['amt_pay']),
                     'refund_cents': _cents(raw['amt_rfd']),
                     'quantity': int(raw['qty']),
                     'channel': _mapped(values, 'ch', raw['ch'])}
        except ValueError as exc:
            isolate('order', row, str(exc))
            continue
        result['orders'].append(order)
        counts['order']['accepted'] += 1
        if not any(s['status'] == 'accepted' for s in samples):
            samples.append({'source_file': row['source_file'], 'source_row': row['source_row'],
                            'status': 'accepted',
                            'destination': 'orders.csv 记录 %d' % len(result['orders']),
                            'reason': '会员与门店均可关联、金额与日期按规则换算'})
        if order['refund_cents'] > order['paid_cents']:
            flag(row, config['refund_exceeds_paid']['reason_code'])
        if raw['ord_stat'] == '已支付':
            flag(row, config['paid_status_anomaly']['reason_code'])

    # ---- 卡：卡种走值映射，员工卡落"员工内购" ----
    for row in tables[W04_FILES['card']]['rows']:
        raw = row['raw']
        if raw['hy_id'] not in accepted_members:
            isolate('card', row, 'UNLINKED_ACCOUNT')
            continue
        try:
            ended = raw['stop_dt'].strip()
            card = {'card_id': raw['card_no'],
                    'member_id': raw['hy_id'],
                    'card_type': _mapped(values, 'card_kind', raw['card_kind']),
                    'valid_from': _date(raw['st_dt']),
                    'valid_until': _date(raw['ed_dt']),
                    'ended_at': None if ended in missing.get('stop_dt', MISSING) else _date(ended),
                    'card_paid_cents': _cents(raw['pay_amt'])}
        except ValueError as exc:
            isolate('card', row, str(exc))
            continue
        result['cards'].append(card)
        counts['card']['accepted'] += 1

    coverage = {'source': '本次只含新 CRM 的四个导出文件；门店老收银系统里还有一部分会员的消费记录，这次没有导出，'
                          '所以这份 CRM 订单不能当作完整的销售数据（老周 MSG-05318）。',
                'time_range': {'start': '2024-09-01', 'end_exclusive': '2026-09-01'},
                'quarantined': {kind: counts[kind]['quarantined'] for kind in counts}}
    excess = sum(o['refund_cents'] > o['paid_cents'] for o in result['orders'])
    staff = [c for c in result['cards'] if c['card_type'] == '员工内购']
    coverage['source'] += (
        ' 迁移前未导出的订单及商品明细未取得，不能当零或据此分析商品结构。'
        ' 保留退款大于实付的订单 %d 笔，原金额不修正；全体订单口径的净销售额包含其负净额，'
        '有效购买、月度购买净销售额与月度复购按净额大于零筛选，不含这些订单；'
        '课程方 QH4-03 已说明其为历史手工补录错误，正确金额仍待逐笔凭据；'
        '包含错误负净额的全体净销售仅供异常核对，不作为正式经营结论。'
        ' 员工内购卡 %d 张（%d 个账户）留库，员工卡本身不授予月报付费资格；'
        '同账户其他范围内有效卡独立判定。员工账户的订单未从全体订单指标中一概排除。'
        % (excess, len(staff), len({c['member_id'] for c in staff})))
    return {'tables': result, 'record_counts': counts,
            'field_mapping': _field_mapping(),
            'samples': samples, 'coverage_notes': coverage,
            'order_flags': order_flags}


W04_FILES = {'member': 'crm_member_export.csv', 'order': 'crm_order_export.csv',
             'card': 'crm_card_export.csv', 'shop': 'crm_shop.csv'}
W04_TABLES = {'member': 'members', 'order': 'orders', 'card': 'cards', 'shop': 'stores'}
SLASH_RE = re.compile(r'^[0-9]{4}/[0-9]{2}/[0-9]{2}$')
COMPACT_RE = re.compile(r'^[0-9]{8}$')
CATEGORY_KEYWORDS = (
    ('触达限制', ('勿打电话', '勿发短信')),
    ('卡务', ('卡务', '续卡', '卡费', '金额卡', '办卡', '会员卡', '储值卡')),
    ('客户关系', ('熟客', '客户关系', '老客户', 'VIP', 'vip')),
    ('联系状态', ('服务', '联系状态', '电话', '号码', '微信', '这阵子不方便接听')),
)


def _aux_path(context, relative):
    """Rules live in artifacts/w04; lists they read may sit there or under customer/w04."""
    name = Path(relative).name
    for candidate in (Path(context['rules_dir']).parent.parent / relative,
                      Path(context['rules_dir']).parent / relative,
                      Path(context['rules_dir']) / name,
                      Path(relative)):
        if candidate.is_file():
            return candidate
    raise ValueError('AUX_FILE_MISSING:' + relative)


def _rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def _legal_tags(context, source):
    rows = _rows(_aux_path(context, source))
    return [row['tag'] for row in sorted(rows, key=lambda r: int(r['match_order']))]


def _value_map(context):
    mapping = {}
    for row in _rows(_aux_path(context, 'customer/w04/value_mapping.csv')):
        mapping[(row['source_field'], row['source_value'])] = row['target_value']
    return mapping


def _mapped(mapping, field, value):
    key = (field, (value or '').strip())
    if key not in mapping:
        raise ValueError('UNMAPPED_VALUE:%s:%s' % (field, key[1]))
    return mapping[key]


def _date(value):
    text = (value or '').strip()
    if len(text) > 10 and text[10] == ' ':
        text = text[:10]
    if COMPACT_RE.match(text):
        text = text[:4] + '-' + text[4:6] + '-' + text[6:]
    elif SLASH_RE.match(text):
        text = text.replace('/', '-')
    try:
        return datetime.strptime(text, '%Y-%m-%d').date().isoformat()
    except ValueError:
        raise ValueError('INVALID_DATE') from None


def _cents(value):
    text = (value or '').strip()
    if text in MISSING:
        raise ValueError('INVALID_MONEY')
    try:
        number = Decimal(text) * 100
    except InvalidOperation:
        raise ValueError('INVALID_MONEY') from None
    if not number.is_finite() or number != number.to_integral_value():
        raise ValueError('INVALID_MONEY')
    return int(number)


def _store_code(value):
    return unicodedata.normalize('NFKC', value or '').replace('\u3000', '').strip().upper()


def _category(note):
    for label, words in CATEGORY_KEYWORDS:
        if any(word in note for word in words):
            return label
    return '其他'


def _tags_and_notes(row, raw_tag, missing_values, tags, splitter, member_id, result, seen):
    """Keep the remaining note whole: punctuation inside a note is not a boundary."""
    if (raw_tag or '').strip() in missing_values:
        return
    rest = raw_tag or ''
    for tag in tags:
        if tag in rest:
            rest = rest.replace(tag, '\u0000' * len(tag))
            key = ('tag', member_id, tag)
            if key not in seen:
                seen.add(key)
                result['member_tags'].append({'member_id': member_id, 'tag': tag})
    leftover = rest.replace('\u0000', '')
    # Only strip separator residue at the outside. Internal commas/slashes stay.
    edge = ' -\u3000\t\r\n/' + ''.join(
        re.sub(r'\\(.)', r'\1', part) for part in splitter.pattern.split('|'))
    note_text = leftover.strip(edge)
    if not note_text:
        return
    key = ('note', member_id, row['source_row'], note_text)
    if key in seen:
        return
    seen.add(key)
    result['member_notes'].append({'member_id': member_id, 'source_file': row['source_file'],
                                   'source_row': row['source_row'], 'source_field': 'tag',
                                   'raw_text': raw_tag, 'note_text': note_text,
                                   'category': _category(note_text)})


def _field_mapping():
    mapping = []
    defined = {
        'crm_member_export.csv': [
            ('member_id', ['hy_id'], '保留稳定原编号，不 trim、不改大小写'),
            ('registered_at', ['join_dt'], '三种写法统一 YYYY-MM-DD：ISO 直取、斜杠改连字符、8 位紧凑插连字符'),
            ('home_store_id', ['reg_shop'], 'NFKC 全角转半角、去空白、转大写，与门店表 403/403 可对'),
            ('tier', ['lv'], '原值直取中文（普通／银卡／金卡），不自造英文枚举'),
            ('account_status', ['stat'], '0→未激活、1→活跃、2→冻结、3→注销（契约白名单无"正常"）'),
            ('registered_channel', ['src_ch'], '原值直取；"系统导入"是契约内合法值，单列不与其他渠道混算'),
            ('created_at', ['create_tm'], '取前 10 位日期（建档时间，与 join_dt 不同源）'),
            ('member_tags.tag', ['tag'], '16 词表最长匹配；连字符属标签名不切；缺失标记不产标签'),
            ('member_notes.raw_text', ['tag'], '保留该格完整原值，一字不改'),
            ('member_notes.note_text', ['tag'], '整格识别正式标签，剩余备注整条保留，内部逗号不切分；原格完整保留于 raw_text'),
            ('member_notes.category', ['tag'], '按关键词归入契约 5 值：触达限制→卡务→客户关系→联系状态→其他'),
        ],
        'crm_order_export.csv': [
            ('order_id', ['ord_no'], '原样'),
            ('member_id', ['hy_id'], '与会员表关联；关联不上进 quarantine（UNLINKED_ACCOUNT）'),
            ('store_id', ['shop_cd'], 'NFKC、去空白、转大写'),
            ('ordered_at', ['ord_tm'], '取日期前 10 位'),
            ('status', ['ord_stat'], '已完成／已支付／部分退款／全额退款→paid，已取消→cancelled；原值保留在原始CSV，异常订单另存order_flags.csv'),
            ('gross_cents', ['amt_total'], 'Decimal 元乘 100 转整数分，禁 float'),
            ('paid_cents', ['amt_pay'], 'Decimal 元乘 100 转整数分'),
            ('refund_cents', ['amt_rfd'], 'Decimal 元乘 100 转整数分；大于实付只打标不改数'),
            ('quantity', ['qty'], '转整数'),
            ('channel', ['ch'], '原值直取（门店／小程序／商城均在白名单内）'),
        ],
        'crm_card_export.csv': [
            ('card_id', ['card_no'], '原样'),
            ('member_id', ['hy_id'], '与会员表关联'),
            ('card_type', ['card_kind'], '悦享卡（年）并入悦享年卡；员工卡→员工内购，本卡不授予付费资格；不据此认定免费身份或排除账户普通购物'),
            ('valid_from', ['st_dt'], '原样 ISO 日期'),
            ('valid_until', ['ed_dt'], '原样 ISO 日期'),
            ('ended_at', ['stop_dt'], '四种缺失写法（空／NULL／-／无）转空值，不填当天不推算'),
            ('card_paid_cents', ['pay_amt'], 'Decimal 元乘 100 转整数分'),
        ],
        'crm_shop.csv': [
            ('store_id', ['shop_cd'], 'NFKC、去空白、转大写；字母码 A051~N172 为 2025 年后新店，合法'),
            ('region', ['area'], '原值直取'),
            ('store_name', ['shop_nm'], '原值直取'),
        ],
    }
    for source_file, items in defined.items():
        for target, sources, transformation in items:
            mapping.append({'source_file': source_file, 'source_fields': sources,
                            'target': target, 'transformation': transformation})
    return mapping


def reconcile(payload):
    """Compute adapter_test_report from raw, cleaned and both imported databases."""
    meta = payload['metadata']
    manifest = payload['manifest']
    counts = meta['record_counts']
    rows = []
    all_balanced = True
    for kind, filename in W04_FILES.items():
        values = counts[kind]
        read = len(payload['source'][filename]['rows'])
        actual = payload['first']['counts'].get('raw_' + W04_TABLES[kind], 0)
        balanced = (read == values['read'] == values['accepted'] + values['quarantined'] + values['deduplicated']
                    and actual == values['accepted'])
        all_balanced = all_balanced and balanced
        rows.append({'record_type': kind, 'read': values['read'], 'accepted': values['accepted'],
                     'quarantined': values['quarantined'], 'deduplicated': values['deduplicated'],
                     'reconciliation': {'balanced': balanced,
                                        'evidence': '源文件 %d = 接受 %d + 隔离 %d + 去重 %d；库内实到 %d'
                                                    % (read, values['accepted'], values['quarantined'],
                                                       values['deduplicated'], actual)}})
    clean = payload['cleaned']['orders.csv']['rows']
    total = sum(int(record['raw']['paid_cents']) for record in clean)
    before, after = payload['first']['counts'], payload['second']['counts']
    repeat = before == after
    good = (all_balanced and repeat
            and len(clean) == payload['first']['order_count'] == payload['second']['order_count']
            and total == payload['first']['paid_cents'] == payload['second']['paid_cents'])
    return {'contract_version': CONTRACT_VERSION, 'data_version': manifest['id'],
            'field_mapping': meta['field_mapping'], 'record_counts': rows,
            'samples': meta['samples'],
            'repeat_import': {'first_run_id': payload['first_run_id'],
                              'second_run_id': payload['second_run_id'],
                              'before': before, 'after': after, 'row_counts_equal': repeat},
            'test_result': {'passed': good,
                            'details': '清洗后订单 %d 条、实付 %d 分；两次独立导入的表计数与金额逐项比对。'
                                       % (len(clean), total)}}
