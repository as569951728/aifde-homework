from pathlib import Path
import json,hashlib,datetime
b=Path('artifacts/w03/monthly-application-qa-20261107');o=b/'independent-review';c=json.loads((o/'source-first-criteria.json').read_text());cm={x['id']:x for x in c['cases']};qs=json.loads((b/'input/selected_questions.json').read_text())['cases'];audit=json.loads((o/'native-request-review.json').read_text());am={x['id']:x for x in audit['cases']};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
points={
'R01':[('月底时点和有效期','判定日2026-08-31；生效当天包含，计划结束2027-08-31不含，空终止仍受计划结束限制；计划/综合区间均正确。'),('最终纳入判断','来源与范围末段明确A月末有资格且8月10日有有效购买，因此应纳入，不要求购买当天有资格。'),('来源','产品归小林，日期归陈姐，月末资格及整月购买选择归实际给定04。')],
'R02':[('结论','直接“不纳入”；月末2026-08-31为计划结束当天，卡已无效且无其他卡。'),('前提与反例','8月10日有效购买不替代月末资格，无其他卡条件保持。'),('来源','04统计时点/购买人数，陈姐计划结束端点，小林产品范围分开引用。')],
'R03':[('A','全额退款净额为0，不是有效订单；有月末资格仍不纳入。'),('B','月末有资格但无订单，无有效购买不纳入。'),('条件与来源','明确两个必要条件，不把资格撤销；04购买人数+01有效订单直接支持。')],
'R04':[('主回应','说明现有口径不支持部分自然月直接计算，不把定义限制当单纯缺筛选条件。'),('日期保持','准确解释给定半开区间只覆盖8月10至30日；没有静默改请求。'),('后续','仅建议经补问改为[2026-08-01,2026-09-01)，月底8月31判资格；未声称实际计算。'),('来源范围','04完整月/全门店全渠道；补充产品时明确邮件本身未定具体产品，未错归04。')],
'R05':[('分月','7/8各购买账户1、复购0；不跨月凑两单为月内复购。'),('跨月唯一','1+1是月度累计而非唯一人数，给定A跨两月唯一账户为1；仍以按月展示为材料支持范围。'),('普通周报','使用03整月全门店月内口径，没有新增付费卡/资格过滤或年份。')],
'R06':[('维度限制','04不支持按成交门店或渠道拆8月付费复购率；字段存在不等于支持。'),('多月支持','7、8可以一起请求但逐月给出；各用当月月末资格及整月订单，不合成跨月率。'),('未知与建议','新的拆分口径仅列待确认建议，不宣称既有能力或已执行。')],
'R07':[('分母账户','B/C；A无有效订单不进，B一笔/C两笔均进。'),('分子账户','仅C；B一笔不进入分子；没有把C的2笔当2人。'),('旧稿修订','03首段明确已从全部注册改为同月有效购买，当前不得纳入A。'),('普通周报','仅用03指定口径，未追加付费筛选；人工条件和完整月/全门店保持。')]
}
quotes={
'R01':['判定日：2026-08-31','| 计划区间 | 2026-08-31 | 是 | 2027-08-31 | 否 |','8月10日又有有效购买，故应纳入'],
'R02':['不纳入','计划权益结束日为2026-08-31','该笔购买不使A进入8月付费购买人数'],
'R03':['A、B均不纳入','月末资格条件对A、B均满足，但不替代有效订单条件'],
'R04':['应说明不支持按该区间直接计算','只覆盖8月10日至8月30日','可补问并调整为完整自然月窗口2026-08-01至2026-09-01（不含）'],
'R05':['7月月内购买会员数为1，月内复购会员数为0','8月月内购买会员数也为1，月内复购会员数也为0','相加得到2只是两个月各自人数的合计，不是跨月去重人数'],
'R06':['现有口径下不能直接给出按成交门店或渠道拆分的8月复购率','分别给出7月和8月各自的月度复购率','不能把7、8月合并成一个跨月复购率'],
'R07':['分母“月内购买会员数”选B、C；分子“月内复购会员数”选C','现改为同月有效购买账户']}
notes={
'R01':['回答采用了单卡日期模板，但末段完整回答本题账户纳入且来源匹配，按预先判据通过；不能仅因展示形式多余判失败。当前只证明本题实际应用正确，不补回此前日期DQ10成绩。'],
'R05':['“A只有一人”宜改成“A只有一个账户”。本句紧接“跨月唯一账户”，全文按账户定义计数，未跨系统合并自然人；沿既有完整语义标准作为非阻塞措辞观察，不把该措辞等同自然人映射已验证。']}
rows=[]
for q in qs:
 id=q['id'];d=json.loads((b/'output'/f'{id}.json').read_text());a=d['actual_answer'];assert all(x in a for x in quotes[id]),id
 rows.append({'id':id,'verdict':'pass','input_track':q['input_track'],'original_question':q['question'],'fixed_materials':q['fixed_materials'],'required_point_review':[{'point':p,'status':'pass','actual':v} for p,v in points[id]],'actual_evidence_quotes':quotes[id],'source_refs':cm[id]['source_refs'],'negative_case_review':{'status':'pass','checks':cm[id]['failure_modes'],'assessment':'逐项查看完整实际答复，未发生所列实质错误；具体判定见required_point_review，不仅比较主结论或数值。'},'dimensions':{k:'pass' for k in ['对象身份与粒度','关系与时点','最终结论','理由与反例','题设与范围','引用与角色']},'issues':[],'nonblocking_notes':notes.get(id,[]),'actual_answer':a,'answer_text_sha256':am[id]['answer_text_sha256'],'output_path':str(b/'output'/f'{id}.json'),'output_sha256':am[id]['output_sha256'],'native_run':d['result']['run'],'native_run_sha256':am[id]['run_sha256'],'request_sha256':am[id]['request_sha256']})
r={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'/root/w03_qualification_qa_reviewer','status':'passed_for_this_fixed_material_batch_only','counts':{'pass':7,'needs_revision':0,'indeterminate':0},'input_track':'model_with_fixed_materials','cases':rows,'source_first_criteria_sha256':sha(o/'source-first-criteria.json'),'model_sha256':sha(b/'input/business_model.md'),'prompt_sha256':sha(b/'input/knowledge_prompt.txt'),'run_index_sha256':sha(b/'run_index.json'),'protocol':{'case_answers':7,'http_attempts':7,'http_successes':7,'length_retries':0,'semantic_retries':0,'independent_review_model_calls':0,'native_request_exact_designated_materials':'passed','protected_hashes':'passed'},'conclusion':'R01–R07七题一次实际材料应用均通过；R01保留日期模板但完整回答纳入，R05/R07普通复购未附加付费条件，范围题没有静默改窗口或维度。','limitations':['本组必须单列为7题指定材料应用；不能加到此前model_only成绩并宣称正文独立记忆通过。','已逐题核真实request只带该题指定材料，原文在question/settings/request保存；并非原生source_manifest独立资料节点。','本次成功不回改此前DQ10和P09模型原答失败，导师核对稿不计模型得分。','七题一次结果不代表其他未测题、SQL/指标数值独立对账、生产接入、客户验收或正式采用。','模型正文、现用提示/Skill、正式v0.4和原生proposal3未替换；无apply。'],'next_scope_assessment':'未发现必须先修的正文或本组业务语义缺陷；继续其他冻结题覆盖时仍按材料轨道分别准备，不能将当前来源应用正确等同完整模型通过。'}
(o/'review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');md=['# R01–R07月报材料应用独立评审','','原答：7 pass，0 needs_revision，0 indeterminate。输入轨道：model_with_fixed_materials。','',r['conclusion'],'','实际7次HTTP、各题一次成功，无重试或挑样；独立原生请求与正式保护hash核验通过。','',f'模型：`{r["model_sha256"]}`',f'提示：`{r["prompt_sha256"]}`',f'运行索引：`{r["run_index_sha256"]}`','','## 逐题','']
for row in rows:
 md += [f'### {row["id"]} — pass','','- 逐项判断：'+'；'.join(x['point']+'：'+x['actual'] for x in row['required_point_review']),'- 原答证据：'+'；'.join('“'+x+'”' for x in row['actual_evidence_quotes']),'- 原来源：'+'；'.join(row['source_refs']),f'- 原生运行：`{row["native_run"]}`',f'- 输出SHA256：`{row["output_sha256"]}`']
 for n in row['nonblocking_notes']:md+=['','非阻塞观察：'+n]
 md+=['']
md+=['## 保留边界','']+['- '+x for x in r['limitations']]+['',r['next_scope_assessment']]
(o/'review.md').write_text('\n'.join(md)+'\n');print(json.dumps({'counts':r['counts'],'run_index_sha256':r['run_index_sha256']},ensure_ascii=False))
