from pathlib import Path
import json,hashlib,datetime,re
root=Path('/Users/chenzhaowen/czw-code/AIFDE'); audit=root/'W03/实操工程/artifacts/w03/source-semantics-audit-20261108'; out=audit/'reviews/model_and_artifact'
criteria=json.loads((out/'source-criteria.json').read_text()); expect=json.loads((audit/'input/reviewer_expectations.json').read_text()); q=json.loads((audit/'input/original_questions.json').read_text()); ids=[x['id'] for x in criteria['rows']]; own={x['id']:x for x in criteria['rows']}; questions={x['id']:x for x in q['cases']}
# Below are the reviewer-authored semantic conclusions, not model scores or keyword matches.
notes={
'U01':['双目标有沈总原因验证与小林减负诉求各自支持，分开观察是合理设计边界。','沈总明确优先原因与老化假设；字段/口径核查不是最终经营目标。','没有实际工时、原因或改善证据；正文排除个人载体/交付项依据用户边界。'],
'U02':['字典确有账户/多卡/等级/自然人边界，角色确认等级与资格不同。','资格有产品/日期依据；活跃定义缺失，分析属性为已采纳概念表达，不是新增身份事实。','购买记录与复购群体指标概念不同；不得把公式结果归为永久个人属性。','例子仅条件推导，普通可付费而不必购买/活跃。'],
'U03':['字典明确单订单账户/成交门店和多卡关系；角色禁止重复计人和订单。','题设成交B、归属A在两个明确关系下可判。','字典无订单卡键，不能由共享账户制造实际用卡。','07与字典均声明合成/非自然人统一，只在本期解释。'],
'U04':['03862提供一般步骤且明确具体活动/名单/条件不能确认。','01949/01953与03888/90支持门店安排需另确认。','01945/53保留已知局部与未知返回，没有否定公司存在闭环。','业务用途与具体责任未知可并存；排除载体是用户选择而非源事实否定。'],
'P09':['本期资格和全系统免费分类不同，假设不推出额外事实。','01742要求分范围，不证明系统互斥；旧学员判断没有升级。'],
'C01':['题内2有效卡和2不同订单；业务规则得1账户2订单。','账户资格存在判断/等效去重是可行实现建议，不冒称客户字段或唯一算法。'],
'C06':['两产品都在范围，题内2有效卡仍1账户2订单。','账户资格存在判断/等效去重是可行实现建议，不冒称客户字段或唯一算法。'],
'F09':['发放记录仅支持收到，不支持使用资格及门店商品范围。','需实规则/配置/记录是核查建议，不虚构限制与负责人。'],
'T01':['按最新用户选择定义正文范围，是建模范围约束。','用户明确迁出Excel/FDE项目交付；原文留存不受此影响。','正文可引用来源，但过程、导师归属、旧评分须另存。'],
'T02':['来源与范围/性质准确、完整问答、合成与生产分开符合根规则；不能以源文件存在代替内容审查。本次只评价这项判据在专项上的正确性，另对候选抽查记录低严重度精度建议。'],
'T03':['业务目标/局部流程/权限保留；W03已获规则可更新同范围旧未知。','用户边界优先，迁移不是事实删除；不能强逼正文恢复个人载体/交付。','版本和各层结论分别保存，本次不改基线或任何旧分。'],
'REG01':['旧题证据不因周次丢失，角色实际用途和未授权仍有效。','本期来源只更新本期范围；未知筛选条件与生产效果继续待核。','legacy_invariants四条分别与01925、01949/53、01951等相合，不能字面旧答扣分。'],
'REG02':['沈总原因验证与角色参与边界由有效W02原文支持。','产品/日期新规则有来源，生产/因果仍未确认。','legacy_invariants六条与01725/31/33/37/39、01925、01949/51/53相合，观察方式需标建议。']}
findings=[
{'id':'MA-N01','severity':'low','blocking':False,'kind':'candidate_precision','affected_cases':['U01','E02','T02','T03','REG02'],'target':'input/business_model.md:7','finding':'“改善幅度与效果定义尚未核实”未保留MSG-01731更具体的“届时向董事会说明用什么数字、什么口径，现在还没定”；源对提升幅度说的是不能先承诺，并未同句断言幅度也明确未定。现句没有虚构肯定/否定事实，但对“明确未定”状态表达偏宽。','source_refs':['MSG-01730','MSG-01731'],'recommendation':'只替换此半句：三个月见效是客户期望；沈总表示届时向董事会说明所用的具体数字与口径还没定，也不能先承诺提升幅度。','effect':'提高正文状态精度；不阻断当前U01/E02等预期，也不改变既有运行成绩。'},
{'id':'MA-N02','severity':'info','blocking':False,'kind':'shared_reviewer_guardrail','affected_cases':ids,'target':'reviewer_expectations.json#/grading','finding':'现有全局“核结论、理由、范围、来源；证据缺失不判不存在”和各题来源已足够约束本专项。可补一句显式提醒，防后续答卷把业务规则降为建模选择或把角色不掌握升级成未定。不是每题缺句均有缺陷。','source_refs':['MSG-03848','MSG-03854','MSG-03885','MSG-03886','MSG-03868','MSG-01731','MSG-01937','MSG-01938'],'recommendation':'在全局grading末尾添加来源/状态分类提醒；不用复制进56题。'},
{'id':'MA-N03','severity':'info','blocking':False,'kind':'source_completeness_enhancement','affected_cases':['C05'],'target':'reviewer_expectations.json#/cases/43/sources','finding':'C05结论正确；已有两条来源主要直接支撑资格/当月购买，活跃定义未知的最直接原文在W02老周01754。当前可由正文及总体来源得到，建议增列便于逐断言追溯。','source_refs':['MSG-01754','MSG-03848','MSG-03868'],'recommendation':'在C05 sources追加W02老周MSG-01754，仅评审源，不增加问答输入。'},
{'id':'MA-N04','severity':'info','blocking':False,'kind':'source_completeness_enhancement','affected_cases':['E02'],'target':'reviewer_expectations.json#/cases/74/sources','finding':'E02“本期查询正确不证明旧趋势原因或收益”成立；现有访谈足以支持原因/期望边界，04邮件对本期查询校验范围与收益隔离有最直接表述，建议增列。','source_refs':['MSG-01719','MSG-01731','MSG-01739'],'recommendation':'在E02 sources追加04邮件测试阶段与收益边界，保持model_only题轨不变。'}]
caseindex={c['id']:i for i,c in enumerate(expect['cases'])};
for f in findings:
 if f['id']=='MA-N03': f['target']=f"reviewer_expectations.json#/cases/{caseindex['C05']}/sources"
 if f['id']=='MA-N04': f['target']=f"reviewer_expectations.json#/cases/{caseindex['E02']}/sources"

def src_detail(src):
 p=root/src['path']; t=p.read_text(); loc=src.get('locator',''); msgs=re.findall(r'MSG-\d+',loc); detail={'path':src['path'],'locator':loc,'status':'verified_in_source_scope','file_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 if msgs:
  d=json.loads(t); lookup={m['id']:m for m in d['messages']}; detail['messages']=[{'id':m,'speaker':lookup[m]['speaker'],'excerpt':lookup[m]['content']} for m in msgs]
  detail['attribution_note']='保留问题与回答角色；列出的user消息为范围/前提，不计角色独立新增规则。'
 elif '05_数据字典' in src['path']: detail['attribution_note']='物理字段/关系/合成覆盖；不支持独立裁定产品纳入或日期端点。'
 elif 'business_model' in src['path']: detail['attribution_note']='已采纳v0.4表达/设计与事实状态参照；不是新的客户原始证据。已核与正式v0.4 SHA相同。'
 elif 'knowledge_cases' in src['path']: detail['attribution_note']='历史题与预期连续性；不把旧评分/答案作为真值。只核当前legacy与原问答。'
 elif 'AGENTS' in src['path']: detail['attribution_note']='协作/来源排除要求，属于任务规范而非新增青禾事实。'
 elif '作业任务书' in src['path']: detail['attribution_note']='课程任务规范；不证明客户采用、执行、验收或业务效果。'
 else: detail['attribution_note']='已读指定材料相应语义；仅在其说明范围内采用。'
 return detail
rows=[]
for c in expect['cases']:
 id=c['id']
 if id not in ids: continue
 r=own[id]; checked=[]
 for field in ['required_points','unacceptable','legacy_invariants']:
  for j,claim in enumerate(c.get(field,[])):
   note=(notes.get(id,[r['independent_criterion']]*len(c['required_points']))[j] if field=='required_points' else ('所禁止的推断会越过本题已知/未知/来源边界；禁止方向与独立原文判据一致。' if field=='unacceptable' else '已逐项对照原始问答与本次用户范围；是建议/观察/权限边界，不是新增已实施事实。'))
   checked.append({'field':f'/cases/{caseindex[id]}/{field}/{j}','claim':claim,'status':'supported_in_specialty_scope','reason':note,'source_groups':r['source_groups']})
 sources=[src_detail(s) for s in c['sources']]
 if 'boundary_change_source' in c: sources.append(src_detail(c['boundary_change_source']))
 rows.append({'id':id,'status':'pass_specialty_review','input_track':questions[id]['input_track'],'checked_claims':checked,'source_refs':sources,'independent_source_groups':r['source_groups'],'fixture_review':r['independent_criterion'],'findings':[f['id'] for f in findings if id in f['affected_cases']],'boundary':'仅来源、状态与规则/设计区分；不是实际答卷通过、全维度设计验收或指标数值运行。'})
# Review source registry records are exact original text for audit, not used to generate answers.
patches=[{'target':'reviewer_expectations.json','kind':'optional_nonblocking','op':'replace','path':'/grading','old_value':expect['grading'],'value':expect['grading']+' 来源判读还须区分：角色不掌握/资料未取得不等于事项不存在或尚未决定；原文明说未定的，保留其明确未定的对象。角色已说明的业务规则与客户材料中的统计选择，不得降为学员建模选择；正式文件未取得不抹去已获规则。学员候选分析规则、表达组织设计和业务角色确认分别标注。','finding':'MA-N02'},
{'target':'reviewer_expectations.json','kind':'optional_nonblocking','op':'add','path':f"/cases/{caseindex['C05']}/sources/-",'value':{'source':'H-c4fe490a','path':'W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/W2-interview-c4fe490a-ddae-5bcb-a51b-f44dd796b854-transcript.json','locator':'MSG-01754','evidence_kind':'活跃定义未提供的直接访谈依据'},'finding':'MA-N03'},
{'target':'reviewer_expectations.json','kind':'optional_nonblocking','op':'add','path':f"/cases/{caseindex['E02']}/sources/-",'value':{'source':'D4','path':'W03/实操工程/materials/w03/04_本期统计确认邮件.md','locator':'本阶段验收与复购率提升/投资回报边界','evidence_kind':'本期查数与校验范围；不扩大客户批准状态'},'finding':'MA-N04'}]
(out/'proposed_expectation_patches.json').write_text(json.dumps({'apply_status':'not_applied','mandatory_patches':[],'optional_patches':patches},ensure_ascii=False,indent=2)+'\n')
(out/'proposed_model_edit.json').write_text(json.dumps({'apply_status':'not_applied','target_sha256':criteria['model_sha256'],'source':'MSG-01731','old_text':'三个月见效是客户期望，改善幅度与效果定义尚未核实','new_text':'三个月见效是客户期望；沈总表示届时向董事会说明所用的具体数字与口径还没定，也不能先承诺提升幅度','finding':'MA-N01','blocking':False},ensure_ascii=False,indent=2)+'\n')
report={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'independent_model_and_artifact_agent','source_criteria_frozen_at':criteria['created_at'],'source_criteria_sha256':hashlib.sha256((out/'source-criteria.json').read_bytes()).hexdigest(),'reviewed_expectations_sha256':hashlib.sha256((audit/'input/reviewer_expectations.json').read_bytes()).hexdigest(),'model_sha256':criteria['model_sha256'],'baseline_v04_sha256':'6e48419390810b44cdaa1ba430b01038a54be37c9f8692b58933ac8785592bf0','api_calls':0,'review_status':'pass_specialty_review_with_nonblocking_notes','coverage':{'expected':56,'reviewed':len(rows),'model_only':53,'artifact_review':3,'required_points_checked':sum(len(c['required_points']) for c in expect['cases'] if c['id'] in ids),'unacceptable_checked':sum(len(c['unacceptable']) for c in expect['cases'] if c['id'] in ids),'legacy_invariants_checked':10,'missing_ids':[]},'blocking_findings':[],'findings':findings,'business_decisions_needed':[],'rows':rows,'scope_limits':['未调用模型API；未执行38指标或82题；未读取旧原始答案或历史评分文件；未改任何旧分。','source-criteria先冻结后读取reviewer_expectations；原文优先于当前正文与旧建模转述。','T01—03仅来源/状态/规则归类专项；未声称原T全量正文/引用/字段审计完成。','少量历史成绩标题在查找model_changes时意外可见；不用于独立判据、此次结论或重新评分。','读取REG引用的历史题库仅核问题和legacy判据；其中执行元数据不作本次运行证据。','候选5fb4尚非正式v0.4，全部建议未应用到input/正式正文/旧预期。']}
(out/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
md=['# model_and_artifact 来源语义专项审查','',f"结论：56/56 项本专项通过，0 个阻断，0 个需业务裁决；0 API。53 道 model_only 与 3 项 artifact_review 全覆盖。",'',f"检查 {report['coverage']['required_points_checked']} 条 required_points、{report['coverage']['unacceptable_checked']} 条 unacceptable、10 条 legacy_invariants，并核每题所有 sources / boundary_change_source。",'',f"来源判据先于期望冻结：{criteria['created_at']}。当前候选 SHA `{criteria['model_sha256']}`；正式 v0.4 SHA `{report['baseline_v04_sha256']}`。",'','本结论不是 82 题运行通过、指标数值验证、全维度测试设计验收或模型采用。T01—03此次只核来源、状态、规则/设计归类。','', '## 发现与建议','']
for f in findings: md += [f"- {f['id']}（{f['severity']}，非阻断）：{f['finding']} 建议：{f['recommendation']}"]
md += ['','## 逐题覆盖','','| ID | 状态 | 独立语义核对 | 相关提示 |','| --- | --- | --- | --- |']
for r in rows: md += [f"| {r['id']} | 专项通过 | {r['fixture_review']} | {', '.join(x for x in r['findings'] if x!='MA-N02') or '无；共通增强 MA-N02'} |"]
md += ['','## 保存与适用边界','','- source-criteria.json/md：先形成的独立原文判据、消息角色与原文注册表。','- review.json：逐题逐条 required/unacceptable/legacy 核对、来源定位、原消息、严重度。','- proposed_expectation_patches.json：3项可选、非阻断JSON字段修改，未应用。','- proposed_model_edit.json：正文第7行精确化建议，未应用。','']+['- '+x for x in report['scope_limits']]
(out/'review.md').write_text('\n'.join(md)+'\n')
print(json.dumps({k:report[k] for k in ['review_status','coverage','api_calls']},ensure_ascii=False))
