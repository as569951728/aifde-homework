from pathlib import Path
import json,hashlib,datetime
b=Path('artifacts/w03/source-refined-qualification-qa-20261107');o=b/'independent-review';old=Path('artifacts/w03/qualification-qa-20261106/independent-review');criteria=json.loads((old/'source-first-criteria.json').read_text());cm={x['id']:x for x in criteria['cases']};selected=json.loads((b/'input/selected_questions.json').read_text())['cases'];audit=json.loads((o/'native-request-review.json').read_text());am={r['id']:r for r in audit['cases']};rows=[]
points={
'U02':[('七项概念','账户/卡/订单是对象记录，等级与资格分离，活跃未知，复购率为群体指标；账户非自然人。'),('规则与行为','同卡范围+有效期、paid净实付>0，资格不推出购买或活跃。'),('同账户例子','普通账户+有效悦享卡+体验卡+全退订单；有资格而该支付订单非有效购买；明确为构造例。'),('范围与引用','资格归小林，日期归陈姐，正文未整组降级成未确认学员选择。')],
'U03':[('关系基数','账户0至多卡/订单；卡订单各归一账户；一账户一个归属店、一订单一个成交店。'),('门店','成交归B，A仅账户归属。'),('关联未知','不能经共同账户确定具体用卡，不外推生产身份已统一。')],
'P01':[('资格与原因','有资格；有效悦享卡满足，普通等级/购卡金额不影响。'),('前提与模板','直接接受判定日有效；未给具体日期不妨碍资格结论，没有套日期模板判待核。')],
'P02':[('资格与原因','有资格；有效家庭季卡不遗漏，普通等级与3000分不替代。'),('前提','完整人工记录和已知有效状态保持。')],
'P03':[('资格与原因','无资格；唯一悦享卡失效，金卡/10000分不能补足。'),('完整记录','没有其他卡可提供资格，未把完整事实变未知。')],
'P04':[('资格与原因','无资格；有效且收费联名卡产品不纳入，等级/金额不能补救。'),('范围','仅本期自营月报，人工情境不是生产事实。')],
'P05':[('资格与原因','无资格；体验卡不在产品范围，不因0分/普通等级而排除。')],
'P06':[('资格与原因','有资格；有效家庭季卡满足，0分不能构成额外门槛。')],
'P07':[('未知与不足','不能判有或无；卡记录未提供不能当无卡。'),('需要信息','列卡类型、开始/结束/提前终止、判定日，正确说明同一卡及端点。')],
'P08':[('范围','不能推广历史/合作方，本期口径不改其他报表。'),('下一步','分报表核对象、产品、判定日、窗口、渠道及来源，历史保原定义、合作方单独核。')],
'P09':[('两项主结论','不具本期资格不推出全系统免费；两类说法不证明绝对互斥。'),('原来源范围','系统重叠仍缺记录，模型不建立互斥；无擅自定系统分类。')],
'C01':[('数与粒度','1有资格账户、2不同有效订单，O1/O2各计一次。'),('防关联重复','先账户资格标记，卡/订单通过账户联系，不用卡作订单计数键，不反推用卡。')],
'C02':[('存在条件','有效家庭季卡即可；失效悦享与不纳入联名不否定。')],
'C03':[('同一卡','不能拼接；失效悦享和有效联名分别不满足完整条件，完整集合无合格卡。'),('来源/前提','小林03848/03854与陈姐03886/03888分开；未追加生产核验才可答。')],
'C04':[('完整无卡','直接无本期资格，明确缺判定日不影响完整无卡题设判断。'),('缺表未知','未提供不是无卡，不能因此判无资格；不推账户不存在或永久无资格。')],
'C05':[('三状态','月末有资格、当月无有效购买、活跃待核；彼此不可替代。'),('来源','资格归小林/模型，有效购买归订单/财务材料，活跃未知归01719/01754。')],
'C06':[('混合产品多卡','1账户、2订单，不把O1/O2复制4笔或去重成1笔。'),('关系','账户作为资格与订单的桥，不分配具体卡，不制造实际用卡关系。')]
}
quotes={
'U02':['账户不等于跨系统自然人','那笔支付订单不是有效购买；也不能据此推出A活跃或会复购','日期端点来自陈姐'],
'U03':['一个账户可以对应0至多张卡','应归B店，而不是A店','不能据订单反推卡'],
'P01':['账户A在判定日有付费资格','仅采用题设“判定日有效”的给定状态'],
'P02':['账户A在判定日具有本期总部月报口径下的付费资格','唯一卡为家庭季卡'],
'P03':['不具有本期总部月报口径下的付费资格','没有其他卡可提供资格'],
'P04':['不满足本期总部月报的产品范围','金卡等级和实付金额不能补救'],
'P05':['只有一张体验卡','普通等级和实付金额0都不是本判断的替代依据'],
'P06':['卡实付金额为0均不能替代卡类型与有效状态判断，也不构成排除条件'],
'P07':['“金卡”本身不足以支持“有资格”或“无资格”','判定日不早于生效日、早于计划结束日'],
'P08':['该口径明确只约束本期总部运营月报，不改其他报表','逐个报表核对统计对象'],
'P09':['账户A只有一张有效异业联名卡','不能推出A在全系统属于“免费注册”类别','现有“两类会员”的说法不能证明系统绝对互斥'],
'C01':['应计 1 个有资格账户、2 笔有效订单','卡与订单均只通过账户关联'],
'C02':['均不影响上述判断'],
'C03':['不能把不同卡的条件拼接判断','该结论限于本期月报口径和题设完整记录'],
'C04':['没有给出具体判定日并不妨碍这一结论','卡表未提供则是证据缺失，不能把缺失当作无卡'],
'C05':['本期月末付费资格：有','当月有效购买：无','活跃状态：待核'],
'C06':['应计1个有资格账户、2笔有效订单','不能把两笔不同订单去重成一笔']}
notes={
'U02':['概念表仍沿用字典与多条访谈的成组引用；CRM物理字段/账户粒度直接证据是字典，旧会员两类消息主要提供业务背景。后续宜进一步精确分配，当前未把特定字段错误说成某角色原话，按既有标准不单因背景来源冗余判失败。'],
'C01':['“再按订单唯一标识关联账户”宜改清为“通过账户标识关联、按订单唯一标识计一次”。全文随后明确卡/订单只通过账户关联且不重复订单，故不按歧义片段判实质关联错误；本题也没有执行SQL。'],
'C04':['开头“若…覆盖A且账户标识能够匹配”是题设的适用边界，后文明说完整无卡足以推无资格，没有重加生产核验才回答的门槛；与此前C04判准一致。']}
for case in selected:
 id=case['id'];d=json.loads((b/'output'/f'{id}.json').read_text());a=d['actual_answer'];assert all(q in a for q in quotes[id]),id
 issues=[]
 if id=='P09':issues=[{'id':'P09-unsupported-card-count','severity':'局部题设事实增加，主结论未错','quote':'题设仅给定：账户A只有一张有效异业联名卡','original_question_fragment':'账户A只有有效异业联名卡','reason':'原题只限定所持有效卡产品，未限定卡数。答案把“一张”写成题设事实，属于无依据增加对象数量；即使分类结论不受影响，也未满足整份答案前提保持。','minimal_correction':'删除“一张”，保留其余答案；如另存核对稿必须不覆盖原答、不回改本次得分。','requires_business_decision':False}]
 dims={k:'pass' for k in ['对象身份与粒度','关系路径','主要结论','理由与反例','题设与范围','角色与引用']}
 if issues:dims['题设与范围']='needs_revision'
 rows.append({'id':id,'verdict':'needs_revision' if issues else 'pass','question':case['question'],'fixture':case.get('fixture'),'criteria_ref':str(old/'source-first-criteria.json')+'#'+id,'required_point_review':[{'point':p,'status':'pass','actual':v} for p,v in points[id]],'actual_evidence_quotes':quotes[id],'source_refs':cm[id]['source_refs'],'dimensions':dims,'issues':issues,'nonblocking_notes':notes.get(id,[]),'actual_answer':a,'actual_answer_sha256':am[id]['actual_answer_sha256'],'output_path':str(b/'output'/f'{id}.json'),'output_sha256':am[id]['output_sha256'],'native_run':d['result']['run'],'native_run_sha256':am[id]['run_sha256'],'native_request_sha256':am[id]['request_sha256']})
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();counts={k:sum(r['verdict']==k for r in rows) for k in ['pass','needs_revision','indeterminate']}
report={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'batch':str(b),'reviewer':'/root/w03_qualification_qa_reviewer','status':'needs_revision','counts':counts,'main_conclusion_correct':17,'model_sha256':sha(b/'input/business_model.md'),'prompt_sha256':sha(b/'input/knowledge_prompt.txt'),'run_index_sha256':sha(b/'run_index.json'),'runtime':{'case_answers':17,'http_attempts':17,'http_successes':17,'extra_review_model_calls':0,'length_retries':0,'semantic_retries':0,'request_isolation':'passed','protected_hashes':'passed'},'rubric':'沿用原source-first判据、原题/fixture/预期及读首批实际答案前的U02概念门槛校准；未把旧17/17迁移到新版本。逐份读新原答，并分别判断完整前提、关系、来源及主结论。','cases':rows,'model_text_assessment':'本17题没有发现必须先阻断后续覆盖的业务模型正文规则缺陷；本次原答失败是P09无依据增加卡数，删除“一张”即可形成另存核对稿。新来源层次可继续用于后续材料应用测试，但不能把本批通过范围扩展为未测规则。','supervision_boundary':['审查使用独立来源先行判据及另一次上下文判读，不等于业务权威批准或未见题泛化证明。','冻结输入及实际请求核验可证明本次喂入内容与记录一致；不能自动证明业务语义正确，故P09原答保留失败。','新增日期空白模板未误触发本17题；本批不含日期边界运算的重新验证。','前日期批DQ10原答失败继续保留，导师核对稿不计模型成绩；本批不能关闭DQ10。','正式v0.4、原生proposal3、现用Skill/提示未替换；无apply、指标SQL/数值对账、客户验收或课程提交。','P09可由现有题面直接解决，不需用户作真实业务裁决；不新增模型调用重抽样。']}
(o/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
md=['# 来源细化候选：17题实际问答独立评审','','原答结果：16 pass，1 needs_revision（P09），0 indeterminate。17题主结论均正确，但P09无依据增加卡数量，完整答案未通过。','',f'实际运行：17题、17次HTTP成功，无长度或语义重试；审查未调用模型。原生请求隔离和正式保护hash均通过。', '',f'模型：`{report["model_sha256"]}`',f'提示：`{report["prompt_sha256"]}`',f'运行索引：`{report["run_index_sha256"]}`','','## 逐题','']
for r in rows:
 md += [f'### {r["id"]} — {r["verdict"]}','','- 判据与实答：'+'；'.join(x['point']+'：'+x['actual'] for x in r['required_point_review']),'- 原答证据：'+'；'.join('“'+q+'”' for q in r['actual_evidence_quotes']),'- 来源：'+'；'.join(r['source_refs']),f'- 输出 SHA256：`{r["output_sha256"]}`',f'- 原生运行：`{r["native_run"]}`']
 for i in r['issues']:md+=['','**原答问题：**'+i['reason'],'','最小修正：'+i['minimal_correction']]
 for n in r['nonblocking_notes']:md+=['','非阻塞观察：'+n]
 md+=['']
md+=['## 正文与监督边界','',report['model_text_assessment'],'']+['- '+x for x in report['supervision_boundary']]
(o/'review.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'counts':counts,'main_conclusion_correct':17,'files':['review.md','review.json']},ensure_ascii=False))
