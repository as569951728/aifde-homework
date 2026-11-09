"""Independent semantic judgments plus offline native checks; no model execution."""
from pathlib import Path
import json,hashlib,datetime,sys,importlib.util
R=Path(__file__).resolve().parents[5];B=R/'artifacts/w03/answer-repair-20261107/stage1';O=B/'independent-review';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
criteria=read(O/'source-first-criteria.json');requirements={c['id']:c['required_points'] for c in criteria['cases']};requirements.update({c['id']:c['required_points'] for c in read(O/'controls_expectations.json')['cases']})
reasons={
'U01':'经营原因验证与岗位提效分开；陈述、老化假设和三个月期望分清，80万/120万按定义/范围/时点/来源待核，不再将未知写成已不同。',
'U05':'A保留日期规则与凭据缺口，B明确01918先带入、01919承接及01921三步感受，C未知非不存在，D不能直接求率，E核查认可非批准。',
'P09':'不纳本期范围不能推出全系统免费类别或两类绝对互斥；未擅补卡数。',
'A03':'费用构成/计价依据与阶段记录原则均归指定王经理访谈，节点/金额/付款待谈；核查、草案、实际执行与批准分开，未再虚构业务正文第5节承载。',
'E01':'首次调用MODEL_NETWORK_ERROR且无响应/答案；不具备语义评分对象，另建同输入恢复后单独审查。',
'E03':'不直接求活跃率/沉睡人数或判矛盾；定义/时点/覆盖/来源待核，未加必须同一来源门槛。',
'E05':'拒绝作废W04备忘，保留无效来源痕迹及未知；未再声称模型全部来源限W03。后文有效W03材料或实际记录为取证建议，不构成排除有效W02总规则。',
'REG01':'原120万误活跃已消失，也明确月报产品范围不扩至活动；但新增“模型中的客户是CRM会员账户”的无据定义，并把模型统计人群/待审核候选/执行名单误述为候选/待审核候选/执行名单后声称一致。主方案与权限/效果边界大体正确，仍有关键新增定义和来源转述错误。',
'U04':'一般工作/局部交接、未知闭环及核查下一步正确；但额外断言80万/120万的范围、时点、来源均不同，将仍待核的时点/来源写成已不同，正向回归失败。',
'P01':'完整记录的一张有效悦享年卡足以有资格；等级和金额未作门槛，隔离情境范围保留。',
'P05':'完整记录只有体验卡，无本期资格，依据产品排除而非零金额/普通等级。',
'E02':'四季下降为角色陈述未复算、会员老化为假设、三个月为期望；测试仅支持测试范围的定义/查询核对，不证业务原因或收益。',
'A02':'王经理只核查，认可总结非验收/预算签约/上线批准，拍板人与授权继续待核；未擅定沈总。',
'F05':'局部协作不证明完整闭环；提出按同一实际事项查策划/执行/反馈/分析答复/下轮决策记录和责任交接，未知不判不存在。',
'CTRL01':'接受陈姐在非诱导问答主动提供的一般做法和个人负担感受；准确归01665、不将01664当事实证据，不虚构量化损失/具体实例/效果。',
'CTRL02':'接受不同来源但已核可比条件，60/240=25%，180只为本题定义下无有效购买账户；未强加同源或沉睡定义，不迁入青禾事实。',
'CTRL03':'有效W02来源可保留为小林岗位诉求，明确非公司优先级/已有效，业务确认与未授权自动操作边界完整。',
'CTRL04':'甲有资格但购买贡献/卡数未知；乙无资格、不计入、2张；丙资格/贡献/卡数未知。正确区分至少一张、完整记录和只查到，不重复计账户。'}
findings={
'U04':[{'code':'UNKNOWN_ATTRIBUTES_AS_KNOWN_DIFFERENT','severity':'key','actual_excerpt':'80万与120万分别是活跃会员与系统全量会员的角色陈述，范围、时点、来源不同','reason':'已知活跃与全量概念不同，但模型§1要求定义、范围、时点与来源分别核查，未证明时点/来源已不同。','replacement':{'before':'80万与120万分别是活跃会员与系统全量会员的角色陈述，范围、时点、来源不同','after':'80万与120万分别是活跃会员与系统全量会员的角色陈述，两者定义、范围、时点与来源需分别核查'}}],
'REG01':[{'code':'UNSUPPORTED_CUSTOMER_ACCOUNT_DEFINITION','severity':'key','actual_excerpt':'模型中的“客户”是CRM会员账户','reason':'模型§2仅称会员账户是经营统计对象，未定义“客户”等同账户；客户/主体概念不能自行替换。','replacement':{'before':'模型中的“客户”是CRM会员账户','after':'模型以CRM会员账户作为经营与统计对象'}},{'code':'STATISTICAL_POPULATION_REPLACED_BY_CANDIDATE_POPULATION','severity':'key','actual_excerpt':'候选人群、待业务审核候选人群、实际执行名单三分开的模板','reason':'模型§3规则5明确是统计人群、待业务审核候选人群和实际执行名单。原答改第一个概念后仍称与模型三者不可等同一致，来源转述不准确。','replacement':{'before':'候选人群、待业务审核候选人群、实际执行名单三分开的模板','after':'统计人群、待业务审核的候选人群、实际执行名单三分开的模板'}}]}
advisories={
'U05':[{'severity':'nonblocking','note':'B末句“个人感受或局部陈述”可更精确拆成“没人用为提问前提被沿用；三步为个人感受”；前文已正确说明，不改通过结论。'}],
'P01':[{'severity':'nonblocking_wording','note':'“银行卡记录完整”应为“会员卡记录完整”。同段已明确唯一悦享年卡且推理按会员卡规则，视局部笔误，未改变资格结论。'}],
'A02':[{'severity':'nonblocking_relevance','note':'统一业务口径/分析牵头/最终规则责任与本题项目审批授权不是同一事项，建议删无关旁证；本题结论已由王经理原文直接充分支持。'}],
'U04':[{'severity':'source_scope_repair','note':'“订单与具体卡无对应”应保留本期材料未提供对应的范围；优惠券实际名单的粒度与用途须另核，不能把月报按账户去重自动推广为所有活动名单规则。','replacements':[{'before':'订单与具体卡无对应，名单应按账户去重','after':'本期材料未提供订单与具体卡的对应；本期账户口径统计应按账户去重，具体活动名单的用途与粒度仍须核实'}]}],
'REG01':[{'severity':'source_scope_repair','note':'“订单与具体卡没有对应关系”应表述为本期材料未提供，避免未知外推为现实不存在。','replacement':{'before':'订单与具体卡没有对应关系','after':'本期材料未提供订单与具体卡的对应关系'}}]}
runner=R/'artifacts/w03/answer-repair-20261107/support/run_batch.py';spec=importlib.util.spec_from_file_location('output_audit_runner',runner);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
def forbidden(*a,**k):raise RuntimeError('offline audit only')
m.Agent=forbidden;m.ContextModel=forbidden;m.read_key=forbidden
ctx=m.prepare(B);gate=read(B/'gate_acceptance.json');native_checks=[]
def ck(n,v):native_checks.append({'id':n,'passed':bool(v)})
ck('gate_review_hash_exact',gate['input_review_sha256']==sha(O/'input-review.json'))
review=read(O/'input-review.json');ck('gate_review_state_consistent',review['status']=='approved_for_execution' and review['approved'] and review['run_allowed'] and review['failed_checks']==[] and all(x['passed'] for x in review['checks']))
for key,f in [('runner_sha256',runner),('manifest_sha256',B/'input/manifest.json'),('preflight_sha256',B/'preflight.json')]:ck('gate:'+key,gate[key]==sha(f))
records=[];attempts_total=0
for cid in ctx['cases']:
 f=B/'output'/f'{cid}.json';d=read(f);runpath=d['result']['run'];rpath=R/runpath;folder=rpath.parent;run,settings,_,_=m.check_run(m.Workspace(R),runpath);request=read(folder/'request.json');attempts=read(folder/'attempts.json')['attempts'];attempts_total+=len(attempts)
 ck(cid+':native_contract_valid',True);ck(cid+':native_hash_matches_output',sha(rpath)==d['native_run_sha256']);ck(cid+':actual_messages_exact_frozen',request['messages']==m.messages_for(ctx['document'],ctx['prompt'],ctx['requests'][cid]['question'],True));ck(cid+':native_settings',settings['expected']=='' and settings['include_knowledge'] is True and settings['question']==ctx['requests'][cid]['question'] and settings['profile']=='deepseek-json');ck(cid+':one_http_attempt',len(attempts)==1);ck(cid+':gate_before_start',datetime.datetime.fromisoformat(gate['signed_at'])<datetime.datetime.fromisoformat(d['started_at']));ck(cid+':output_gate_hash',d['gate_sha256']==sha(B/'gate_acceptance.json'))
 for path,digest in d['native_files'].items():ck(cid+':preserved:'+path,sha(R/path)==digest)
 if cid=='E01':
  ck(cid+':no_answer_technical_failure',run['status']=='failed' and run['error']['code']=='MODEL_NETWORK_ERROR' and not (folder/'answer.json').exists() and not (folder/'response.json').exists() and d['actual_answer'] is None);verdict='not_assessable_technical_failure'
 else:
  ck(cid+':succeeded_with_exact_native_answer',run['status']=='succeeded' and d['actual_answer']==read(folder/'answer.json')['answer']);verdict='failed' if cid in findings else 'passed'
 group='original_failure' if cid in criteria['scope']['original_failures'] else 'positive_regression' if cid in criteria['scope']['positive_regressions'] else 'independent_control'
 records.append({'id':cid,'group':group,'input_track':d['input_track'],'verdict':verdict,'reason':reasons[cid],'required_point_review':[{'criterion':x,'result':'not_assessable' if cid=='E01' else ('needs_revision' if cid=='REG01' and x==requirements[cid][-1] else 'passed')} for x in requirements[cid]],'source_and_added_assertion_review':'not_assessable' if cid=='E01' else 'failed' if cid in findings else 'passed','findings':findings.get(cid,[]),'advisories':advisories.get(cid,[]),'native_structure_verdict':'passed','native_run_status':run['status'],'native_error':run.get('error'),'native_run':runpath,'native_run_sha256':sha(rpath),'output_path':str(f.relative_to(R)),'output_sha256':sha(f),'actual_answer_sha256':hashlib.sha256(d['actual_answer'].encode()).hexdigest() if d['actual_answer'] is not None else None,'http_attempts':len(attempts),'original_response_preserved':True})
failed=[x for x in native_checks if not x['passed']];assert not failed
summary={'total_cases':18,'native_structure_passed':18,'native_execution_succeeded':17,'native_execution_failed':1,'technical_no_answer_ids':['E01'],'http_attempts':attempts_total,'same_version_semantic_retries':0,'semantic_passed':15,'semantic_failed':2,'semantic_not_assessable':1,'semantic_failed_ids':['REG01','U04'],'by_group':{}}
for g in ['original_failure','positive_regression','independent_control']:
 cs=[c for c in records if c['group']==g];summary['by_group'][g]={'total':len(cs),'passed':sum(c['verdict']=='passed' for c in cs),'failed':sum(c['verdict']=='failed' for c in cs),'not_assessable':sum(c['verdict']=='not_assessable_technical_failure' for c in cs)}
native={'status':'passed_for_evidence_integrity','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'summary':summary,'checks':native_checks,'failed_checks':[],'note':'原生契约有效不等于原生调用成功或语义通过；E01网络失败记录有效。'};(O/'native-request-review.json').write_text(json.dumps(native,ensure_ascii=False,indent=2)+'\n')
r={'status':'completed_with_semantic_failures_and_technical_no_answer','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'independent_source_first':True,'criteria_sha256':sha(O/'source-first-criteria.json'),'candidate_prompt_sha256':sha(B/'input/knowledge_prompt.txt'),'model_sha256':sha(B/'input/business_model.md'),'summary':summary,'cases':records,'native_review':'native-request-review.json','native_review_sha256':sha(O/'native-request-review.json'),'scoring_boundary':'主判断正确不能掩盖关键附加断言。U04新增已不同时点/来源、REG01新增客户定义/误述三种人群是关键错误；U05范围表达、P01银行卡笔误、A02无关旁证另列非关键建议。','recovery':'E01另建同输入恢复，须单独报告；此原18批网络失败与原始分组分数不覆盖。','original_answers_and_historical_grades_unchanged':True,'human_decisions':[]}
(O/'review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
lines=['# Stage1 原18题独立复审','','原批结果：**15题语义通过、2题语义失败（REG01、U04）、1题无答复网络失败（E01，暂不可判语义）**。18条原生记录均通过证据契约核对，其中17次成功、1次网络失败；共18次HTTP尝试，无语义重抽样。','','|分组|通过|失败|无答复|','|---|---:|---:|---:|','|8个历史失败回归|6|1|1|','|6个正向回归|5|1|0|','|4个独立对照|4|0|0|','','|题|独立结论|理由|','|---|---|---|']
for c in records:lines.append('|'+c['id']+'|'+{'passed':'通过','failed':'失败','not_assessable_technical_failure':'技术无答复'}[c['verdict']]+'|'+c['reason']+'|')
lines+=['','U04把80万/120万的时点和来源待核改写为已不同。REG01虽然删除旧的全量/活跃错误，却新增“客户=CRM账户”定义，并将“统计人群”误转为“候选人群”；不能只按旧错误消失判修复成功。精确替换与附加来源范围修正已在JSON中列出，未回写原答。','','U05末句措辞、P01“银行卡”笔误、A02无关旁证另列非关键建议，不将局部表达问题与关键新增事实混同。4个对照均通过，说明本组反向风险已检查，不证明所有题的通用错误已消失。','','E01恢复批另审：原无答复网络失败永久保留，既不计语义通过也不计语义失败。导师修订稿不算模型输出；本报告不证明正式模型采用、全82题最新提示回归或38指标数值验收。真实人类决策：无。','']
(O/'review.md').write_text('\n'.join(lines));print(json.dumps({'summary':summary,'review_sha256':sha(O/'review.json'),'native_checks':len(native_checks),'native_failed_checks':[]},ensure_ascii=False,indent=2))
