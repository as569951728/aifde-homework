import json,pathlib,re,datetime,hashlib,collections
root=pathlib.Path.cwd(); base=root/'W03/实操工程/artifacts/w03/source-semantics-audit-20261108';out=base/'reviews/source_context'
criteria=json.loads((out/'source-criteria.json').read_text()); exp=json.loads((base/'input/reviewer_expectations.json').read_text()); questions=json.loads((base/'input/original_questions.json').read_text()); qs={x['id']:x for x in questions['cases']}; ids=[x['id'] for x in criteria['cases']]; cc={x['id']:x for x in criteria['cases']}
# Verdicts are source-semantics review only, not a replay of historical answers.
notes={
'U05':{'r':['03885限定两类卡，03886给出规则并保留文件/历史缺证，03890重申；候选正确保留两种证据状态。','01918先引入没人用，01919新增负担感受，01921限定非精确步骤；候选归属正确。','01945/01953不掌握返店细节，未核不能判无；01719/01744分别是活跃/全量口径，不能直接算活跃率。','本次候选已区分王经理不知道具体人/额度与正式批准未定，未将两项未知强写成公司未设。03931另有“审批安排还没定”，可保留但U05并未禁止该陈述。'], 'u':['负例正确防止抹去已答规则。','负例正确拦截问题前提升级。','重复转述不是新增独立证据，核查意见不能升级批准。']},
'F01':{'r':['03858个人表用途与非统一/非交付限制、03870交叉核对用途直接支持；“核来源字段后辅助还原”为明示推导，不断言表内容已验真。'],'u':['同时排除当权威统计和完全禁用，两端均符合来源。']},
'F02':{'r':['03860是岗位偏好与助手限制；03910/11阶段草案和认可边界支持不自动改变本期范围。'],'u':['“不让助手”不等于“小林本人无权”；权限主体负例准确。']},
'F07':{'r':['配合范围和无固定交付承诺准确；“没有生产权限/真实接入”缺证据主体，容易将尚未取得授权/接通证明扩成事实不存在，建议改为“访谈未授予权限、未证实真实接通”。'],'u':['既不能抹去可配合事项，也不能升级实际交付和接入批准。']},
'F10':{'r':['01685确认注册指标，完整构成未掌握；不能补计分或责任人。','01824只是转问，01907不能确认且个人表非考核依据；候选正确保留后续否认确认能力。'],'u':['三个禁止推论均有直接问答依据。']},
'A01':{'r':['03910提议、03911认可分期及03919分工直接对应；“阶段成果”要读作拟交付，候选禁止已完成可防升级。'],'u':['原文明确测试正确不等于验收、收益或批准，禁止上线/已完成有据。']},
'A02':{'r':['“尚待落实”将信息不掌握与事项未决定压成一类。03930未知人为问题前提；03931直接分述不掌握人/额度及审批安排还没定；03933分述执行方/权限不掌握、收益/金额/批准未定。建议显式拆开。'],'u':['禁止擅定人正确，但还应拦“未核实所以公司没设额度”和删除03931直接未定陈述两种来源错误。']},
'A03':{'r':['费用/节点/确认记录对应03927；“付款安排待双方谈定”作为未有约定的推导成立，但具体同词来自03932提问方总结，03933不构成付款批准。建议补标推导/来源精度。'],'u':['金额比例或已承诺节点无来源，禁止正确。']},
'A04':{'r':['03924支持范围为拟议前提；03925书面变更要求与核查权限明确。候选未把具体筛选条件补成已定。'],'u':['书面提出、依据不足复核和核查非审批直接支持。']},
'A05':{'r':['03929明确书面缺项/影响、执行安排方决定、双方书面确认后复核；未谈金额待确认。'],'u':['03928明确可能情境，不能写成已发生；无自动顺延加费或王经理执行权。']},
'A06':{'r':['03923核查、补充复核及暂缓财务确认是有条件流程，非永久否决或批准。'],'u':['与材料不足需补充的边界一致。']},
'E01':{'r':['完整01918—01921支持前提归属、个人负担感受、未精确量化；保留原问答是审查做法。'],'u':['三种不可接受均是对应直接证据的来源保护。']},
'E04':{'r':['前两角色未掌握不构成反规则，后来03886/90直接说明规则，可更新模型；文件与历史仍另缺。测试范围描述限定使用，没有将规则降为导师选择。'],'u':['同时拦全部未知和生产普适化，与来源一致。']},
'E06':{'r':['现文只写陈姐答复适用范围，未明确其新增日期/空值/账户规则；题目明确要区分提问限定与角色新增答复，仅给范围判据不足以防“只是接受问题，没有新增规则”。王经理总结认可边界方向正确；须连03931保留审批安排未定与具体额度未知。'],'u':['现有两项禁止正确，但未拦删除角色新增规则、把未知升级未设及把直接未定降为未知。']}
}
findings={
'F07':[{'finding_id':'SC-F07-01','kind':'unknown_to_absence_risk','severity':'must_clarify','field':'/cases/64/required_points/0','detail':'“没有生产权限/真实接入”字面是状态否定；原访谈只否定以测试推断生产接通且不作交付承诺，没有证明所有生产权限均不存在。','source_ids':['MSG-03875','MSG-03877','MSG-03881','MSG-03883'],'recommendation':'按实际证据层级写未获本次授权/未证实接通，保留配合与日期安排边界。'}],
'A02':[{'finding_id':'SC-A02-01','kind':'unknown_vs_undecided_collapse','severity':'must_clarify','field':'/cases/69/required_points/0','detail':'“最终验收人、审批权限/授权额度与执行安排责任方尚待落实”未区分王经理不掌握与公司尚未决定；也缺直接“审批安排还没定”的并列状态。','source_ids':['MSG-03930','MSG-03931','MSG-03932','MSG-03933'],'recommendation':'保留总体审批安排未定的角色陈述；具体人/额度/执行方仍待核，不能推出公司未指定或未设定。'}],
'A03':[{'finding_id':'SC-A03-01','kind':'source_precision_note','severity':'optional_precision','field':'/cases/70/sources/0/locator','detail':'付款安排待谈的措辞出自03932总结，03927仅直接说节点切分和确认记录待谈。现有derivation允许情境推导，结论不属实质越权，但对本轮引用精度宜补上下文并标性质。','source_ids':['MSG-03926','MSG-03927','MSG-03932','MSG-03933'],'recommendation':'补03932/03933，注明付款安排未获确认是综合判断，不能冒称03927原话或03933付款批准。'}],
'E06':[{'finding_id':'SC-E06-01','kind':'new_role_assertion_omitted_from_criteria','severity':'must_clarify','field':'/cases/79/required_points/0','detail':'该题要求角色新增答复，现判据对陈姐只写范围，未防将其直接业务规则降成纯总结或建模选择；王经理也需逐事项区分未知与未定。','source_ids':['MSG-03885','MSG-03886','MSG-03910','MSG-03911','MSG-03930','MSG-03931','MSG-03932','MSG-03933'],'recommendation':'明确两类卡/月末等是提问范围；端点/空终止/判定日/账户规则为陈姐新增；保留王经理直接陈述及总结的权限边界。'}]
}
patches=[
 {'op':'replace','path':'/cases/64/required_points/0','value':'说明核查对象、用途和范围；老周配合核对取数条件、系统统计所用的范围、时间和统计说明，列出待补记录与待确认责任。访谈中的配合说明不构成生产访问授权，也不能证明真实数据已经接通；具体核查记录取决于实际材料，目前没有固定交付或日期承诺。','reason':'SC-F07-01'},
 {'op':'add','path':'/cases/64/unacceptable/-','value':'将本次未取得生产权限或接通证据写成公司或当事人不存在生产权限、真实数据一定未接通。','reason':'SC-F07-01'},
 {'op':'add','path':'/cases/64/sources/-','value':{'path':'W03/实操工程/materials/w03/07_客户内部沟通.md','locator':'IT 对接纪要：样例能跑与上线接入','evidence_kind':'课程虚构沟通：生产清理、导入及联调时间另行安排'},'reason':'SC-F07-01'},
 {'op':'replace','path':'/cases/69/required_points/0','value':'不能；王经理参与统计口径、验收依据及合同材料核查，认可总结不等于最终验收、预算签约或上线批准。03930中“最终验收确认人尚未明确”为提问前提；03931/03933中他明确自己无法确认具体最终验收人、授权额度/审批权限和执行安排责任方，需要另行核实，不能据此断定公司尚未指定或尚未设定这些事项。同时保留03931直接陈述“审批安排还没定”，以及03933的收益目标、预算金额和正式批准尚未定；总体安排未定不能代替对具体授权额度的核实。','reason':'SC-A02-01'},
 {'op':'add','path':'/cases/69/unacceptable/-','value':'把王经理不掌握具体确认人或授权额度写成公司尚未指定或尚未设定；或因这些细节未知，抹去03931“审批安排还没定”和03933“正式批准都还没定”的直接陈述。','reason':'SC-A02-01'},
 {'op':'replace','path':'/cases/70/required_points/0','value':'可列费用构成/计价依据，并拟使结算与阶段成果及确认记录对应；未谈妥金额、具体节点划分和确认记录形式待双方谈定。现无已确认付款安排；“付款安排仍待谈”的文字见03932提问方总结，综合前文可保留未确认状态，不得称03927原话或把03933认可核查顺序当作付款批准。','reason':'SC-A03-01','optional':True},
 {'op':'replace','path':'/cases/70/sources/0/locator','value':'MSG-03926、MSG-03927、MSG-03932、MSG-03933','reason':'SC-A03-01','optional':True},
 {'op':'replace','path':'/cases/79/required_points/0','value':'陈姐03885提问已限定本期月报、月末、按账户和两类卡；03886在该范围新增生效当天有效、计划结束及提前终止当天无效、空终止不等于无限、按要求判定日检查和账户资格/去重规则，同时保留具体文件与历史凭据不掌握。王经理03910讨论的是学员阶段草案；03911认可边界并补四类说明、核查分工和权限限制，不等于公司主动提出全部方案或正式批准。03932为提问方总结，03933的认可须连前文读取：03931直接说审批安排还没定；具体验收人/授权额度及执行责任方他不掌握需另核，不能推公司未设；03933收益目标、预算金额和正式批准未定是独立直接陈述，不能全部降为未知。','reason':'SC-E06-01'},
 {'op':'add','path':'/cases/79/unacceptable/-','value':'把陈姐新增的日期、空终止和账户规则说成只是接受提问范围或导师可选建模方案；把王经理不掌握额度改成公司未设额度；或抹去其审批安排、正式批准未定的直接陈述。','reason':'SC-E06-01'},
 {'op':'replace','path':'/cases/79/sources/1/locator','value':'MSG-03910、MSG-03911、MSG-03930、MSG-03931、MSG-03932、MSG-03933','reason':'SC-E06-01'}
]
# Collect all candidate source refs and all surrounding complete messages.  They were read after criteria.
source_cache={}; source_records={}; cases=[]; totals=collections.Counter()
for index,e in enumerate(exp['cases']):
 if e['id'] not in ids:continue
 i=e['id']; checked=[]
 for field,short in [('required_points','r'),('unacceptable','u')]:
  for j,v in enumerate(e[field]):
   verdict='supported'
   if field=='required_points' and i in ('F07','A02','E06'):verdict='needs_clarification'
   elif field=='required_points' and i=='A03':verdict='supported_with_source_precision_note'
   checked.append({'field':f'/cases/{index}/{field}/{j}','value':v,'status':verdict,'rationale':notes[i][short][j],'source_refs':cc[i]['source_refs']})
 for j,s in enumerate(e['sources']):
  p=s['path']; d=source_cache.setdefault(p,json.loads((root/p).read_text())); ms={m['id']:m for m in d['messages']}; loc=re.findall(r'MSG-\d+',s['locator']); missing=[x for x in loc if x not in ms]
  assert not missing,(i,p,missing)
  supported_by_model=p not in qs[i]['fixed_materials']
  context=set()
  for n,m in enumerate(d['messages']):
   if m['id'] in loc:
    context.update(range(max(0,n-1),min(len(d['messages']),n+2)))
  context_ms=[d['messages'][n] for n in sorted(context)]
  sr={'path':p,'locator':s['locator'],'origin':d['origin'],'week':d['week'],'role_id':d['role_id'],'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest(),'context_messages':context_ms}
  source_records[f'{i}:{j}']=sr
  rationale='定位ID存在且角色/周次正确，完整前后问答已核；引用支持本题对应规则或限定，不构成新增授权。'
  if supported_by_model:rationale+=' 该原始文件未在本题fixed_materials中，运行时仅模型已有转述可见；预期可作审查者证据，不要求被测模型伪造未提供的原文。'
  if i=='A03':rationale+=' 付款安排文字在后续03932总结；建议补03932/03933并区分直接引文与推导。'
  checked.append({'field':f'/cases/{index}/sources/{j}','value':s,'status':'supported_with_source_precision_note' if i=='A03' else 'verified','rationale':rationale,'source_refs':loc,'source_not_directly_in_fixed_materials':supported_by_model})
 status='needs_source_semantics_clarification' if i in ('F07','A02','E06') else 'pass_with_precision_note' if i=='A03' else 'pass_source_semantics'
 totals[status]+=1
 cases.append({'id':i,'status':status,'checked_claims':checked,'source_refs':cc[i]['source_refs'],'findings':findings.get(i,[]),'candidate_case_index':index,'candidate_fields_checked':{'required_points':len(e['required_points']),'unacceptable':len(e['unacceptable']),'sources':len(e['sources'])},'not_assessed':['历史答案与评分','其他测试维度','模型API运行及指标执行']})
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
review={'created_at_utc':now,'reviewer':'independent source_context subagent','scope':'14题来源语义专项；只核业务模型正文相关来源和问答引用准确性。A类交付问题不写回业务正文。','model_api_calls':0,'criteria_before_expectations':{'criteria_created_at_utc':criteria['created_at_utc'],'criteria_sha256':hashlib.sha256((out/'source-criteria.json').read_bytes()).hexdigest(),'candidate_expectations_first_read':'criteria落盘后才读取；时序见本会话工具记录','candidate_expectations_sha256':hashlib.sha256((base/'input/reviewer_expectations.json').read_bytes()).hexdigest()},'counts':dict(totals),'cases':cases,'suggested_json_field_changes':patches,'source_evidence':source_records,'business_decisions_needed':[],'non_changes':['未改input或historical_expectations','未改历史评分/答案','未调用模型API','未更新正式模型或Skill','未扩为全维度设计验收或模型运行通过'],'root_paraphrase_table_review':{'path':'artifacts/w03/source-semantics-audit-20261108/转述核对表.md','sha256':hashlib.sha256((base/'转述核对表.md').read_bytes()).hexdigest(),'status':'pass_source_semantics','rows':[{'row':1,'source_ids':['MSG-03931'],'finding':'准确并列审批安排未定与具体人/额度本人无法确认；拒绝从总体安排推额度未设。'},{'row':2,'source_ids':['MSG-03933'],'finding':'准确保留收益目标、预算金额、正式批准未定；没有以额度未知替换预算金额未定。'},{'row':3,'source_ids':['business_model:3','MSG-03885','MSG-03886','MSG-03890'],'finding':'准确保留角色业务规则及文件/生产历史凭据缺口，不降为自由建模选择。'},{'row':4,'source_ids':['business_model:来源索引'],'finding':'模型已有来源转述可支持模型题；未提供原文时不编引文，证据精度限制正确。'}],'required_changes':[]},'memory_use_disclosure':criteria['context_disclosure']}
(out/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
md=['# 来源上下文14题专项审查',f'审查时间（UTC）：{now}','仅审来源归属、前提/新增答复、已知/未知/未定、规则/建模选择及核查/批准边界。0模型API；不复评历史答案或分数；不宣称全维度设计或实际问答通过。',f'结论：10题来源语义通过；F07、A02、E06需收紧判据；A03结论可支持，另有可选引用精度建议。没有需用户裁定的业务取舍。',f"独立判据先落盘：{criteria['created_at_utc']}；SHA256 `{review['criteria_before_expectations']['criteria_sha256']}`。随后才读候选预期。",criteria['context_disclosure']]
for e in cases:
 md+=['',f"## {e['id']} — {e['status']}"]
 for f in e['findings']:md += [f"- {f['finding_id']}（{f['severity']}）：{f['detail']} 字段 `{f['field']}`。依据：{'、'.join(f['source_ids'])}。"]
 for cl in e['checked_claims']:md += [f"- `{cl['field']}`：{cl['status']}。{cl['rationale']}"]
md+=['','## 精确字段建议（仅建议，未改输入）']
for p in patches:md += ['',f"### {p['reason']} {p['path']} ({p['op']})",json.dumps(p['value'],ensure_ascii=False,indent=2)]
md+=['','## 王经理原文，防止删除后半句或混淆事项']
w=next(d for p,d in source_cache.items() if '92c91632' in p)
for m in w['messages']:
 if m['id'] in ['MSG-03930','MSG-03931','MSG-03932','MSG-03933']:md += [f"### {m['id']} {m['speaker']}",m['content']]
md+=['','## 导师转述表核对','4行来源语义通过；前两行分别保留03931审批安排未定、具体人/额度本人不掌握，以及03933收益目标/预算金额/正式批准未定，无需修订。表是导师示范，不是模型原答或实际测试通过。','','## 可追溯与限制','review.json逐题逐字段列出了全部required_points、unacceptable、sources的检查，source_evidence附实际来源、角色、周次、SHA256和完整前后问答。U05中3份历史来源未随题直接发送，模型只能引用其已见正文转述，不能被要求编造未提供的原话。']
(out/'review.md').write_text('\n\n'.join(md)+'\n')
print(json.dumps({'cases':len(cases),'counts':dict(totals),'fields_checked':sum(len(x['checked_claims']) for x in cases),'source_records':len(source_records),'suggested_changes':len(patches),'model_api_calls':0},ensure_ascii=False))
