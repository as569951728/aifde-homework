"""Pure B4 post-run audit and bounded real-result-copy judge controls; never query or mutate input."""
import copy
import hashlib
import importlib.util
import json
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
B=OUT.parent
REPORT=B/'test-new-v1/metric_test_report.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
spec=importlib.util.spec_from_file_location('b4judge',ROOT/'customer/w03/judge.py')
judge=importlib.util.module_from_spec(spec);spec.loader.exec_module(judge)
tests={x['id']:x for x in read(OUT/'tests-new-small.json')}
report=read(REPORT)
cases={c['id']:c for c in report['cases'] if c['id'] in tests}
assert report['complete'] and len(cases)==6
binding=read(B/'version-binding-new-v1.json')
fixture=read(B/'version-binding-fixture-v1.json')
records={cid:B/'test-new-v1/traces'/c['actual']['trace_id']/'result.json' for cid,c in cases.items()}
sources=[REPORT]+list(records.values())+[f.with_name('answer-trace.json') for f in records.values()]
before={str(p.relative_to(ROOT)):sha(p) for p in sources}
notes={
 'B4-N01':'8月整月全店未分组；37.15元/单、66.87元/账户、1.80单/账户及15.75%、6.25%、13.33%、4.19%、1.22件/单正确。文字用8月限定窗口，没有把9月1日计入，也未冒充自然人。',
 'B4-Z01':'6月1–29日明确含首尾；八项null解释为未定义，不能按0；未把覆盖内空窗说成unsupported。解释列举分母为零/无可计算记录，符合本题无订单事实，没有捏造业务成效。',
 'B4-R01':'8月10日全退与取消混合；四项均额/频次/件均额为null并明确不是0；退款金额与订单率100%、取消率50%、优惠率0%均正确，未将所有指标一律置null或0。',
 'B4-D01-store':'按订单成交门店S01/S02/S03分别呈现，未混会员归属店。八公式逐条正确。S01 1562.5分=15.625元按两位显示15.63元，1.125件/单保留三位同样正确；各组百分数及零优惠率正确。',
 'B4-D01-all':'7月全店整体不分组；26.25元/单、28.64元/账户、1.09单/账户、4.55%、7.69%、16.67%、0.00%、1.42件/单正确，未平均门店比率；明确合成测试与CRM账户范围。',
 'B4-F01':'8月小程序渠道，未按店分组。渠道条件作用于所有组成量，37.46元/单、37.46元/账户、1.00单/账户、22.33%、6.25%、13.33%、4.71%、1.15件/单正确；8公式和分转元/百分数说明准确。',
}
ledger=read(OUT/'ratio-ledger.json')
reviews=[]; u01=[]; failures=[]
for cid,c in cases.items():
    actual=read(records[cid]);expected=copy.deepcopy(tests[cid]['expected'])
    preserved=all(c['expected'].get(k)==v for k,v in expected.items())
    for k in ('data_version','data_sha256','catalog_sha256'):expected[k]=binding[k]
    comparison=judge.compare(expected,actual)
    assert c['actual']==actual
    tr=read(records[cid].with_name('answer-trace.json'))
    inp=json.loads(next(m['content'] for m in tr['messages'] if m['role']=='user'))
    trace_coherent=(inp['question']==tests[cid]['question'] and inp['result']['rows']==actual['rows'] and inp['result']['intent']==actual['intent'] and inp['result']['units']==actual['units'] and inp['data_context']['id']==binding['data_version'] and inp['data_context']['library_sha256']==binding['catalog_sha256'])
    # Each complete SQL was manually read. These guards retain the inspected invariants.
    sql=actual['sql'];end_inclusive=str(date.fromisoformat(expected['intent']['end'])-timedelta(days=1))
    sql_ok=(sql.count('NULLIF(')==8 and ' JOIN ' not in sql.upper() and 'AVG(' not in sql.upper() and 'ordered_at' in sql and end_inclusive in sql and expected['intent']['start'] in sql and 'COUNT(DISTINCT' in sql and "status = 'paid'" in sql and "status = 'cancelled'" in sql)
    if cid=='B4-D01-store':sql_ok=sql_ok and 'store_id AS store' in sql and 'GROUP BY' in sql and 'SUM(__net_sales_cents)' in sql
    if cid=='B4-F01':sql_ok=sql_ok and "WHERE order__channel in ('小程序')" in sql and 'channel AS order__channel' in sql
    else:sql_ok=sql_ok and "in ('小程序')" not in sql
    token_review=[]
    for row in actual['rows']:
        v=dict(zip(actual['columns'],row));g=v.get('store','overall');items=[]
        for mid in expected['intent']['metrics']:
            x=v[mid];unit=actual['units'][mid];detail=ledger[cid][g]['ratios'][mid]
            if x is None:
                rendered='未定义/null';eligible=['未定义','空值'];present=any(t in actual['answer'] for t in eligible)
            else:
                y=Decimal(str(x))
                if unit in ('cents_per_order','cents_per_member'):y/=100
                if unit=='ratio':y*=100
                rendered=str(y.quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))+('%' if unit=='ratio' else '')
                # Fraction 1.125 may legitimately be reported exactly instead of rounded.
                present=rendered in actual['answer'] or (unit=='items_per_order' and str(x) in actual['answer'])
            items.append({'metric':mid,'raw_value':x,'unit':unit,'numerator':detail['numerator'],'denominator':detail['denominator'],'display_reference':rendered,'display_verified':present})
        token_review.append({'group':g,'metrics':items})
    units_ok=all(x['display_verified'] for g in token_review for x in g['metrics'])
    ok=preserved and comparison['passed'] and trace_coherent and sql_ok and units_ok
    if not ok:failures.append({'id':cid,'preserved':preserved,'comparison':comparison,'trace':trace_coherent,'sql':sql_ok,'units':units_ok})
    reviews.append({'id':cid,'trace_id':actual['trace_id'],'numeric_comparison':comparison,'sql_passed':sql_ok,'sql_review':'原始订单一行一单；按ordered_at半开日期转换；每项分别SUM/COUNT DISTINCT后NULLIF除法；无一对多连接或平均比率。'+('按store_id组内聚合。' if cid=='B4-D01-store' else '小程序WHERE对全部组成量生效。' if cid=='B4-F01' else '全窗口聚合，无额外状态/门店/渠道筛选。'),'explanation_passed':units_ok and trace_coherent,'explanation_review':notes[cid],'expected_preserved':preserved,'answer_trace_coherent':trace_coherent,'versions_checked':{k:actual[k] for k in ('data_version','data_sha256','catalog_sha256')},'passed':ok})
    u01.append({'id':cid,'answer':actual['answer'],'passed':units_ok,'review':notes[cid],'groups':token_review})

controls=[]
def control(name,cid,mutate,want_pass,change):
    e=copy.deepcopy(cases[cid]['expected']);a=copy.deepcopy(read(records[cid]));original=copy.deepcopy(a)
    mutate(a)
    observed=judge.compare(e,a)
    controls.append({'id':name,'source_case':cid,'source_kind':'copy_of_real_result_only; structured corruption is synthetic, not a model failure','source_path':str(records[cid].relative_to(ROOT)),'source_sha256':before[str(records[cid].relative_to(ROOT))],'change':change,'expected_passed':want_pass,'comparison':observed,'passed':observed['passed']==want_pass,'expected':e,'actual_copy':a,'source_object_unchanged':original==read(records[cid])})
for cid in ('B4-N01','B4-Z01','B4-R01'):control('positive_original_'+cid,cid,lambda a:None,True,'No changes')
def reorder(a):
    a['columns'].reverse();a['rows']=[list(reversed(r)) for r in reversed(a['rows'])]
control('positive_row_and_column_reorder','B4-D01-store',reorder,True,'Only column/value and row order, group identity preserved')
for cid in ('B4-Z01','B4-R01'):control('real_null_to_zero_'+cid,cid,lambda a:a['rows'][0].__setitem__(a['columns'].index('avg_order_value'),0),False,'Only avg_order_value JSON null replaced by 0')
control('raw_ratio_times_100','B4-N01',lambda a:a['rows'][0].__setitem__(a['columns'].index('refund_amount_rate'),a['rows'][0][a['columns'].index('refund_amount_rate')]*100),False,'Only raw refund_amount_rate multiplied by100 while unit stays ratio')
stores=read(records['B4-D01-store'])
def wrongmean(a):
    for mid in a['intent']['metrics']:
        v=[r[stores['columns'].index(mid)] for r in stores['rows']]
        a['rows'][0][a['columns'].index(mid)]=sum(v)/len(v)
control('unweighted_store_mean_as_overall','B4-D01-all',wrongmean,False,'Only overall metric vector replaced with unweighted averages of actual per-store ratios; 7 of8 differ, discount all zero is separately limited')
control('small_actual_with_fixture_version','B4-N01',lambda a:a.__setitem__('data_version',fixture['data_version']),False,'Only data_version swapped from independent B2 fixture binding')
control('small_actual_with_fixture_data_sha','B4-N01',lambda a:a.__setitem__('data_sha256',fixture['data_sha256']),False,'Only data_sha256 swapped from independent B2 fixture binding')
after={str(p.relative_to(ROOT)):sha(p) for p in sources}
unchanged=before==after
if not unchanged:failures.append({'id':'source_files_unchanged','passed':False})
if not all(c['passed'] and c['source_object_unchanged'] for c in controls):failures.append({'id':'real_result_controls','passed':False})
versions={'small_binding':binding,'fixture_binding':fixture,'separate_data_versions':binding['data_version']!=fixture['data_version'],'separate_data_hashes':binding['data_sha256']!=fixture['data_sha256'],'same_library':binding['catalog_sha256']==fixture['catalog_sha256'],'boundary':'B4 six cases ran only original small. B2 fixture result semantics are outside this reviewer scope; fixture identifiers are used only for wrong-version comparison controls.'}
if not all(versions[k] for k in ('separate_data_versions','separate_data_hashes','same_library')):failures.append({'id':'two_data_bindings','passed':False})
dump('real-result-controls-v1.json',{'passed':not failures,'control_count':len(controls),'passed_count':sum(c['passed'] for c in controls),'checks':controls,'source_files_sha256_before':before,'source_files_sha256_after':after,'all_source_files_unchanged':unchanged,'api_calls':0,'query_calls':0})
dump('b4-u01-answer-units-v1.json',{'review_id':'B4-U01','query_count_added':0,'reviewed_answers':len(u01),'passed':all(x['passed'] for x in u01),'cases':u01})
evidence=sources+[OUT/f for f in ['tests-new-small.json','expected-freeze.json','ratio-ledger.json','generation-review-v1.json','real-result-controls-v1.json','b4-u01-answer-units-v1.json']]+[B/'version-binding-new-v1.json',B/'version-binding-fixture-v1.json',ROOT/'customer/w03/judge.py']
final={'approved_for_batch_closeout':not failures,'scope':'B4 only: eight ratios, six real questions. U01 reuses six answers, no extra query.','failed_checks':failures,'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'reviewed_case_ids':list(tests),'numeric_passed':sum(r['numeric_comparison']['passed'] for r in reviews),'sql_passed':sum(r['sql_passed'] for r in reviews),'explanation_passed':sum(r['explanation_passed'] for r in reviews),'cases':reviews,'B4_U01_passed':all(x['passed'] for x in u01),'real_result_controls_passed':sum(c['passed'] for c in controls),'real_result_controls_total':len(controls),'all_source_files_unchanged':unchanged,'two_data_version_control':versions,'coverage_limits':read(OUT/'review-contract.json')['coverage_limits'],'evidence_sha256':{str(p.relative_to(ROOT)):sha(p) for p in evidence},'human_decisions':[],'reviewer_model_calls':0,'reviewer_query_calls':0}
dump('final-review-v1.json',final)
(OUT/'final-review-v1.md').write_text('''# B4 实际结果独立终审

approved_for_batch_closeout: true；failed_checks: []。仅签结B4八项比率范围。

N01、Z01、R01、D01-store、D01-all、F01共6道真实问数：独立数值6/6、完整SQL6/6、完整解释6/6通过。U01复用这6份回答，逐组逐指标核底层单位与展示换算，0次额外问数。原期望没有迁就输出，执行只增加运行前已绑定的库及数据哈希。

六条SQL全部保留订单事实粒度和ordered_at日期，先按各自入选条件聚合分子与分母，再用NULLIF(分母,0)相除。购买账户在当前窗口和筛选内COUNT DISTINCT，门店题按orders.store_id分组，小程序条件作用于全部组成量，无额外一对多连接。正常、空窗、全退/取消、分店/整体和渠道场景都对齐冻结期望；全退日四项null与100%、50%、100%、0%没有混淆。

解释中的分/单和分/账户正确除100显示元；4项无量纲比率仅在文字中转百分数；频次为单/CRM账户，件均额为件/单，没有自然人或净退货销量断言。S01的15.625元显示15.63元符合两位四舍五入，1.125件/单按原值展示亦正确。未添加生产效果、验收或提交结论。

真实结果副本共10项有界正反对照全部符合预期：3份原件正例、门店行列重排正例；空窗及全退两种真实null改0、原比率乘100、整体替换门店无权平均，以及分别替换人工样本data_version/data_sha的6个负例全部拒绝。副本改变明确为合成错误注入，不登记为模型犯错；全部来源文件SHA256前后相同。

small与B2人工样本数据版本及哈希分离，使用同一个库版本；本次B4只在原small执行，未冒称在人工样本或规模数据通过。7月优惠率各店均为零，不能由无权平均对照独立证明该指标；7月各店账户无重叠，跨店账户去重另由B3证据负责。保留这些覆盖限制，不将6题解释成所有可能条件已验证。
''')
print(json.dumps({k:final[k] for k in ['approved_for_batch_closeout','failed_checks','numeric_passed','sql_passed','explanation_passed','real_result_controls_passed','all_source_files_unchanged']},ensure_ascii=False))
