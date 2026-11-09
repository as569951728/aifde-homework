"""Reflect completed numerical validation and separately reviewed answer corrections."""
import json
from pathlib import Path

B=Path(__file__).resolve().parent
ROOT=B.parents[2]
REL=B.relative_to(ROOT).as_posix()
completion=json.loads((B/'completion.json').read_text())
assert completion['small_passed']==33 and completion['reviewed_corrections_passed']==2
reg=json.loads((ROOT/'customer/w03/metric_register.json').read_text())
new=json.loads((B/'test-new-v1/metric_test_report.json').read_text())
normal=[c for c in new['cases'] if c['id'] in ['B3-N01','B4-N01']]
names={m['id']:m['name'] for m in reg['metrics']}
rows=[]
for c in normal:
    a=c['actual']
    for mid,val in zip(a['columns'],a['rows'][0]):
        unit=a['units'][mid]
        if unit=='ratio':display=f'{100*val:.4f}%'
        elif unit=='cents_per_order':display=f'{val/100:.2f}元/单'
        elif unit=='cents_per_member':display=f'{val/100:.2f}元/账户'
        elif unit=='orders_per_member':display=f'{val:.4f}单/账户'
        elif unit=='items_per_order':display=f'{val:.4f}件/单'
        else:display=f'{val}'+('家' if mid=='selling_store_count' else '件' if mid=='valid_order_items' else '个账户')
        rows.append(f'| {names[mid]} | {val} {unit} | {display} | 与独立期望一致 |')
result='''# B3+B4 两批结果速览

2026-11-08；导师执行、两个独立Agent分工核算和审核。

本轮新增12项，累计 **24/38项（约63%）完成小样本数值核对**。累计24项库一次生成，新增12题＋原21题回归＝课程small33/33；另用原B2人工数据回归1/1。两份small原生报告分别保留；合并报告只是索引，没有新增问数。

**解释单列：原生32/34通过。** B3-U01把退款会员误说成只来自有效订单；B1-Z01把不含6月30日的终点误说成包含当日。两条原失败保留，导师另存纠正稿，经独立复审2/2通过。查询SQL和数值正确，自动解释链路尚未修复，不能记成34份原生回答全部通过。

## 本轮产物样子：2026年8月、全渠道全门店

以下是课程合成测试数据结果，不是青禾生产经营统计。

| 指标 | 原始值及单位 | 展示值 | 核对 |
| --- | --- | --- | --- |
'''+ '\n'.join(rows)+'''

## 怎么检查

- 先看独立原CSV账户集合、订单件数及比率分子分母，再对实际查询的条件、分组、每个数值和单位；32条成功SQL与2条非成功原因分别审阅。
- 购买账户按有效单去重；退款账户按发生退款的paid订单去重，含全退；成交门店按有效订单店去重；件数用原quantity，不猜退款件数。多卡不参与这些指标。
- 8项均值/比率均先聚合各自分子分母再除；零分母为未定义。7月店比率不能无权平均成总体，原数据8项中7项能区分该错误，优惠率全为0不能区分。
- 原数据分别覆盖多单、多卡、重复退款和同额不同账户；未证明同一账户同时多卡且重复退款的组合。7月单月分店人数无重叠，非加性另查7—8月账户集合，不能夸成所有组合已测。

## 证据入口

- [口径与来源](口径与本轮检查.md)；[新增12题原生报告](test-new-v1/metric_test_report.json)；[原21题回归](test-regression-v1/metric_test_report.json)；[人工边界回归](test-fixture-v1/metric_test_report.json)。
- [B3及原题首轮审核（含两条失败）](independent-b3/query-review-v1.md)；[两条审校副本复审](independent-b3/reviewed-corrections-v1.md)；[B4最终审核](independent-b4/final-review-v1.md)。
- [B3-U01纠正稿](mentor-corrections/B3-U01.md)；[B1-Z01纠正稿](mentor-corrections/B1-Z01.md)。纠正稿不覆盖原回答、分数或查询。
- [通用13项判定控制](judge-injections-v1.json)、[B3去重与扇出4项控制](b3-result-controls.json)和B4实际副本控制（见B4审核）检验错误能否被拦，均不新增模型或数据库调用。
- [版本、调用与保护核对](execution-audit.json)；[完成状态](completion.json)。Skill v0.1.2、配置、判定器、业务模型、W02基线与课程数据未改。

## 下一轮

按本人要求继续 **B5注册/观测期首购5项＋B6普通月内购买与复购3项**，累计32项。先独立冻结两批期望，再构建和回归；两批统一汇报。B7付费月报6项、全库/其他维度/规模回归与提交仍未完成，规模0/38。两条自动解释缺陷留在账中，后续回归继续检查，不能用本次审校稿证明系统已修好。
'''
(B/'结果速览.md').write_text(result)

p=ROOT/'docs/w03/指标核对与测试登记.md';text=p.read_text()
text=text.replace('当前推进单位改为**一个指标批次**。每批先核口径与测试，再构建、核数和审解释；仅真实业务取舍交本人，常规修复由导师和独立Agent处理。','当前推进单位为**每轮两批**：并行准备期望与独立审核，累计构建，新增/回归分报告并行；两批统一汇报。仅真实业务取舍交本人。')
old=next(l for l in text.splitlines() if l.startswith('当前：**'))
text=text.replace(old,f'当前：**B1—B4累计24/38项（约63%）通过小样本数值核对；余14项，规模0/38。** small33/33＋原人工边界1/1。原生解释32/34，两条导师审校副本独立通过；自动解释管线未修。[本轮结果](../../{REL}/结果速览.md)。',1)
text=text.replace('本批新增空窗例另经独立预审；当前B1+B2执行证据见上方结果。','B3/B4分别独立冻结并审核；本轮首轮解释失败与审校稿分开留证，见上方结果。')
lines=text.splitlines()
for i,line in enumerate(lines):
    for batch in reg['batches']:
        if line.startswith('| '+batch['id']+' |'):
            state={'B1':'数值回归通过；空窗题解释另有审校稿','B2':'数值、原生解释及人工边界回归通过','B3':'6题数值通过；1份解释另有审校稿','B4':'6题数值及原生解释通过','B5':'下一轮与B6合并，累计32项','B6':'下一轮与B5合并，累计32项','B7':'后续付费月报；再做全库/规模核对'}[batch['id']]
            lines[i]=f'| {batch["id"]} | {batch["name"]} | {len(batch["new_scope_metric_ids"])} | {state} |'
    for m in reg['metrics']:
        if m['batch'] in ['B1','B2','B3','B4'] and line.startswith('| '+m['name']+' `'):
            state={'B1':'数值回归通过；空窗解释另有审校稿','B2':'small及人工回归通过；解释已审','B3':'6题数值通过；1份解释另有审校稿','B4':'6题数值、完整解释通过'}[m['batch']]
            lines[i]=f'| {m["name"]} `{m["id"]}` | '+('02/05' if m['batch']=='B4' else '01/05')+f' | 已核 | B34累计库v1 | 独立期望已冻结 | {state} | 未跑 |'
text='\n'.join(lines)+'\n'
text=text.replace('B1/B2已提升为原生测试，fixture另存；其余新期望未计算','B1—B4已提升为原生数值测试，fixture另存；B5—B7期望待冻结')
text=text.replace('[当前small原生21例（含未改的原15例）]','[当前small原生33例（含未改的原21例）]')
p.write_text(text)

p=ROOT/'docs/w03/指标模型测试集设计.md';text=p.read_text()
start=text.index('更新：2026-11-08。');end=text.index('## 先看一条新增测试长什么样')
text=text[:start]+f'''更新：2026-11-08。现有56条新增设计条目＋原净额8条＝64条。新增56条中26条已真实问数、2条辅助关系、1条复用回答审查、1条已拆分父项、26条待执行。B4-D01拆成门店/整体两题；U01复用回答审查，不另计问数。

**每轮两批推进。** 当前small33题＋原人工fixture1题数值通过；原生解释32/34，两条独立复审的导师纠正稿另存，不改原分。B1-A01/B2-A01为辅助关系。尚未执行的26条设计须继续独立核算；不把参数化设计当成已执行多个子例。[本轮证据](../../{REL}/结果速览.md)。

'''+text[end:]
for batch,next_batch,intro in [
 ('B3','B4','四项指标共6道原small题，数值及SQL通过；原生解释5/6，U01退款账户错句另有独立审过的导师纠正稿。U01使用7—8月课程数据，分别验证多单、多卡及重复退款，不是新增人工fixture；同账户多卡且重复退款的组合未覆盖。'),
 ('B4','B5','八项指标共6道原small题及完整解释通过；D01已拆为D01-store和D01-all两道独立查询；U01复用这6份回答检查单位与百分数，不新增问数。7月优惠率全零，对无权平均错误无区分力，其余7项可区分。')]:
    start=text.index('## '+batch+' ·');end=text.index('## '+next_batch+' ·');section=text[start:end]
    old=next(l for l in section.splitlines() if l.startswith('本批指标：'))
    section=section.replace(old,intro)
    if batch=='B3':
        section=section.replace('隔离边界例：一个账户多次有效购买、多次退款并持多卡；另一个账户的订单金额相同。','实际U01查7—8月四项；原数据分别覆盖多卡多单、重复退款及同额不同账户，组合覆盖边界见上文。')
    text=text[:start]+section+text[end:]
text=text.replace('[原生15题]','[当前small原生33题]')
text=text.replace('每批至少正常多指标用例','每轮两批分别至少有正常多指标用例').replace('同批通过后一次汇报，不逐指标等待确认。','两批核完统一汇报，不逐指标或两批之间等待确认。')
p.write_text(text)

current='''**B3+B4两批已推进（2026-11-08，当前）：** 累计24/38项（约63%）完成小样本数值核对；新增12题＋原21题回归small33/33，另原人工边界1/1。原生解释32/34，B3-U01退款范围和B1-Z01日期错句保留原失败；两份导师审校副本独立通过。自动解释链路未修，不记作原生全通过。Skill、配置、judge、课程数据、W02和业务模型未改。规模0/38。

**下一轮：B5五项＋B6三项一起推进，累计32项。** 继续独立冻结、构建和回归，两批统一汇报；B7六项及全库/规模后续。无新增业务裁决。导师执行和审校不等于本人独立掌握、客户验收或正式提交。

'''
for name,prefix in [('AGENTS.md',''),('开始这里.md',''),('docs/w03/test_design.md','../../'),('../W03-学习会话接续.md','实操工程/')]:
    p=ROOT/name;text=p.read_text();title,rest=text.split('\n',1)
    rest=rest.replace('**B2订单数量批次完成（2026-11-08，当前）：**','**B2订单数量批次完成（2026-11-08，历史）：**',1)
    if name=='AGENTS.md':
        rest='\n'.join(l for l in rest.splitlines() if not l.startswith('**2026-11-08 最新推进方式：'))
    p.write_text(title+'\n\n'+current+f'[本轮结果]({prefix}{REL}/结果速览.md)。以下按发生时点保留历史记录。\n'+rest)
p=ROOT/'docs/w03/metric_decisions.md';title,rest=p.read_text().split('\n',1)
p.write_text(title+'\n\n## B3+B4口径核定（2026-11-08，当前）\n\n购买账户、成交店及原商品件数取有效单；退款账户取paid且退款>0（含全退）；账户/店去重，quantity相加。比率各自汇总分子分母再除，零分母null；退款原订单日，全部按各自量纲，不按多卡放大。\n\n'+f'24项数值已核；原生解释32/34，2条另有独立审校稿，自动解释未修。[来源及边界](../../{REL}/口径与本轮检查.md)，[结果](../../{REL}/结果速览.md)。下一轮B5+B6，以下为历史记录。\n'+rest)
p=ROOT/'../W03-学习笔记.md';title,rest=p.read_text().split('\n',1)
p.write_text(title+'\n\n## 2026-11-08 实操概念速记：去重与比率\n\n含义：账户数量按账户集合计，比率先累计分子分母再除。例：合成测试8月27笔有效订单、15个购买账户，频次27÷15＝1.8单/账户；100300分÷27≈37.15元/单。退款账户含全退，不能沿用购买账户的有效单条件。\n\n易混点：去重人数不能直接相加，门店平均值不能无权再平均；零分母为未定义。用法：先列每项入选集合及分子分母，独立算值后比较实际条件、值和完整回答。记忆要求：能说明上述差别，本轮不登记本人独立掌握。\n\n'+f'来源：01日报、02财务、05字典与[B3+B4实际证据](实操工程/{REL}/结果速览.md)。24/38项数值通过；原解释32/34、2份审校稿通过，管线未修。每轮两批，下一轮B5+B6。以下为历史记录。\n'+rest)
print('Updated existing documents; original failures and historical baselines retained.')
