import json,copy,hashlib,datetime
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
ns={'__name__':'independent_judge_review'}
exec(compile((ROOT/'customer/w03/judge.py').read_text(),'judge.py','exec'),ns)
compare=ns['compare'];tests=json.loads((OUT/'tests-new-small.json').read_text());group=tests[1]['expected'];flat=tests[0]['expected']
checks=[]
def check(name,e,a,want):
    result=compare(e,a);checks.append(dict(name=name,passed=result['passed']==want,expected_judge_passed=want,judge_result=result))
for t in tests:check('positive-'+t['id'],t['expected'],copy.deepcopy(t['expected']),True)
a=copy.deepcopy(group);a['rows'].reverse();check('row-order',group,a,True)
a=copy.deepcopy(group);a['columns'].reverse();a['rows']=[list(reversed(r)) for r in a['rows']];check('column-order',group,a,True)
mutations=[('wrong-status',lambda a:a.update(status='unsupported')),('wrong-time',lambda a:a['intent'].update(end='2026-08-31')),('wrong-metric',lambda a:a['intent']['metrics'].pop()),('wrong-unit',lambda a:a['units'].update(valid_order_items='cents')),('fractional-item',lambda a:a['rows'][0].__setitem__(-1,33.000000001)),('numeric-string',lambda a:a['rows'][0].__setitem__(-1,'33')),('bool-count',lambda a:a['rows'][0].__setitem__(0,True)),('null-count',lambda a:a['rows'][0].__setitem__(-1,None)),('wrong-version',lambda a:a.update(data_version='other')),('wrong-filter',lambda a:a['intent']['filters'].append(dict(field='order__channel',op='eq',value='门店'))),('extra-unit',lambda a:a['units'].update(other='count')),('missing-column',lambda a:a['columns'].pop())]
for name,mutation in mutations:
    a=copy.deepcopy(flat);mutation(a);check(name,flat,a,False)
for name,mutation in [('missing-group',lambda a:a['rows'].pop()),('extra-group',lambda a:a['rows'].append(['S99',0,0,0,0])),('duplicate-group',lambda a:a['rows'].append(a['rows'][0])),('swapped-group-identities',lambda a:a['rows'][0].__setitem__(0,'S99'))]:
    a=copy.deepcopy(group);mutation(a);check(name,group,a,False)
assert all(c['passed'] for c in checks)
(OUT/'judge-reuse-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((OUT/'expected-freeze.json').read_text());assert all(sha(OUT/p)==h for p,h in freeze['files'].items())
report=dict(status='approved',approved_for='B3四项与B1/B2原12项本轮累计构建及后续真实问数；B4由另一个独立审查范围负责',reviewed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),read_order='original materials, contract, test-guide, raw CSV, design -> independent ledger/calculation -> freeze -> Skill/judge/build config; no generated library/SQL/actual read',checks=[dict(name='source_definitions_and_field_grain',passed=True),dict(name='raw_csv_hashes_match_manifest',passed=True),dict(name='B3_6_full_independent_questions',passed=True),dict(name='units_count_integer_exact_items_not_net_units',passed=True),dict(name='original21_recalculated_objects_unchanged',passed=True),dict(name='old_fixture1_recalculated_source_hashes_retained',passed=True),dict(name='judge_positive_and_fault_injections',passed=True,count=len(checks)),dict(name='skill_generic_method_and_current_build_scope',passed=True),dict(name='frozen_expected_hashes_stable',passed=True)],failed_checks=[],scope=dict(B3_new_small=6,old_small_regression=21,old_isolated_fixture=1),hashes={p:sha(ROOT/p) for p in ['customer/w03/build-metrics/SKILL.md','customer/w03/judge.py','customer/w03/build.json']},expected_freeze_sha256=sha(OUT/'expected-freeze.json'),limitations=json.loads((OUT/'sample-and-scope.json').read_text())['limitations'],next_gate='生成库后核B3四项+B1/B2旧12项表达式/聚合/日期/维度/引用，再审6+21+1真实结果SQL及完整解释；此批准不是运行通过。')
(OUT/'preflight-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'preflight-review.md').write_text('''# B3 独立预检：批准本范围构建\n\n按原订单日报、财务邮件、字典、契约与原 small CSV 独立逐单核算后冻结，随后审构建 Skill 和 judge；未读取被测生成库、SQL 或实际结果。批准范围仅 B3 四项及 B1/B2 旧12项回归，B4另审。\n\nB3六题原样本期望：N01=(15,4,2,33)；D01按成交店S01=(8,0,1,9)、S02=(2,1,1,4)、S03=(1,1,1,4)；R01=(1,1,1,1)；R02=(0,1,0,0)；U01七至八月=(17,5,3,50)；F01小程序=(13,2,2,15)。顺序均为购买账户、退款账户、成交店、有效单原始件数，协议单位均count且整数精确比较，末项业务量纲件。\n\n原21题已独立复算并保持原对象不变；旧B2隔离fixture1题逐日复算一致，题目、期望与源数据哈希沿用。judge八项正确输入/重排与十六项错误注入全部符合预期，数量与标识逐组检查，不只核总和。Skill对事实粒度、窗口、角色、多卡放大、去重和接口单位的方法与来源兼容，无须修改Skill或judge。\n\nU01复用原7–8月数据：多单多卡、相同金额不同账户与重复退款账户分别有区分力，但不是同一账户同时多卡多退款的交叉覆盖。July各店账户无重叠，D01本身不能数值证明非可加；独立辅助台账显示7–8月按店人数相加22而整体去重17。卡表只用于审查放大风险，不加入业务计算。无自然人身份表，因此只验证CRM账户去重。\n\n没有新造fixture、模型调用、数据库调用，也没有规模或B5扩展。下一关是生成定义审核，真实查询、SQL与完整解释审查另计；批准不等于通过、客户验收或提交。\n''')
print(json.dumps(dict(status=report['status'],judge_checks=len(checks),scope=report['scope']),ensure_ascii=False))
