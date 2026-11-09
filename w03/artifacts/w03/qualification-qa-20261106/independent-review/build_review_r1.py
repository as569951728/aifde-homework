from pathlib import Path
import json,hashlib,datetime
b=Path('artifacts/w03/qualification-qa-20261106-r1');out=Path('artifacts/w03/qualification-qa-20261106/independent-review');r0=json.loads((out/'review-r0.json').read_text());old={r['id']:r for r in r0['cases']};audit=json.loads((out/'runtime-integrity-r1.json').read_text());am={r['id']:r for r in audit['cases']};rows=[]
checks={
'U02':[('七项身份与概念','七项分列，账户不等于自然人、卡可多张、等级与资格分开；付费资格非活跃/购买事实。'),('资格/有效购买/活跃','规则保持同一卡产品+有效期，支付净额>0才有效购买，活跃定义未知不判负。'),('例子与不可推出','明确为构造例：金卡账户一有效纳入卡和一失效卡，订单部分有效/全退无效，活跃未知。'),('复购率','群体指标，定义与结果分开；没有强行补入正文未写出的客户具体指标公式。'),('R0来源与字段失败复查','有明确来源规则按原范围使用；未笼统归成未确认学员选择，提前终止为空未扩成计划结束为空。')],
'U03':[('关系基数','账户多卡/多订单、卡订单各归一账户、账户当前归属店与订单成交店分列，门店可多账户/订单。'),('成交门店','明确归B；A仅归属。'),('订单用卡','明确现有账户关系不能证明实际用哪卡，需订单—卡使用记录。')],
'P01':[('结论','有本期资格。'),('理由与负例','有效悦享年卡满足，普通等级/购卡实付不能代替规则。'),('范围','只用完整人工情境，非生产事实。')],
'P02':[('结论','有本期资格。'),('理由与负例','有效家庭季卡满足同卡条件，普通等级/3000分不改变。'),('范围','完整卡记录与已知状态允许情境判断，正式文件缺失不拦题目结论。')],
'P03':[('结论','无本期资格。'),('理由与负例','唯一悦享卡失效，完整记录无其他合格卡，金卡/金额不补足。')],
'P04':[('结论','无本期资格。'),('理由与负例','唯一有效联名卡不纳入，收费/等级不改变。')],
'P05':[('结论','无本期资格。'),('理由与负例','体验卡产品范围不合，非由0分或普通等级否定。')],
'P06':[('结论','有本期资格。'),('理由与负例','有效家庭季卡即满足，0分不排除，普通等级不阻止。')],
'P07':[('未知处理','不能判有/无，金卡不能代替。'),('缺失信息','需要账户卡类型/起止/提前终止及业务范围、判定日；不给卡不等于无卡。')],
'P08':[('范围','只本期，不直接套历史/合作方。'),('下一步','按报表核用途、期间、产品、判定日、覆盖、规则来源，合作方独立确认。')],
'P09':[('两项主结论','不确定全系统免费，不能证明绝对互斥。'),('理由','本期资格与系统类别两种规则；互斥/重叠未有记录核验。'),('R0条件漂移复查','保持“A仅持有有效异业联名卡”，未再把其他卡作为当前未决条件。')],
'C01':[('数与身份','1有资格账户、2笔订单，O1/O2各一次。'),('关联','卡资格收敛到账户层，再按订单识别计数，避免卡×订单组合。'),('R0证据降级复查','本期模型及原消息作为规则依据，未把规则整组归为待确认学员选择。')],
'C02':[('存在条件','有效家庭季卡即可，失效悦享/联名不否定。'),('题设','接受本题完整卡记录和有效状态。')],
'C03':[('同卡条件','不能跨卡拼接；两卡各不满足完整条件。'),('R0完整性漂移复查','直接写“在题设条件下结论是不具备本期付费资格”，不再索取生产完整性才能判。'),('R0角色引用复查','仅准确列消息ID，未将小林消息归陈姐。')],
'C04':[('完整无卡','明确无本期资格。'),('未提供','缺信息则未知，不当成无卡。'),('R0作者归属复查','引用字典/模型/消息，没有补造导师/审查建议身份。')],
'C05':[('资格','8月月末有本期资格，未购不取消。'),('购买','完整订单记录无有效购买，paid净额>0解释一致。'),('活跃','无法判活跃或不活跃，需定义。'),('R0来源分层复查','资格归具体模型/消息，有效购买归订单/财务材料，活跃未知归模型和01719/01754，没有说成学员选定状态。')],
'C06':[('混合产品多卡','1账户、2有效订单，悦享+家庭不累加人次/订单。'),('关联','卡侧按同卡条件和账户去重，订单侧order_id，按账户联系，禁止卡数复制订单。'),('边界','本题人工推导不是客户查询，无订单实际卡关系。')]
}
notes={
'U02':['例子中“是否构成复购或复购率变化，也不能由该账户单独得出”把个体复购判断和群体指标写在一起，不够精确。当前例子未给复购定义、统计期间或完整历史，未知结论可成立；若今后已有这些条件，单账户是否复购可以判断，不宜抽象成永远不能判断。此题核心是复购率的群体含义，完整答复没有输出错误的具体复购判定，本轮不判失败。'],
'U03':['“没有直接关系／无关联”按全文明确的本期字典关系边界解读；宜统一为“本期资料未提供直接关联”，避免读成生产业务不存在关联。答案多次明确实际用卡未知并需记录，故未判实质失败。'],
'P02':['仍使用“本期口径下的建模选择”泛称。全文同时逐项指明原访谈依据，并未否定其有来源或将人工条件改成未核，所以按R0同一原则不因该词单独判失败。'],
'C01':['“账户按人去重”建议改为“按CRM账户标识去重”。本答同时明确1个账户、资格收敛到账户层及订单标识粒度，没有提出跨系统自然人合并，故按完整语义本轮通过，而非按单个词判错。此题只有一个账户，不能据本结果宣称已测试跨账户自然人映射。']
}
for id in [r['id'] for r in r0['cases']]:
 d=json.loads((b/'output'/f'{id}.json').read_text());row={'id':id,'verdict':'pass','previous_verdict':old[id]['verdict'],'required_point_review':[{'point':k,'status':'pass','actual':v} for k,v in checks[id]],'dimensions':{k:'pass' for k in ['身份与对象','关系与粒度','主要结论','理由与反例','范围与题设','引用与证据性质']},'source_check':old[id]['source_check'],'r0_issue_resolution':[{'code':i['code'],'status':'not_reproduced','evidence':'见本题 required_point_review 中 R0 复查项及保存的完整实际答复。'} for i in old[id]['issues']],'issues':[],'nonblocking_notes':notes.get(id,[]),'native_run':d['result']['run'],'output_path':str(b/'output'/f'{id}.json'),'output_sha256':am[id]['output_sha256'],'run_sha256':am[id]['run_sha256'],'request_sha256':am[id]['request_sha256'],'actual_answer':d['actual_answer']}
 # Re-use source identities, not R0-specific negative annotations.
 if id=='U02':row['source_check']=['DICT、ORDERS、FINANCE；LIN3 03848/03854；CHEN3 03886/03888/03890；ZHOU2 01744/01754支持对象、资格、有效期、活跃未知。']
 if id=='C03':row['source_check']=['LIN3 03848/03854/03870与CHEN3 03886/03888支持同卡条件；本轮没有错误的角色归属。']
 rows.append(row)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'round':'r1','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'/root/w03_qualification_qa_reviewer','status':'passed_for_this_17_case_regression_only','counts':{'pass':17,'needs_revision':0,'indeterminate':0},'r0_counts':r0['counts'],'candidate_sha256':sha(b/'input/business_model.md'),'prompt_sha256':sha(b/'input/knowledge_prompt.txt'),'run_index_sha256':sha(b/'run_index.json'),'manifest_sha256':sha(b/'input/manifest.json'),'runtime_integrity':{'status':audit['status'],'cases':17,'actual_attempts':17,'length_or_semantic_retries':0,'input_expected_leakage':False,'tools':False,'protected_files_unchanged':all(audit['protected_files'].values())},'change_control':'模型正文、原题、fixture、预期、GUARD、runner和模型参数不变；仅客户层回答提示变更，配置路径改到隔离副本。批准新提示hash与实际请求逐题一致。','rubric':'沿用来源优先判据及读实际答案前的U02概念题门槛校准；没有按R1输出修改预期，也不因措辞不同要求背固定答案。','cases':rows,'conclusion':'R0的6题实质失败在R1均未再出现，原11题在同一判据下未见实质回归。17题通过；仍保留4题非阻塞表述观察，不将本轮通过写为业务模型全文完备、所有测试通过或生产可用。','authorization_and_scope':['同一已见17题测试集的一次有界回归，不证明未见题泛化，不证明长期稳定性。','两轮共34次成功调用都保留；不覆盖R0失败，不用R1回改R0。','正式v0.4、现用prompt、Skill及配置未替换，未apply。','未做日期专题、其余模型题、38项指标SQL/数值独立对账、客户验收或课程提交。','当前这17题没有需用户做真实业务裁决的冲突；正式规则文件、生产历史凭据和活跃定义等原未知继续保留。']}
(out/'review-r1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
md=['# 首批17题实际问答独立回归评审 R1','','结果：17 pass，0 needs_revision，0 indeterminate。仅对这17题本次回归成立。','',report['conclusion'],'',report['change_control'],'',f"模型 SHA256：`{report['candidate_sha256']}`",f"提示 SHA256：`{report['prompt_sha256']}`",f"运行索引 SHA256：`{report['run_index_sha256']}`",'','17份实际请求、原生快照和答案分别核对；各1次成功尝试，无长度/语义重试，无预期、其他题或工具泄漏。正式保护文件hash均不变。','','## 逐题','']
for row in rows:
 md += [f"### {row['id']} — pass（R0：{row['previous_verdict']}）",'','- '+'；'.join(x['point']+'：'+x['actual'] for x in row['required_point_review']),f"- 实际输出：`{row['output_path']}`",f"- 原生记录：`{row['native_run']}`",f"- 输出 SHA256：`{row['output_sha256']}`"]
 if row['r0_issue_resolution']:md += ['- 首轮问题本轮未再出现：'+', '.join(x['code'] for x in row['r0_issue_resolution'])]
 for note in row['nonblocking_notes']:md += ['','非阻塞观察：'+note]
 md += ['']
md += ['## 保留边界','']+['- '+x for x in report['authorization_and_scope']]
(out/'review-r1.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'counts':report['counts'],'run_index_sha256':report['run_index_sha256'],'files':['review-r1.md','review-r1.json']},ensure_ascii=False))
