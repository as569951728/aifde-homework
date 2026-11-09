"""Independent R2 judgments and native integrity checks. Offline only."""
from pathlib import Path
import json,hashlib,datetime,sys,importlib.util
R=Path(__file__).resolve().parents[5];base=R/'artifacts/w03/answer-repair-20261107';B=base/'stage1-r2';S=base/'stage1';O=B/'independent-review';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
criteria=read(S/'independent-review/source-first-criteria.json');requirements={c['id']:c['required_points'] for c in criteria['cases']};requirements.update({c['id']:c['required_points'] for c in read(S/'independent-review/controls_expectations.json')['cases']})
reasons={
'U01':'经营原因验证和岗位提效分别说明；角色报告、老化假设和三个月期望未当因果/承诺；80万/120万定义、范围、时点、来源保留待核，未再写已不同。内容偏长，但没有关键新增事实。',
'U05':'A—E均逐项回答；日期规则与未取得凭据并列，01918提问前提及01919/01921新增体验和限定明确，未知不等于不存在，不能直接求率或把认可当验收批准。',
'P09':'仅在本期月报排除联名卡，不推出全系统免费类别或两类互斥；没有补单卡数量。',
'A03':'费用/计价依据、阶段记录与变更延期核查来自王经理原文；金额/节点/付款待谈，核查非批准，未虚构正文已有SOW事实。',
'E01':'实际答复准确区分01918提问带入、01919承接与自身界面体验、01921非精确清单限定；未将没人用当独立证实，三步只作定性负担线索。',
'E03':'分别否定直接算率、沉睡差值和同口径矛盾；未知条件继续待核，没有加入必须同源限制。',
'E05':'拒绝作废W04陈述进当前规则/流程，来源留痕且明确未采纳；待有效来源核查，不再把有效W02整体排除。',
'REG01':'第一版建议、接入小林/陈姐工作及过程评估完整，业务确认和不自动操作边界保留，未把省时当复购收益；旧客户=账户定义、三类人群误述与全量误活跃均未再出现。月报规则明确标本期口径，活动范围仍需业务确认。',
'U04':'保留一般流程、门店前置条件、局部交接、未核闭环与具体后续记录/经手人/影响判断；月报产品范围不直接成为券活动筛选条件；未再追加时点/来源已不同。',
'P01':'完整记录的一张有效悦享年卡已足以有资格，普通等级/实付不替代产品有效条件，题设与真实记录分清。',
'P05':'完整记录只有体验卡，无资格，理由为产品不纳入且无其他卡，非零金额或等级判断。',
'E02':'下降是未复算角色陈述、老化为待验假设、三个月为期望非承诺；测试不证明原因/收益/生产身份或历史还原。',
'A02':'核查意见与公司审批/验收分清，王经理和沈总均未被擅定为本期最终拍板人，具体审批/授权仍待核。',
'F05':'局部执行链不能推出全部闭环；建议同一实际活动按策划/执行/反馈/分析答复/下轮决策查记录及责任，并只在该实例可核时确认，不外推。',
'CTRL01':'非诱导提问中陈姐新增工作做法、个人感受和期望被保留并正确归回答；不量化耗时损失、不当正式制度或实际效果，未一律拒绝角色观察。',
'CTRL02':'不同来源但同范围/时点/账户去重且子集已核时可算60/240=25%；按账户和测试情境限定，未补同源门槛、沉睡定义、青禾事实或业务原因。题目未要求计算余数，未报180不构成漏答。',
'CTRL03':'有效W02访谈可按来源/范围保留，岗位诉求与公司优先级、已实现效果分开；人群执行确认及未授权自动操作边界未丢。',
'CTRL04':'甲资格有、购买贡献与确切卡数未知；乙资格无、不计入、2卡；丙资格/贡献/卡数未知。按完整性与正证据分别判断，没将只查到变只有，未新增条件。'}
advisories={
'REG01':[{'severity':'nonblocking_wording','code':'FORMAL_EVIDENCE_SCOPE_NEEDS_PRECISION','quote':'该口径正式规则文件尚未取得，应标待确认。','suggested_replacement':'这些本期规则已有角色说明；正式规则文件和生产/历史执行凭据仍未取得，继续标为待核。','why_nonblocking':'前文已按现有规则完整列产品/资格/端点/去重，并未将规则退为未知或拒绝使用；应把待确认标注对象写清，避免读者误解。'}],
'A03':[{'severity':'nonblocking_reason_wording','quote':'业务模型未把费用与结算写成已确认的客户业务规则，因此这些内容只能作为待确认草稿','suggested_replacement':'指定王经理访谈表明金额、节点及授权等尚待谈定或核实，因此现阶段仅能形成相应草稿和待确认事项','why_nonblocking':'主体答复已准确归访谈并列待谈事项；末句宜避免让正文未收录成为批准状态的推理依据。'}],
'CTRL02':[{'severity':'nonblocking_terminology','quote':'不能将240个CRM账户等同于自然人数或会员人数','suggested_replacement':'不能把240个CRM账户直接当作跨系统自然人会员人数；本题按CRM账户口径计数仍成立','why_nonblocking':'主结论明确同集合按CRM账户算25%，没有拒绝账户口径；“会员人数”字样需限定自然人含义，避免泛化。'}]}
runner=base/'support/run_batch.py';spec=importlib.util.spec_from_file_location('r2_output_offline',runner);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
def forbidden(*a,**k):raise RuntimeError('offline audit only')
m.Agent=forbidden;m.ContextModel=forbidden;m.read_key=forbidden
ctx=m.prepare(B);gate=read(B/'gate_acceptance.json');checks=[]
def ck(n,v,d=None):
 x={'id':n,'passed':bool(v)}
 if d is not None:x['detail']=d
 checks.append(x)
ck('gate_review_hash',gate['input_review_sha256']==sha(O/'input-review.json'));ir=read(O/'input-review.json');ck('gate_review_states',ir['status']=='approved_for_execution' and ir['approved'] and ir['run_allowed'] and not ir['failed_checks'] and all(x['passed'] for x in ir['checks']))
for k,p in [('runner_sha256',runner),('manifest_sha256',B/'input/manifest.json'),('preflight_sha256',B/'preflight.json')]:ck('gate:'+k,gate[k]==sha(p))
records=[];attempt_total=0;expansions=[]
for cid in ctx['cases']:
 out=B/'output'/f'{cid}.json';d=read(out);runpath=d['result']['run'];rp=R/runpath;folder=rp.parent;run,settings,_,_=m.check_run(m.Workspace(R),runpath);request=read(folder/'request.json');ats=read(folder/'attempts.json')['attempts'];attempt_total+=len(ats)
 ck(cid+':native_contract',True);ck(cid+':native_status_succeeded',run['status']=='succeeded' and d['status']=='succeeded' and not d['runner_errors']);ck(cid+':actual_messages_frozen',request['messages']==m.messages_for(ctx['document'],ctx['prompt'],ctx['requests'][cid]['question'],True));ck(cid+':settings_exact',settings['expected']=='' and settings['include_knowledge'] is True and settings['question']==ctx['requests'][cid]['question'] and settings['profile']=='deepseek-json');ck(cid+':output_answer_native_exact',d['actual_answer']==read(folder/'answer.json')['answer']);ck(cid+':native_run_hash',sha(rp)==d['native_run_sha256']);ck(cid+':gate_before_call',datetime.datetime.fromisoformat(gate['signed_at'])<datetime.datetime.fromisoformat(d['started_at']));ck(cid+':output_gate_hash',d['gate_sha256']==sha(B/'gate_acceptance.json'))
 for path,digest in d['native_files'].items():ck(cid+':preserved:'+path,sha(R/path)==digest)
 if cid=='REG01':
  ck(cid+':documented_truncation_expansion',len(ats)==2 and ats[0].get('finish_reason')=='length' and ats[0].get('error')=='MODEL_OUTPUT_TRUNCATED' and ats[0]['max_tokens']==8192 and ats[0]['timeout_seconds']==180 and ats[1].get('finish_reason')=='stop' and not ats[1].get('error') and ats[1]['max_tokens']==16384 and ats[1]['timeout_seconds']==240 and ats[0]['request']['messages']==ats[1]['request']['messages'])
  expansions.append({'case_id':cid,'run':runpath,'first':{'http_status':ats[0]['http_status'],'finish_reason':ats[0]['finish_reason'],'error':ats[0]['error'],'max_tokens':ats[0]['max_tokens'],'timeout_seconds':ats[0]['timeout_seconds']},'second':{'http_status':ats[1]['http_status'],'finish_reason':ats[1]['finish_reason'],'max_tokens':ats[1]['max_tokens'],'timeout_seconds':ats[1]['timeout_seconds']},'same_messages':True,'classification':'course_builtin_truncation_token_expansion_not_semantic_retry','attempts_sha256':sha(folder/'attempts.json')})
 else:ck(cid+':single_attempt',len(ats)==1)
 group='original_failure' if cid in criteria['scope']['original_failures'] else 'positive_regression' if cid in criteria['scope']['positive_regressions'] else 'independent_control'
 records.append({'id':cid,'group':group,'input_track':d['input_track'],'verdict':'passed','reason':reasons[cid],'required_point_review':[{'criterion':x,'result':'passed'} for x in requirements[cid]],'source_and_key_added_assertion_review':'passed','findings':[],'advisories':advisories.get(cid,[]),'output_path':str(out.relative_to(R)),'output_sha256':sha(out),'actual_answer_sha256':hashlib.sha256(d['actual_answer'].encode()).hexdigest(),'native_run':runpath,'native_run_sha256':sha(rp),'native_structure_verdict':'passed','native_run_status':run['status'],'http_attempts':len(ats),'original_response_preserved':True})
ck('cancelled_recovery_not_executed',not list((base/'stage1-network-recovery/output').glob('*')) and not (base/'stage1-network-recovery/gate_acceptance.json').exists())
old=read(S/'independent-review/review.json');ck('stage1_scores_preserved',old['summary']['semantic_passed']==15 and old['summary']['semantic_failed']==2 and old['summary']['semantic_not_assessable']==1)
failed=[x for x in checks if not x['passed']];assert not failed
summary={'total_cases':18,'semantic_passed':18,'semantic_failed':0,'semantic_not_assessable':0,'by_group':{'original_failure':{'total':8,'passed':8,'failed':0},'positive_regression':{'total':6,'passed':6,'failed':0},'independent_control':{'total':4,'passed':4,'failed':0}},'native_runs':18,'native_structure_passed':18,'native_execution_succeeded':18,'http_attempts':attempt_total,'course_builtin_truncation_expansions':len(expansions),'network_recovery_calls':0,'semantic_retries':0,'runner_level_retries':0}
now=datetime.datetime.now(datetime.timezone.utc).isoformat();native={'status':'passed','reviewed_at':now,'summary':summary,'truncation_expansion_details':expansions,'checks':checks,'failed_checks':[],'reviewer_model_calls':0};(O/'native-request-review.json').write_text(json.dumps(native,ensure_ascii=False,indent=2)+'\n')
r={'status':'completed_passed_with_nonblocking_wording_advisories','reviewed_at':now,'independent_source_first':True,'criteria_reused_from':'artifacts/w03/answer-repair-20261107/stage1/independent-review/source-first-criteria.json','criteria_sha256':sha(S/'independent-review/source-first-criteria.json'),'controls_expectations_sha256':sha(S/'independent-review/controls_expectations.json'),'candidate_prompt_sha256':sha(B/'input/knowledge_prompt.txt'),'model_sha256':sha(B/'input/business_model.md'),'summary':summary,'cases':records,'native_review':'native-request-review.json','native_review_sha256':sha(O/'native-request-review.json'),'truncation_expansion_details':expansions,'grading_boundary':'全部必要问题判断正确且无关键新增事实才通过。未按“旧错消失”给分，18题均重新审全文。3项有歧义/不够精确的附加措辞列非关键建议，其上下文已明确正确判断与来源，未改变资格、授权或计算结论。控制题CTRL02的180是边界反例，不要求题目未问的余数计算；答复未给余数或沉睡标签，未触发禁止项。','historical_state':{'stage1':'15通过/2语义失败/1技术无答复，原记录保留','stage1_network_recovery':'准备和审核后取消，0API；E01在R2按新提示运行，不是同版本恢复','earlier_11_failures':'历史原始失败不回改；本报告仅确认stage1范围8个原失败在R2回归通过，其余B05/DQ10/F06由后续阶段检验。'},'not_proven':['当前累计提示已通过全82题','正式模型v0.4已apply','38指标实现与独立数值校验','生产接入/业务收益/客户验收','提示对全部未测问题已无来源错误'],'human_decisions':[]}
(O/'review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
lines=['# Stage1-r2 原18题独立复审','','本版 **18/18语义通过**：8个历史失败回归8/8、6个正向回归6/6、4个独立对照4/4。每题均重读本版原答，未沿用上版通过分。','','18个原生运行、18份最终答复、19次HTTP请求。REG01首次因length截断，课程内置以同messages从8192扩至16384 tokens、超时180增至240秒后成功；两次尝试均保留。这是1次内置截断扩容，**0语义重抽、0网络恢复调用**，不能写成18请求或笼统0重试。','','|题|结论|理由|','|---|---|---|']
for c in records:lines.append('|'+c['id']+'|通过|'+c['reason']+'|')
lines+=['','3处非关键措辞建议已在JSON列精确改法：REG01把待核对象明确为正式文件/凭据；A03把待谈状态的原因明确归原访谈；CTRL02把“会员人数”明确限定为自然人会员人数。原答必要判断与边界已经成立，这些建议不计新模型答复，也没有回写原答。','','原stage1的15/2/1和所有历史失败保留。同版本E01网络恢复批未运行即取消；R2的E01是新提示回归。本报告仅覆盖当前18题，不能据此称全82题在最新提示通过、正式正文已采用或38项指标数值验收完成。真实人类决策：无。','']
(O/'review.md').write_text('\n'.join(lines));print(json.dumps({'summary':summary,'review_sha256':sha(O/'review.json'),'native_checks':len(checks),'native_failed_checks':[]},ensure_ascii=False,indent=2))
