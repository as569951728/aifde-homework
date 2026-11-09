from pathlib import Path
import json,hashlib,datetime
root=Path('/Users/chenzhaowen/czw-code/AIFDE'); audit=root/'W03/实操工程/artifacts/w03/source-semantics-audit-20261108'; out=audit/'reviews/model_and_artifact'
q=json.loads((audit/'input/original_questions.json').read_text()); ids=json.loads((audit/'scope.json').read_text())['groups']['model_and_artifact']; cases={x['id']:x for x in q['cases']}
source_dir='W03/实操工程/artifacts/w03/w02_revision_20261104/artifacts/w02/sources/'
sources={}
for p in (root/source_dir).glob('*.json'):
 d=json.loads(p.read_text())
 for m in d['messages']: sources[m['id']]={'path':str(p.relative_to(root)),'speaker':m['speaker'],'content':m['content']}
for p in (root/'W03/实操工程/artifacts/w02/sources').glob('W3-interview-*.json'):
 d=json.loads(p.read_text())
 for m in d['messages']: sources[m['id']]={'path':str(p.relative_to(root)),'speaker':m['speaker'],'content':m['content']}
groups={
'goals':{'refs':['MSG-01719','MSG-01731','MSG-01733','MSG-01737','MSG-01739','MSG-03856','MSG-01925','MSG-01951'],'criterion':'复购下降为角色陈述，未重算；会员老化为沈总个人判断，无因果证据；三个月见效为期望。MSG-01731明确到时拿什么数字、按什么口径现在还没定，不能退回为仅未知。提效未量化；小林优先人群和时期在MSG-03856明确还没定。两种目标分别观察，方案/查数/核查进展不能代替已执行与业务收益。'},
'population':{'refs':['MSG-01615','MSG-01679','MSG-01742','MSG-01719','MSG-01744','MSG-01754'],'criterion':'付费卡、免费注册需分范围，但系统绝对互斥未证实；活跃定义未知，不以有卡/有购买/等级推定。80万活跃与120万系统全量来源和口径不同，既不能相减/相除，也不能断言同口径冲突。'},
'products':{'refs':['MSG-03847','MSG-03848','MSG-03853','MSG-03854','MSG-03870'],'criterion':'小林明确本期总部月报纳入悦享年卡和家庭季卡，排除收费异业联名卡与体验卡；一张范围内有效卡即可，按账户去重。等级/支付金额不替代资格；完整无符合卡可否定本期资格，未给卡记录则未知。不能从不纳入本期推出全系统免费身份。此为已获业务规则，不是学员建模选择；未得正式文件不抹去访谈规则。'},
'dates':{'refs':['MSG-03849','MSG-03850','MSG-03873','MSG-03875','MSG-03885','MSG-03886','MSG-03887','MSG-03888','MSG-03889','MSG-03890'],'criterion':'陈姐在提问限定的两类卡范围下，新增生效当天有效、计划结束/提前终止当天无效、空终止不等于无限期、按所需判定日检查、账户归并规则。不能将这些归给小林/老周/字典/邮件，不能因早期不掌握或无正式文件改为全未知；也不能把日期规则说成学员建模选择。03885的本期月末前提不是陈姐独立提出月末口径。'},
'monthly':{'refs':['MSG-03867','MSG-03868','MSG-03869','MSG-03870'],'material':'W03/实操工程/materials/w03/04_本期统计确认邮件.md','criterion':'04邮件是本期六项月报月末选账户、当月全渠道全门店有效订单、完整月及按月展示的统计选择。小林03868/03870确认有资格且当月有有效购买及月末才生效也纳入此前有效购买。选择有客户来源，不能称纯学员自定。卡产品/日期端点另由角色说明。'},
'data':{'refs':['MSG-03875','MSG-03877','MSG-01937','MSG-01938','MSG-01942'],'material':'W03/实操工程/materials/w03/05_数据字典.md','criterion':'账户、卡、订单、门店及字段关系来自本期干净合成测试字典，只适用其覆盖。账户不等于自然人，home_store_id和orders.store_id分开，未提供订单到具体卡关联不等于生产不存在。W02购买时有效为学员候选分析规则、老周待业务确认，不能升为现行规则；生产历史还原仍未知。'},
'effective_purchase':{'refs':[],'material':'W03/实操工程/materials/w03/01_订单日报说明.md','other_materials':['W03/实操工程/materials/w03/02_财务邮件.md','W03/实操工程/materials/w03/03_会员运营周报.md'],'criterion':'有效购买依据paid且实付减累计退款>0，与支付状态/资格/活跃分开。统计粒度是订单、账户；多卡不能复制订单。当前月内复购分母为同月有效购买账户，非全部注册会员；规则仅本期测试覆盖。'},
'workflow':{'refs':['MSG-01623','MSG-01635','MSG-01637','MSG-01641','MSG-01665','MSG-01667','MSG-01681','MSG-01913','MSG-01915','MSG-01925','MSG-01927','MSG-01945','MSG-01947','MSG-01949','MSG-01951','MSG-01953','MSG-03856','MSG-03858','MSG-03860','MSG-03862','MSG-03886','MSG-03888'],'criterion':'小林一般工作步骤与三种活动类型已知；具体活动/名单/条件/经手与结果未取得，不能说公司没有/尚未决定该流程。陈姐与小林局部交接已知，反馈分析接收、答复返店、下一轮闭环未知；不得抹掉已知交接或说没有闭环。门店范围/工作量/答复责任/工作记录及人员执行需确认，影响考核先澄清。人群需业务确认，不能自动发券/联系/改记录。整理是拟议支持方向，不是已运行/获授权/已见效。'},
'coupon':{'refs':['MSG-01648','MSG-01752','MSG-01665'],'criterion':'发放与核销分环节；发放记录不证明使用资格、核销、购买或复购改善；券适用限制需具体规则/配置/使用记录。未给限制记录不等于没有限制。'},
'invalid':{'refs':[],'material':'W03/实操工程/AGENTS.md','criterion':'W04 meeting 5e112925-9605-5362-b908-1ef8849d9c5f已作废，只归档。题干明确唯一依据失效的60天/每周一/排员工/勿扰规则不入当前模型；这不证明青禾不存在相应流程，状态为缺有效依据待核。'},
'artifacts':{'refs':['MSG-01937','MSG-01938','MSG-01731','MSG-03848','MSG-03886'],'material':'W03/实操工程/artifacts/w03/w02_revision_20261104/docs/w02/business_model.md','criterion':'保留v0.4经营双目标、角色参与边界、权限和未知；可按W03来源更新本期关系/产品/日期规则，历史与生产未知保留。正文对象/规则/局部流程可读，证据取舍和测试记录另存；设计属性不冒称源字段，业务规则不降为设计。当前冻结正文是20261108候选，不是正式v0.4；本次只专项审来源/状态/分类，不执行原T全量验收。'}
}
mapids={
'U01':['goals','workflow'],'U02':['population','products','data','effective_purchase'],'U03':['data'],'U04':['workflow'],
'P07':['products','population'],'P08':['products'],'P09':['products','population'],
'C01':['products','dates','data'],'C02':['products'],'C03':['products'],'C04':['products'],'C05':['products','monthly','population'],'C06':['products','dates','data'],
'F03':['workflow'],'F04':['workflow'],'F05':['workflow'],'F06':['goals','workflow'],'F09':['coupon'],
'E02':['goals'],'E03':['population'],'E05':['invalid'],'T01':['artifacts'],'T02':['artifacts','data','products','dates','monthly','workflow'],'T03':['artifacts','data','products','dates','monthly'],
'REG01':['goals','workflow'],'REG02':['goals','workflow','data']}
notes={
'U01':'原因验证与岗位减负分开；检查角色陈述/假设/期望/未定/未知及当前可观察边界。',
'U02':'属性并存例必须是例子，不写客户实有账户；付费、等级、活跃、购买不能相互推出。',
'U03':'成交统计归B；本期一账户多卡、多订单，一店多账户和订单；订单用哪张卡未知。',
'U04':'工作链是一般做法；实际实例与分析闭环待证，后续动作列为建议。',
'P07':'金卡而卡记录未给，只能待核；不能说无付费资格。','P08':'本期总部月报范围不能推广历史/合作方。','P09':'本期不纳入成立；全系统免费与分类互斥均不能推得。',
'C01':'一有资格账户、两笔不同订单；同类多卡不可复制订单。','C02':'至少一张家庭季卡范围内有效，成立，其他卡不抵消。','C03':'不成立；同一卡需兼具产品和有效期条件。','C04':'完整卡表无记录可否定本期资格；缺表时未知。','C05':'月末资格是；有效购买否；活跃定义未知不能否定。','C06':'一有资格账户、两笔订单；跨产品仍去重。',
'F03':'一般步骤不能代最近活动事实；需对应活动/名单/执行记录及经手人核验。','F04':'信息整理不等执行确认，范围工作量责任记录/人员安排需确认。','F05':'保留已知局部链；闭环未验证不等没有闭环。','F06':'主观负担，无测量、无原因因果；其他工作有权益说明与回访。','F09':'仅发放事实；使用资格与适用规则未知。','E02':'趋势角色陈述、老化个人判断、三个月期望；量化口径明确未定；测试不证明真实原因或收益。','E03':'两数字是不同角色所称不同统计总体，不能计算活跃率/沉睡差或断言矛盾。','E05':'拒用失效依据，保留来源失效与待核，不认定不存在。','T01':'正文/过程分离属表达组织选择，不改变已确认业务规则证据性质。','T02':'本次仅新增句的来源归属、状态、规则/设计边界；不冒称所有字段或全量引用审计通过。','T03':'对照正式v0.4而非旧v0.3；正文更新仅本期测试与原访谈范围，前后版本分存；不要求把用户已排除的Excel或FDE交付重塞正文。','REG01':'建议可核对支持及工作连接/观察方法，不冒称第一阶段已选定或最佳价值/已提效。','REG02':'原因验证是业务目标，定义核对是前提，阶段产出应支撑原因或下一步；选择建议非客户已决。'}
rows=[]
for id in ids:
 c=cases[id]
 if id.startswith('P') and id not in mapids:
  mapids[id]=['products']; notes[id]={'P01':'有效悦享年卡纳入，普通等级不排除。','P02':'有效家庭季卡纳入。','P03':'金卡等级不能补失效卡，无本期资格。','P04':'付费联名卡排除本期，收费/等级不替代。','P05':'体验卡排除本期。','P06':'有效家庭季卡纳入，购卡金额零不排除。'}[id]
 if id.startswith(('DY','DQ')):
  mapids[id]=['products','dates']; n=int(id[2:]); notes[id]={1:'生效前无效。',2:'生效当天有效。',3:'生效后有效。',4:'计划结束前有效。',5:'计划结束当天无效。',6:'计划结束后无效。',7:'提前终止前有效。',8:'提前终止当天无效。',9:'提前终止后无效。',10:'提前终止晚于计划结束仍在计划结束当天无效。',11:'按给定历史判定日有效，运行日失效不改历史判断。',12:'生效前无效，不能只检查终止上界。'}[n]+' 这是题内人工卡记录上的静态规则应用，不是实际数据/生产历史验证。'
 gs=mapids[id]; refs=list(dict.fromkeys(z for g in gs for z in groups[g].get('refs',[])))
 rows.append({'id':id,'input_track':c['input_track'],'source_groups':gs,'source_refs':refs,'independent_criterion':notes[id],'fixture':c.get('fixture')})
used={r for x in rows for r in x['source_refs']}
d={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':'source_criteria_frozen_before_reviewer_expectations_read','scope':'仅来源归属、未知/已知/明确未定与业务规则/建模选择专项','model_sha256':hashlib.sha256((audit/'input/business_model.md').read_bytes()).hexdigest(),'api_calls':0,'coverage_count':len(rows),'input_tracks':{'model_only':53,'artifact_review':3},'method':'按原材料/完整问答建立来源分组，再逐题映射。未读reviewer_expectations、historical_expectations、旧模型答案；查找当前修订说明时曾见少量历史成绩标题，未作为判据/证据使用。','general_rules':['原问答分提问前提、角色新增答复、总结认可；未得正式文件不抹去已获规则。','未知不等无/未定；明确未定也不能退回未知。','业务规则、角色确认的统计选择、学员候选分析规则与表达组织设计分开。','题内完整记录可支持相应否定；未提供记录不等不存在；所有人工例仅题内。','不把每题未重复共通规则自动当缺陷；仅实质来源错误/状态扭曲/分类错误阻断。'],'source_groups':groups,'source_registry':{k:sources[k] for k in sorted(used)},'rows':rows}
(out/'source-criteria.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
md=['# 独立来源判据：model_and_artifact','',f"冻结时间：{d['created_at']}；0 API；56项（53 model_only + 3 artifact_review）。",'','先原材料与完整问答、后逐题映射；本文件形成后才读取 reviewer_expectations.json。','',f"候选 SHA-256：`{d['model_sha256']}`。当前候选不是正式 v0.4。",'',d['method'],'','## 共通边界','']+['- '+x for x in d['general_rules']]
for name,g in groups.items(): md += ['',f'## 来源组 {name}','',g['criterion'],'','来源：'+('、'.join(g['refs']) or '无访谈引用')+('；'+g['material'] if 'material' in g else '')]
md += ['','## 逐题独立判据','','| ID | 来源组 | 判据 |','| --- | --- | --- |']
for r in rows: md += [f"| {r['id']} | {', '.join(r['source_groups'])} | {r['independent_criterion']} |"]
(out/'source-criteria.md').write_text('\n'.join(md)+'\n'); print(d['created_at'],len(rows),d['model_sha256'])
