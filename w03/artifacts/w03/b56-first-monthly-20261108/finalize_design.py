"""Record approved test preparation; never mark unexecuted metric queries as passed."""
import hashlib
import json
from pathlib import Path

B=Path(__file__).resolve().parent
ROOT=B.parents[2]
REL=B.relative_to(ROOT).as_posix()
rd=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

review=rd(B/'design-review/final-review-v2.json')
assert review['approved_for_build_preparation'] and not review['failed_checks']
assert not (B/'design-completion.json').exists()
for p,h in review['evidence_sha256'].items():assert sha(ROOT/p)==h,p
guard=rd(B/'protected.json')
for p,h in guard.items():assert sha(ROOT/p)==h,p
f5=rd(B/'independent-b5/expected-freeze.json')
for p,h in f5['source_files'].items():assert sha(ROOT/p)==h,p
for v in f5['data_sources'].values():
    for p,h in v['files'].items():assert sha(ROOT/p)==h,p
for p,h in f5['artifacts'].items():assert sha(B/'independent-b5'/p)==h,p
f6=rd(B/'independent-b6-v2/expected-freeze.json')
for field in ['inputs_sha256','artifacts_sha256']:
    for p,h in f6[field].items():assert sha(ROOT/p)==h,p
designs={}
tests=[]
for sub,field in [('independent-b5','designs'),('independent-b6-v2','cases')]:
    d=rd(B/sub/'design.json')
    for c in d[field]:designs[c['id']]=(sub,c)
    for f in ['tests-small.json','tests-fixture.json']:
        for c in rd(B/sub/f):tests.append((sub,f,c))
assert len(tests)==13 and len({c['id'] for _,_,c in tests})==13 and len(designs)==14
assert set(review['reviewed_case_ids'])=={c['id'] for _,_,c in tests}
assert set(review['reviewed_design_ids'])==set(designs)
small=rd(B/'tests-new-small-v2.json');old=rd(B/'tests-regression-small.json')
assert len(small)==10 and len(old)==33
assert old==rd(ROOT/'customer/w03/tests.json')==rd(B/'before/customer/w03/tests.json')
assert rd(B/'tests-small-all-planned-v2.json')==small+old
table={c['id']:c for _,_,c in tests}
review_ref=f'{REL}/design-review/final-review-v2.json'

# Formal runtime tests stay at the previous 33 cases. New candidates remain in this artifact.
regpath=ROOT/'customer/w03/metric_register.json';reg=rd(regpath)
reg['version']='w03-metric-register-v5';reg['updated_at']='2026-11-08'
reg['next_pair_design_review']=review_ref
for batch in reg['batches']:
    if batch['id'] in ['B5','B6']:
        batch.update(status='design_reviewed_expected_frozen_not_built',design_reference=f'{REL}/'+('independent-b5' if batch['id']=='B5' else 'independent-b6-v2')+'/design.json',design_review_reference=review_ref)
for m in reg['metrics']:
    if m['batch'] not in ['B5','B6']:continue
    m['before_B56_design_reference']=f'{REL}/before/customer/w03/metric_register.json#{m["id"]}'
    sub='independent-b5' if m['batch']=='B5' else 'independent-b6-v2'
    ids=[c['id'] for s,_,c in tests if s==sub and (m['id'] in c['expected'].get('intent',{}).get('metrics',[]) or c['expected']['status']!='ok')]
    m.update(definition_status='本轮字段/粒度/规则来源已核；尚未核生成实现',
             test_design_status='候选测试及独立期望已通过独立Agent设计审核',
             expected_status='原CSV或明确人工样本独立核算已冻结，运行版本待加载绑定',
             candidate_test_case_ids=ids,expected_reference=f'{REL}/{sub}/expected-freeze.json',
             design_reference=f'{REL}/{sub}/design.json',design_review_reference=review_ref,
             known_pending='32项候选生成、实际维度可达、版本绑定、真实数值及解释核对、规模回归；无新增业务决策')
    assert m['build_status']=='未构建' and m['small_status']=='未运行' and m['explanation_status']=='未审'
reg['summary'].update(next_pair='B5+B6',next_pair_design_metrics=8,next_pair_design_entries=14,
    next_pair_unique_candidate_questions=13,next_pair_small_candidates=10,next_pair_new_fixture_candidates=3,
    metrics_with_frozen_design_expected=32,next_pair_native_build_calls=0,next_pair_native_queries=0,
    next_pair_execution_state='not_run',next_pair_design_reference=review_ref)
assert reg['summary']['metrics_with_small_pass']==24
save(regpath,reg)
planpath=ROOT/'customer/w03/test-plans/metric_cases.json';plan=rd(planpath)
plan['version']='w03-metric-test-plan-v7'
plan['next_pair_preparation']={'batches':['B5','B6'],'review':review_ref,'design_entries':14,'unique_questions':13,'small':10,'new_fixture':3,'actual_execution':'not_run'}
for c in plan['cases']:
    if c['id'] not in designs:continue
    sub,d=designs[c['id']];ids=d.get('candidate_ids',d.get('native_case_ids'))
    c.update(before_B56_design_reference=f'{REL}/before/customer/w03/test-plans/metric_cases.json#{c["id"]}',
             state='independent_design_reviewed_not_run',executable=False,prepared_for_execution=True,
             expected_state='independent_expected_frozen_reviewed',execution_state='not_run',
             candidate_case_ids=ids,candidate_questions=[table[i]['question'] for i in ids],
             design_reference=f'{REL}/{sub}/design.json#{c["id"]}',expected_reference=f'{REL}/{sub}/expected-freeze.json',
             design_review_reference=review_ref,coverage_limits=d.get('gaps',[]))
    if c['id']=='B5-D01':c['design_revision']='注册分组由无注册的8月改到有12个注册账户的7月；保留原问法于before与作者original-designs.json。'
assert len(plan['cases'])==64
assert sum(bool(c.get('executable')) for c in plan['cases'])==34
save(planpath,plan)

brief={
 'B5-N01':'注册0；观测期首购5；首单净额12800分；首单5；后续订单22；有效单27。复用核5+22=27。',
 'B5-D01':'归属店×当前等级四组：S01普通4/金卡2；S02普通4/金卡2。含未有效购买的注册账户。',
 'B5-Z01':'五项均0；用于覆盖内空窗。单独不能证明注册与订单日期不同，由人工例补。',
 'B5-H03':'M00005：首购0/首单净额0/首单0/后续1/有效1；M00007：1/3000分/1/0/1。',
 'B5-H02-F':'首购1、首单净额137分、首单1、后续1、有效2；要按订单号选对同日首单。',
 'B5-Z01-F':'注册2，其余四项0；不能因无订单把注册也算0。',
 'B6-N01':'购买账户15、复购账户12、复购率0.8（80%）；分母不是20个注册账户。',
 'B6-M01':'7月11/1/1÷11；8月15/12/0.8。各月单列，不跨月加人数或平均比率。',
 'B6-Z01':'购买0、复购0、复购率null（未定义）；5月在覆盖内。',
 'B6-R01':'购买3、复购1、复购率1/3；三有效单仍只计一个复购账户；一有效单加全退/取消不凑复购，多卡不放大。',
 'B6-X01':'unsupported：普通月内指标只支持完整自然月，不擅自扩月。',
 'B6-X02':'unsupported：材料中的普通月内口径要求全门店。',
 'B6-X03':'unsupported：当前工具契约限制全渠道；不能说03业务原文禁止渠道分析。',
}
lines=['# B5＋B6 测试设计与独立期望','',
 '2026-11-08；导师与独立测试Agent准备，另一独立Agent审核。**设计审核通过，尚未构建或真实问数。** 当前实测进度仍为24/38项，不能因为本轮准备了8项就写32项已通过。','',
 '本轮14条设计要求映射到13道候选问题：原small10题、两套独立人工数据共3题。H01与A01复用现有候选，辅助等式不是额外问数。7月有注册记录，因此把原D01的8月分组改到7月，提高区分力。B6第二版在同一人工题补第三笔有效单，区分“至少2次”和“恰好2次”；原首版及审核记录保留。','',
 '## 来源与计算规则','',
 '- [会员运营周报](../../materials/w03/03_会员运营周报.md)：注册按registered_at；首购先在全部测试覆盖期内找每个账户第一笔有效订单，再筛窗口；同日按order_id排序；后续是第二笔以后有效订单，按单数计。','- [订单日报](../../materials/w03/01_订单日报说明.md)：有效订单为paid且实付减累计退款大于0，取消和全退不计。','- [字典](../../materials/w03/05_数据字典.md)与[业务模型](business_model.md)：一行一个CRM账户/订单；账户不等于自然人，成交店与归属店分开，当前等级不冒称历史等级；与本轮无关的多卡资格不加入筛选。','- [工具契约](contract.md)：半开日期、月分组与全渠道限制、零分母null。未来加载后再绑定真实数据/库hash；没有预填不存在的运行版本。','',
 '## 所有候选问题','',
 '下方是**独立预期**，不是已得到的系统回答。人工数据在单独项目运行，与原small和旧B2人工数据分别保存。','']
for batch in ['B5','B6']:
    lines += ['### '+batch+(' 注册、观测期首购与后续订单' if batch=='B5' else ' 普通月内购买与复购'),'']
    for sub,file,c in tests:
        if not c['id'].startswith(batch):continue
        kind='原small合成测试集' if file=='tests-small.json' else '单独人工样本'
        lines += [f'**{c["id"]}｜{kind}**',c['question'],'',f'独立期望与检查点：{brief[c["id"]]}','']
lines += ['## 怎样复核与继续','',
 f'两位作者分别从原CSV/人工样本逐单核算，保存账户、订单、注册或账户月份台账；审核Agent先独立形成判据，再复算并检查候选。见[独立设计终审](../../{REL}/design-review/final-review-v2.md)、[B5明细](../../{REL}/independent-b5/summary.md)、[B6明细](../../{REL}/independent-b6-v2/summary.md)。判定副本自检仅证明比较逻辑能识别特定错误，不是指标运行通过。','',
 '后续累计构建32项，检查派生排序/账户月汇总与维度、加载并绑定版本，再运行原small43题（新增10＋原33）、新人工3题与旧人工1题，合计47题。各数据集分别留原生报告，两批统一汇报。B3-U01退款范围与B1-Z01日期原解释缺陷继续原题回归，导师修订稿不能替代产品原生结果。','',
 '本轮没有新业务取舍需要本人裁决。本人需要掌握的判断是：为什么不能在8月窗口内重新找首单，以及为什么22笔后续订单不等于12个当月复购账户。此处为导师说明，不记录本人已独立答对。','',
 '覆盖限制：未穷举全部维度/渠道/卡组合；B5只验证所列账户筛选，不凭此推定任意筛选与排序关系；B6未另测跨月合计请求的拒绝措辞，也未覆盖零业务月份按月分组补行。规模回归、B7六项付费月报与提交仍在后续。','']
(ROOT/'docs/w03/B5-B6-测试设计.md').write_text('\n'.join(lines))

# Existing registers remain the main entry points; prepend a short current design stop.
current='**B5＋B6测试设计已就绪（2026-11-08）：** 8项新指标的14条设计要求已映射13道候选（原small10＋新人工3），独立期望冻结并通过独立设计审核。本轮未构建、未真实问数；实测仍24/38，原解释32/34与两份已审纠正稿保留。下一步累计构建32项，加载后绑定版本并运行计划47题（含原33＋旧人工1回归），数值与完整解释分别审核。\n\n'
for name,link in [('AGENTS.md','docs/w03/B5-B6-测试设计.md'),('开始这里.md','docs/w03/B5-B6-测试设计.md'),('../W03-学习会话接续.md','实操工程/docs/w03/B5-B6-测试设计.md'),('docs/w03/test_design.md','B5-B6-测试设计.md')]:
    p=ROOT/name;title,rest=p.read_text().split('\n',1)
    p.write_text(title+'\n\n'+current+f'[问题、独立期望与检查方法]({link})。以下保留上轮执行证据和历史记录。\n'+rest)
p=ROOT/'docs/w03/指标核对与测试登记.md';text=p.read_text()
needle='## 分批顺序'
text=text.replace(needle,'B5＋B6新增8项的测试设计已独立审核：13道候选、期望冻结；尚未构建或执行。[查看全部问题与预期](B5-B6-测试设计.md)。\n\n'+needle,1)
text=text.replace('下一轮与B6合并，累计32项','设计/期望已审；与B6合并构建32项待执行').replace('下一轮与B5合并，累计32项','设计/期望已审；与B5合并构建32项待执行')
for m in reg['metrics']:
    if m['batch'] not in ['B5','B6']:continue
    prefix='| '+m['name']+' `'+m['id']+'`'
    text='\n'.join((f'{prefix} | 03/05、01及契约 | 来源/字段已核 | 未构建 | 独立期望已审冻结 | 未跑/未审回答 | 未跑 |' if line.startswith(prefix) else line) for line in text.splitlines())+'\n'
p.write_text(text)
p=ROOT/'docs/w03/指标模型测试集设计.md';text=p.read_text();title,rest=text.split('\n',1)
text=title+'\n\nB5＋B6本轮准备：14条设计映射13候选，独立期望已审冻结，实际未执行。完整问题及映射见[B5—B6设计](B5-B6-测试设计.md)。原64条设计记录保留；B7的12条设计仍待细化期望。\n'+rest
for batch,endbatch,desc in [('B5','B6','7设计→6候选（原small4＋人工2），H01/A01复用；D01改7月注册分组，Z01增加人工注册非零/订单零例。'),('B6','B7','7设计→7候选（原small6＋人工1）；5月零购买期望0/0/null；半月、门店、渠道三条为unsupported，来源分别记录。')]:
    a=text.index('## '+batch+' ·');z=text.index('## '+endbatch+' ·');part=text[a:z]
    oldintro=next(l for l in part.splitlines() if l.startswith('本批指标：'))
    part=part.replace(oldintro,desc+' 独立设计审核通过、期望已冻结；真实执行未开始。下表原设计简写保留，最终独立完整问句及数值见链接。')
    text=text[:a]+part+text[z:]
p.write_text(text)
p=ROOT/'../W03-学习笔记.md';title,rest=p.read_text().split('\n',1)
p.write_text(title+'\n\n## 2026-11-08 测试设计速记：先找首单，再筛窗口\n\n含义：观测期首单是账户在全部测试覆盖期内的第一笔有效订单，月内复购则重新按每个自然月数有效订单。例：原small的M00005在7月31日及8月20日各买一单；8月有1笔观测期后续订单，但8月并未达到月内两单复购。\n\n易混点：不能先截8月再找首次；后续订单数不是复购账户数。用法：先保留全覆盖订单和首单身份，再按问题窗口核各项；比较日期、单位、数字后另审完整解释。记忆要求：能说明排序与筛选顺序、订单与账户粒度差别；本轮为导师示范，不记录本人已独立掌握。\n\n来源：01订单日报、03会员运营周报、原small订单及[本轮设计](实操工程/docs/w03/B5-B6-测试设计.md)。设计13题已独立审，指标尚未构建执行；实测进度仍24/38。\n'+rest)
planexec=rd(B/'execution-plan.json');planexec['course_small']['new_cases']=10;planexec['course_small']['new_candidate_file']=f'{REL}/tests-new-small-v2.json';planexec['course_small']['all_candidate_file']=f'{REL}/tests-small-all-planned-v2.json';planexec['approved_b6_source']='independent-b6-v2';planexec['planned_total_questions']=47;planexec['planned_new_questions']=13;planexec['design_review']=review_ref;save(B/'execution-plan.json',planexec)
completion={'status':'design_reviewed_expected_frozen_not_executed','batches':['B5','B6'],'metrics':8,'design_entries':14,'candidate_questions':13,'new_small':10,'new_fixture':3,'formal_small_tests_unchanged':33,'old_fixture_tests_unchanged':1,'future_total':47,'metrics_actually_passed_small':24,'native_build_calls':0,'native_queries':0,'review':review_ref,'human_document':'docs/w03/B5-B6-测试设计.md','business_decisions_pending':[],'next':'累计32项构建/生成物独立审查/加载绑定/47题真实测试','attribution':'导师与独立Agent设计/审核；不登记本人独立作答、实际问数通过、客户验收或提交'}
save(B/'design-completion.json',completion)
save(B/'progress.json',completion)
print(json.dumps(completion,ensure_ascii=False))
