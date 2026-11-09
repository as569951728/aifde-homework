import json,pathlib,hashlib,datetime
root=pathlib.Path.cwd(); batch=root/'artifacts/w03/date-boundary-qa-20261106'; out=batch/'independent-review'; sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
criteria=json.loads((out/'source-first-criteria.json').read_text()); criteria_cases={c['id']:c for c in criteria['cases']}; protocol=json.loads((out/'execution-protocol-review.json').read_text()); proto={c['id']:c for c in protocol['cases']}; selected=json.loads((batch/'input/selected_questions.json').read_text())['cases']
source_issue_quotes={
'DY01':'依据为 business_model 第3节规则1，来源 MSG-03848、03854 和《本期统计确认邮件》',
'DY11':'依据MSG-03848、MSG-03854及《本期统计确认邮件》',
'DY12':'悦享年卡属于本期总部运营月报纳入范围（《本期统计确认邮件》；MSG-03848、03854）',
'DQ12':'依据为业务模型第3节规则1及《本期统计确认邮件》所述本期范围'
}
manual_reason={1:'未到生效日；计划结束尚未到且空终止不解除开始限制。',2:'生效当天包含；未到计划结束且无提前终止。',3:'生效后、计划结束前，空终止不造成失效。',4:'计划结束前一天有效；仍核对开始日及空值限制。',5:'恰逢计划结束日，结束端不包含；空终止不能延长。',6:'已过计划结束日；空终止不能使卡继续有效。',7:'已生效、未到计划结束且早于提前终止日，三条件同时满足。',8:'提前终止当天已无效；计划结束尚未到不能覆盖终止约束。',9:'已过提前终止日；已生效和未到计划截止不能抵消终止。',10:'计划结束当天无效；较晚的 ended_at 不延长计划截止。',11:'按8月10日判断有效，明确排除8月31日运行日替代。',12:'未到生效日；未来的计划结束及非空提前终止均不免除开始约束。'}
notes={
'DY11':[{'id':'N-VERBOSITY','kind':'answer_relevance','severity':'nonblocking','quote':'与本题无关的未决项仍包括80万与120万口径、活跃定义、会员老化假设及复购原报表重算等','assessment':'这段自行承认与本题无关，增加阅读负担；未改变日期结论或补造事实。','suggestion':'删去无关经营未决项，保留本题日期与来源边界即可。'}],
'DQ11':[
 {'id':'N-SOURCE-SPLIT','kind':'source_precision','severity':'nonblocking','quote':'该口径只约束本期总部运营月报，依据 MSG-03848、MSG-03854 及《本期统计确认邮件》。','assessment':'此处引用紧随“只约束本期总部运营月报”，邮件确实支持本期月报统计范围；小林消息支持产品范围。全文可按不同来源分别支持邻近陈述理解，未明确称邮件列出两种产品，所以与四个直接挂在产品断言上的实例分级不同。仍建议拆开，避免读者误把邮件当产品清单来源。','suggestion':'卡产品范围引小林 MSG-03848/03854；邮件只引月末选账户、完整自然月及全渠道全门店的统计选择。'},
 {'id':'N-ACCOUNT-CAVEAT','kind':'unasked_extension','severity':'nonblocking','quote':'但本题未提供账户其他卡信息，因此不扩展判断账户整体资格','assessment':'若已知此卡属于某账户，一张范围内有效卡已经足以支持该账户资格，不能把其他卡信息当必要条件。此题只问单卡有效性，回答前文也准确重述“存在一张”规则且明确判卡有效，故尾句歧义未改变本题结论，列非阻断而不据此宣称该表述正确。','suggestion':'改为“本题只判断这张卡；若它归属于某账户，该卡即可提供该判定日的资格依据，不能由此生成真实账户名单。”'}],
'DQ12':[{'id':'N-CARD-ACCOUNT','kind':'terminology','severity':'nonblocking','quote':'这张家庭季卡在判定日 2026-05-19 不具有付费资格，即不是有效卡','assessment':'付费资格是账户的派生属性，卡宜写有效或无效。后续全文明确只判该卡尚未生效，没有把单卡无效扩成整个账户无资格，所以术语问题本身非阻断。','suggestion':'改为“这张家庭季卡在判定日无效，不能据此卡取得账户资格”。'}]
}
source_details={'id':'SRC-04-PRODUCT','kind':'source_attribution','severity':'requires_revision','criteria':['C01','C06','C07','C10'],'problem':'把《本期统计确认邮件》直接列为具体纳入卡产品的出处。04仅明确月末资格选账户、完整自然月、全渠道全门店等统计选择，且把卡产品范围和有效状态交运营与门店确认，没有列出悦享年卡或家庭季卡。','source_quote':'付费资格的卡产品范围和有效状态请向运营与门店确认，不能从等级或付款金额猜测。','correct_sources':['lin:MSG-03848','lin:MSG-03854'],'why_blocking_for_full_answer':'本轮检查完整回答的来源可追溯性。产品结论有正确依据，不代表同段并列的错误文档归因可以被抵消；这不是简单少引一条来源。虽未明确宣称生产核验或正式制度已获批，仍形成错误证据路径，所以日期逻辑通过，完整回答需修订。','suggested_correction':'产品范围仅归于业务模型第3节规则1所引的小林 MSG-03848、MSG-03854；需要讲统计时点与窗口时再引用04。','requires_user_business_decision':False,'date_logic_affected':False}
results=[]
for c in selected:
 id=c['id']; d=json.loads((batch/'output'/f'{id}.json').read_text()); a=d['actual_answer']; own=criteria_cases[id]; f=c['fixture']; n=int(id[2:]); issues=[]
 if id in source_issue_quotes:
  quote=source_issue_quotes[id]; assert quote in a; issues.append({**source_details,'actual_quote':quote})
 ns=notes.get(id,[])
 for note in ns: assert note['quote'] in a,(id,note['id'])
 verdict='fail' if issues else ('pass_with_nonblocking_suggestion' if ns else 'pass')
 k=own['required_conditions']; condition_checks=[
 {'condition':'product_in_scope','expression':f"{f['card_type']} 属于本期纳入产品",'expected_satisfied':True,'actual_applied_correctly':True},
 {'condition':'start_inclusive','expression':f"{f['valid_from']} <= {f['decision_date']}",'expected_satisfied':k['start_inclusive'],'actual_applied_correctly':True},
 {'condition':'planned_end_exclusive','expression':f"{f['decision_date']} < {f['valid_until']}",'expected_satisfied':k['planned_end_exclusive'],'actual_applied_correctly':True},
 {'condition':'early_end_exclusive_or_absent','expression':('ended_at 为空，仅无提前终止，仍有计划截止' if f['ended_at'] is None else f"{f['decision_date']} < {f['ended_at']}"),'expected_satisfied':k['early_end_exclusive_or_absent'],'actual_applied_correctly':True},
 {'condition':'conjunction_and_historical_date','expression':f"全部条件合取，使用指定判定日 {f['decision_date']}"+('，不替换为运行日 '+f['hypothetical_run_date'] if 'hypothetical_run_date' in f else ''),'actual_applied_correctly':True}
 ]
 results.append({'id':id,'verdict':verdict,'date_logic_verdict':'pass','source_traceability_verdict':'fail' if issues else ('pass_with_nonblocking_suggestion' if id=='DQ11' else 'pass'),'question':c['question'],'fixture':f,'actual_answer':a,'expected_valid_independently_derived':own['expected_valid_independently_derived'],'actual_validity_conclusion_matches':True,'manual_full_answer_assessment':manual_reason[n],'condition_checks':condition_checks,'supporting_sources':[{'source_id':'lin','messages':['MSG-03848','MSG-03854'],'supports':'本期产品范围'}, {'source_id':'chen','messages':['MSG-03886','MSG-03888','MSG-03890'],'supports':'开始含、计划结束不含、提前终止不含、空值、指定判定日'}, {'source_id':'test_dictionary','section':'cards / 覆盖说明','supports':'物理日期字段、日期粒度和合成测试边界，不用作端点规则依据'}],'source_role_check':{'date_rule_role_not_upgraded_to_it_or_policy':True,'scope_only_current_report':True,'unverified_policy_or_production_not_claimed_complete':True,'document_attribution_correct':not bool(issues)},'scope_checks':{'constructed_scenario_not_actual_record':True,'no_query_or_production_execution_claim':True,'no_extra_business_condition_changes_card_result':True,'known_rule_used_despite_missing_formal_material':True,'no_unauthorized_expansion_to_monthly_metric_result':True},'issues':issues,'nonblocking_notes':ns,'requires_user_business_decision':False,'protocol':proto[id]})
counts={'cases':len(results),'date_logic_pass':sum(c['date_logic_verdict']=='pass' for c in results),'full_answer_pass':sum(c['verdict']=='pass' for c in results),'full_answer_pass_with_nonblocking_suggestion':sum(c['verdict']=='pass_with_nonblocking_suggestion' for c in results),'full_answer_fail_requires_revision':sum(c['verdict']=='fail' for c in results),'full_answer_acceptable_including_nonblocking':sum(c['verdict']!='fail' for c in results),'needs_business_decision':0,'live_model_runs':protocol['live_runs'],'http_attempts':protocol['total_attempts']}
review={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'independent test review Agent','status':'completed_requires_source_attribution_revision','method':'先原材料/题设冻结判据，再预期与候选，再逐字阅读24份实际回答。日期结果由预先独立推导复核；完整语义判读非关键词评分。实际请求与原生答案逐一只读核验。','counts':counts,'failed_case_ids':[c['id'] for c in results if c['verdict']=='fail'],'nonblocking_case_ids':[c['id'] for c in results if c['nonblocking_notes']],'blocking_findings':[source_details],'source_attribution_followup':{'trigger':'主 Agent 请求核对04引用分级，未提供需要采纳的分数；此前第一遍“无阻断项”只是未完成来源复核的进度意见。','action':'重新逐句核原答复与04；保留原先 source-first-criteria 不变。','conclusion':'四题将04直接挂在产品断言出处，判完整回答需修订；DQ11的引用紧随报告适用范围句，具有可支持的指向，记拆分引用建议。正确日期或正确并列来源不抵消错误的明确文件归因。','not_changed':['原始题目','预期','候选','提示','模型实际答复','冻结判据']},'repair_boundary':'现有来源足以修正引用，无需本人重新选择业务规则。保留本轮4个完整回答失败及24个日期通过的真实记录；不覆写答复、不追加调用、不把编辑性纠正稿当新的模型通过证据。是否另开验证由主 Agent 根据剩余任务决定。','scope_limit':'仅24个单卡日期情境。未验证指标SQL/38指标数值、生产历史资格还原、正式制度、客户验收或模型采纳。','inputs_and_review_hashes':{str(p.relative_to(root)):sha(p) for p in [out/'source-first-criteria.json',out/'input-and-expectation-review.json',out/'execution-protocol-review.json',batch/'input/business_model.md',batch/'input/knowledge_prompt.txt',batch/'input/original_questions.json',batch/'input/reviewer_expectations.json']},'sources':criteria['sources'],'protocol_summary':{k:v for k,v in protocol.items() if k not in ['cases','input_checks','protected_checks']},'cases':results}
(out/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
lines=['# 日期边界24题独立实际问答评审','',f"完成时间（UTC）：{review['created_at']}",'','日期逻辑 **24/24 通过**；完整回答 **19 通过、1 通过但有非阻断建议、4 需修订**。4题共同问题是产品范围来源错挂，不是日期规则不明或需要业务取舍。真实运行24次、HTTP attempts 24次；无预期泄漏、工具使用或输入变更。','','## 分级依据与复核记录','','- 按先前冻结判据完整阅读，不以日期结论代替来源与范围检查。','- 04未列具体卡产品，原文是：“'+source_details['source_quote']+'”','- DY01、DY11、DY12、DQ12把04直接挂在产品纳入断言出处。小林消息或模型规则的正确引用不能抵消这一错误文件归因，完整回答判需修订。','- DQ11的邮件引用紧随“该口径只约束本期总部运营月报”；邮件有相应报告统计范围，故保留通过并建议拆开来源，不按关键词出现邮件就机械判错。','- 主 Agent 提出来源分级复核问题后，评审重新查原文，修正第一遍进度意见“无阻断项”；未改冻结判据、题目、预期、候选、提示或实际答复。','- 原来源可解决上述问题，不需要本人逐题确认业务规则；本轮不追加调用。','','## 逐题结论','','|题号|日期判断|完整回答|必要理由|','|---|---|---|---|']
labels={'pass':'通过','pass_with_nonblocking_suggestion':'通过（建议）','fail':'需修订'}
for c in results: lines.append(f"|{c['id']}|通过：{'有效' if c['expected_valid_independently_derived'] else '无效'}|{labels[c['verdict']]}|{c['manual_full_answer_assessment']}"+(' 来源把04挂到具体产品范围。' if c['issues'] else '')+'|')
lines+=['','## 需修订的来源证据','']
for c in results:
 for issue in c['issues']: lines +=[f"- **{c['id']}** 原文：“{issue['actual_quote']}”。产品范围应归于小林 MSG-03848/03854；04只支持统计选择，不含卡产品清单。"]
lines+=['','## 非阻断建议','']
for c in results:
 for note in c['nonblocking_notes']: lines +=[f"- **{c['id']} / {note['id']}**：{note['assessment']} 建议：{note['suggestion']}"]
lines+=['','## 原答复与逐题证据','','下列原文由原 output 逐字复制。结构化条件检查、来源消息和 output/run/request/answer/attempts 哈希均在同名 JSON；执行协议在 execution-protocol-review.json。']
for c in results:
 lines +=['',f"### {c['id']} — {labels[c['verdict']]}",'',f"日期条件检查：{c['manual_full_answer_assessment']} 判定日 {c['fixture']['decision_date']}；开始/计划结束/提前终止及其合取均已核对。",'',f"原输出：`{c['protocol']['output_path']}`；SHA-256 `{c['protocol']['output_sha256']}`。",f"原运行：`{c['protocol']['run_path']}`；SHA-256 `{c['protocol']['run_sha256']}`。",'','实际答复原文：','',c['actual_answer']]
lines+=['','## 结论范围','',review['scope_limit'],review['repair_boundary']]
(out/'review.md').write_text('\n'.join(lines)+'\n')
assert len(results)==24 and len({c['id'] for c in results})==24
for c in results: assert c['actual_answer']==json.loads((batch/'output'/f"{c['id']}.json").read_text())['actual_answer']
print(json.dumps(counts,ensure_ascii=False)); print('wrote review.md/json; original answer equality verified for all 24')
