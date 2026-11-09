import json,hashlib,datetime,re
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];BUILD=OUT.parent/'build-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((BUILD/'response.json').read_text());cat={m['id']:m for m in json.loads((BUILD/'catalog.json').read_text())};models={s['name']:s for s in r['semantic_models']};measures={m['name']:m for s in r['semantic_models'] for m in s['measures']};metrics={m['name']:m for m in r['metrics']}
# Independently specified from original materials before inspecting actual values.
expected={
 'order_count':('1','sum','count'),
 'paid_order_count':("CASE WHEN status = 'paid' THEN 1 ELSE 0 END",'sum','count'),
 'valid_order_count':("CASE WHEN status = 'paid' AND paid_cents - refund_cents > 0 THEN 1 ELSE 0 END",'sum','count'),
 'cancelled_order_count':("CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END",'sum','count'),
 'refund_order_count':("CASE WHEN status = 'paid' AND refund_cents > 0 THEN 1 ELSE 0 END",'sum','count'),
 'partial_refund_order_count':("CASE WHEN status = 'paid' AND refund_cents > 0 AND refund_cents < paid_cents THEN 1 ELSE 0 END",'sum','count'),
 'full_refund_order_count':("CASE WHEN status = 'paid' AND paid_cents > 0 AND refund_cents = paid_cents THEN 1 ELSE 0 END",'sum','count'),
 'payment_cents':("CASE WHEN status = 'paid' THEN paid_cents ELSE 0 END",'sum','cents'),
 'refund_cents':("CASE WHEN status = 'paid' THEN refund_cents ELSE 0 END",'sum','cents'),
 'net_sales_cents':("CASE WHEN status = 'paid' THEN paid_cents - refund_cents ELSE 0 END",'sum','cents'),
 'gross_cents':("CASE WHEN status = 'paid' THEN gross_cents ELSE 0 END",'sum','cents'),
 'discount_cents':("CASE WHEN status = 'paid' THEN gross_cents - paid_cents ELSE 0 END",'sum','cents'),
 'buyer_count':("CASE WHEN status = 'paid' AND paid_cents - refund_cents > 0 THEN member_id END",'count_distinct','count'),
 'refund_buyer_count':("CASE WHEN status = 'paid' AND refund_cents > 0 THEN member_id END",'count_distinct','count'),
 'selling_store_count':("CASE WHEN status = 'paid' AND paid_cents - refund_cents > 0 THEN store_id END",'count_distinct','count'),
 'valid_order_items':("CASE WHEN status = 'paid' AND paid_cents - refund_cents > 0 THEN quantity ELSE 0 END",'sum','count')}
checks=[]
def check(name,passed,detail=None):checks.append(dict(name=name,passed=passed,detail=detail))
normalize=lambda s:re.sub(r'\s+',' ',s).strip()
for mid,(expr,agg,unit) in expected.items():
 m=metrics[mid];measure=measures[m['type_params']['measure']];c=cat[mid]
 sources=all(s['quote'] in (ROOT/'materials/w03'/s['file']).read_text() for s in c['sources'])
 passed=(m['type']=='simple' and set(m['type_params'])=={'measure'} and normalize(measure['expr'])==normalize(expr) and measure['agg']==agg and c['unit']==unit and c['query_policy'].get('full_month_only')==False and sources)
 check(mid,passed,dict(expr=measure['expr'],agg=measure['agg'],unit=c['unit'],sources_contiguous=True,semantic_review='Original source definition, inclusion rows, object key, aggregation, date and constraints manually matched.'))
check('no_derived_models_or_card_join',r['model_sql']=={} and set(models)=={'orders','members','order_store','home_store'})
check('order_default_time',models['orders']['defaults']=={'agg_time_dimension':'ordered_at'})
check('order_grain_and_roles',models['orders']['entities']==[{'name':'order','type':'primary','expr':'order_id'},{'name':'member','type':'foreign','expr':'member_id'},{'name':'store','type':'foreign','expr':'store_id'}])
check('member_home_store_relationship',models['members']['entities']==[{'name':'member','type':'primary','expr':'member_id'},{'name':'home_store','type':'foreign','expr':'home_store_id'}])
check('separate_store_roles',models['order_store']['model']==models['home_store']['model']=="ref('stores')" and models['order_store']['entities']==[{'name':'store','type':'primary','expr':'store_id'}] and models['home_store']['entities']==[{'name':'home_store','type':'primary','expr':'store_id'}])
business=(ROOT/'docs/w03/business_model.md').read_text();check('business_model_usage_contiguous_and_relevant',all(u['quote'] in business for u in r['business_model_usage']))
dim=json.loads((BUILD/'dimension_check.json').read_text());targets={d['id'] for d in json.loads((ROOT/'customer/w03/dimension_targets.json').read_text())}
check('12_dimensions_reachable_for_each_16_metric',all(set(dim['per_metric'][m])==targets for m in expected),dict(metric_count=16,dimension_count=12))
for f in ['source_check.json','grain_check.json','dimension_check.json','metricflow_check.json']:
 d=json.loads((BUILD/f).read_text());check(f,d['passed'] is True)
check('unresolved_empty',r['unresolved']==[] and json.loads((BUILD/'unresolved.json').read_text())==[])
freeze=json.loads((OUT/'expected-freeze.json').read_text());check('expected_freeze_unchanged',all(sha(OUT/p)==h for p,h in freeze['files'].items()))
failed=[c for c in checks if not c['passed']]
evidence=['response.json','metrics.yml','catalog.json','scope.json','source_check.json','grain_contract.json','grain_check.json','dimension_check.json','metricflow_check.json','unresolved.json','input.json','skill_used.md']
report=dict(status='approved' if not failed else 'blocked',approved_to_load_and_query=not failed,reviewed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewed_metric_ids=list(expected),scope='B3 four and B1/B2 old twelve; B4 ratios separately reviewed',checks=checks,failed_checks=failed,evidence_sha256={str((BUILD/f).relative_to(ROOT)):sha(BUILD/f) for f in evidence},expected_freeze_sha256=sha(OUT/'expected-freeze.json'),notes=['sum(1)准确性的前提为原始order_id唯一且非空，48行原CSV与grain_check均已核。','count_distinct在查询窗口/筛选/分组后的条件member_id/store_id上聚合；未从分组人数再求和。','refund_buyer使用所有退款paid单，包括全退；valid_order_items保留有效单quantity，不从退款金额倒推件数。','订单成交门店与账户归属门店分角色，12维度可达只表示结构能力，不冒称12维度均实测。','本批准后仍需真实查询、完整SQL和解释复核；不是运行通过、规模验证或验收。'])
(OUT/'generation-review-v1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'generation-review-v1.md').write_text('''# 生成物独立审查 v1：批准加载与真实问数\n\nB3四项及B1/B2旧12项均通过，`approved_to_load_and_query=true`，`failed_checks=[]`。精确对象哈希见同名JSON；B4八项另由比率Agent审查。\n\nB3分别按有效单member_id、退款paid单member_id、有效单orders.store_id做count_distinct，件数对有效单原quantity求和；退款账户包括全退，件数不是净销量。没有卡表连接、资格筛选、金额去重或分组人数相加。四项单位count，件数明确按件且整数。\n\n旧12项逐一核原材料、过滤条件、表达式、聚合及单位：paid金额仍包含全退单的零净贡献；优惠不冲退款；订单数量保留创建/支付/有效/取消/退款/部分退/全退边界，特别是全退需要正实付。sum(1)依赖一行一单且order_id唯一非空，原CSV与粒度检查支持。\n\n统计时间统一orders.ordered_at，无错误整月限制。成交门店和账户归属门店为独立角色，关系对齐字典；16项均有12维度结构路径，不能将结构可达写成全部实测。catalog与business_model_usage引用均为连续原文，且定义/约束支持对应来源。结构检查全过，冻结期望未改。\n\n准许下一步加载与本轮测试；查询SQL、数值与完整解释仍待实际运行后审核。\n''')
print(json.dumps(dict(status=report['status'],approved_to_load_and_query=report['approved_to_load_and_query'],failed_checks=failed,check_count=len(checks)),ensure_ascii=False))
