#!/usr/bin/env python3
"""只整理设计记录、纯比较自检和文件哈希；不调用构建、引擎或Agent。"""
import copy
import csv
import hashlib
import importlib.util
import json
import sys
sys.dont_write_bytecode = True
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
small=load(OUT/'tests-small.json');fixture=load(OUT/'tests-fixture.json')
summary=load(OUT/'calculation-summary.json')
S1='materials/w03/01_订单日报说明.md#有效订单数'
S3='materials/w03/03_会员运营周报.md#月内购买会员数/月内复购会员数/月内复购率及开头调整说明'
S5='materials/w03/05_数据字典.md#orders/members/cards及覆盖'
C='docs/w03/contract.md#构建输出/查询与结果'
BM='docs/w03/business_model.md#2.核心对象、属性与关系（账户、卡、等级、有效购买）'
common_review=['人数单位为CRM账户count，不是卡数或自然人数；复购率ratio转百分数时乘100。',
 '有效订单须paid且实付减累计退款大于0；全退取消不凑购买或复购，部分退净额正仍有效。',
 '这是普通月内指标；不添加会员等级、购卡金额或月末付费资格条件，不借用B7六项范围。',
 '声明全门店全渠道，时间为Asia/Shanghai完整自然月；不因卡一对多重复订单。',
 '查询数值与解释单独审核；本文件只规定解释审查标准，尚无真实解释可评分。']
records=[
 {'id':'B6-N01','file':'tests-small.json','rules':['账户月订单集合>=1/>=2','零退款/部分退有效、全退取消排除','购买账户分母','普通/付费分离','等级与多卡不改变人数'],
  'sources':[S1,S3,S5,BM],
  'target_errors':['用paid行数或订单数替账户数','用所有20注册账户作为分母','取消/全退计买家','添加付费卡或等级筛选'],
  'discrimination':['正确15买家/12复购买家=0.8；全注册分母错误为12/20=0.6。',
    'M00002部分退款O0000003净7000分有效，加O0000018构成当月复购。',
    'M00003 O0000004、M00008 O0000012全退；M00017取消039+全退040；M00004取消005，均不是8月买家。',
    'M00015无卡仍有036/037两有效单；M00020仅体验卡仍有046/047两有效单；M00001普通等级有两有效单。'],
  'gaps':['单凭N01不能区分多卡连接将单有效单放大为两单（M00001原small已经复购）；由R01补齐。'],
  'explanation_review':common_review+['8月15、12、0.8=80%，不能解释成12/20、80原始比率或终身复购。']},
 {'id':'B6-M01','file':'tests-small.json','rules':['跨连续完整月按月输出','自然月内复购','半开边界','月组身份','不可跨月合计人数或平均率'],
  'sources':[S1,S3,S5,C],
  'target_errors':['M00005跨月各一单误判月内复购','合并或平均两月','交换月份标签/漏月/重复月/多月','按订单窗口总数代替账户月集合'],
  'discrimination':['7月=11/1/1÷11，8月=15/12/12÷15；两月不同，可识别月组标签交换。',
    'M00005 O0000006在7月31日、O0000007在8月20日，各月仅1单，均非复购；月内复购不可等于观测期后续购买。',
    '7月复购只有M00006的O0000008/O0000009；8月1日和31日属于8月，不能丢月末或串入7月。',
    '即使跨月26人次与13复购人次能相加，也不得冒充跨月账户数；(1/11+12/15)/2不是任一月率。'],
  'gaps':['本题保证按月查询的分组和值；不单独测试用户主动索要跨月合计的拒绝措辞。当前7设计不追加第8题。',
           '零业务月份按月分组是否补行不是本题覆盖范围；Z01仅不分组的单月零值合同。'],
  'explanation_review':common_review+['必须分别说明7月约9.090909%、8月80%；不得给跨月平均代替两行，不称26个不同账户。']},
 {'id':'B6-R01','file':'tests-fixture.json','rules':['1单与2单门槛','1有效+1全退不凑2单','取消不凑购买/复购','部分退仍有效','多卡不复制订单','跨门店跨渠道仍同账户月累计'],
  'sources':[S1,S3,S5,BM],
  'target_errors':['paid未扣全退判断','全量订单行直接算复购','卡表一对多放大单数','门店/渠道先拆分导致漏账户月复购','只算0退款订单'],
  'discrimination':['人工M00001仅FXB6-001有效，002全退、003取消；M00002的004和005部分退净1500为两单，分属S01门店/S02小程序也应合并为该账户当月2单；M00003仅006有效，M00004仅007取消。',
    '正确买家3、复购买家1、率1/3；paid两单算法会把M00001计复购变2/3；取消也计买家会变4人。',
    'M00001保留原两张卡，单有效订单错误按两卡复制会将复购1变2；卡不能参与普通月内门槛。'],
  'gaps':['原small无同账户同月一有效加一全退，故7条人工orders为专用边界；不能计作课程small或真实客户数据。',
          '不含paid实付为0单；B2既有人工边界承接该通用有效订单规则，本批不声称独立新增覆盖。'],
  'explanation_review':common_review+['只能说本人工隔离样本3、1、约33.333333%，不能拿来替代原small8月15、12、80%。']},
 {'id':'B6-Z01','file':'tests-small.json','rules':['覆盖内完整零购买月','人数0与零分母null区分'],
  'sources':[S1,S3,S5,C,'materials/data/small/manifest.json'],
  'target_errors':['0/0给0或100%','无行当覆盖外','把注册/持卡但不购买账户算买家','用空数组或缺字段替代确定0'],
  'discrimination':['2026年5月在覆盖内，原orders全月0行；购买集合与复购集合为空；人数0、0，率null。members中20条账户记录仍在（其中部分注册日晚于5月）；不能用这些记录或卡表代替当月购买分母。'],
  'gaps':['本题无订单；不能单独证明一个只有全退/取消订单月份的零购买行为，相关排除规则由N01与R01另覆盖。'],
  'explanation_review':common_review+['说明有数据覆盖且无有效购买，复购率分母0所以未定义，不可称0%、查询失败或覆盖外。']},
 {'id':'B6-X01','file':'tests-small.json','rules':['仅完整自然月'], 'sources':[S3,C],
  'target_errors':['静默扩月或算半月'], 'discrimination':['8月1日至15日含15日，对应[08-01,08-16)，不是完整自然月，必须unsupported。'],
  'gaps':[], 'explanation_review':['拒绝原因是月度指标仅支持完整自然月；不说无数据覆盖，不自动改为全月，不返回业务数值。']},
 {'id':'B6-X02','file':'tests-small.json','rules':['仅全门店口径'], 'sources':[S3,C],
  'target_errors':['把可达成交店维度等同业务支持','换成归属店分组','去掉分组返回全店'],
  'discrimination':['问题明确成交门店分组，与全门店口径冲突；unsupported有业务材料依据。'],
  'gaps':[], 'explanation_review':['应说明当前普通月内三项仅全门店，不能分店；不能声称所有指标都不支持门店。']},
 {'id':'B6-X03','file':'tests-small.json','rules':['full_month_only当前全渠道实现边界'], 'sources':[C,'platform/fde_product/metrics/engine.py:117-120'],
  'target_errors':['静默删掉渠道筛选','把业务原文未说的话补成禁止','当前约束不支持却预期ok'],
  'discrimination':['问题明确小程序筛选；当前full_month_only在filters非空时拒绝，故unsupported。'],
  'gaps':['03原文未明确渠道禁止；这一项是当前契约/实现边界，不是业务方长期禁止的事实。'],
  'explanation_review':['应说明当前月度查询只提供全渠道，暂不支持小程序筛选；不得说客户原文/青禾政策禁止按渠道。']}]
all_tests={t['id']:t for t in small+fixture}
for r in records:
    r['native_case_ids']=[r['id']]
    r['question']=all_tests[r['id']]['question']
    r['independent_expected']=all_tests[r['id']]['expected']
    r['status']='independent_expected_frozen_pending_separate_review_not_run'
save(OUT/'design.json',{'batch':'B6','stage':'design_only','metrics':['monthly_buyer_count','monthly_repeat_buyer_count','monthly_repeat_rate'],
 'design_count':7,'native_candidate_count':7,'original_small_cases':6,'isolated_fixture_cases':1,
 'rule_origin':'口径数值来自原业务材料与CSV；公开engine及已安装MetricFlow代码只用于接口限制/序列化，未据其业务实现取值。',
 'version_policy':'成功期望锁manifest已知id；原数据及全部输入文件哈希另冻结。不锁尚未加载的catalog_sha256；未将任何候选当作实际加载库。',
 'execution':'未构建、未真实问数、未改Skill/正式tests/judge/model/W02；只有独立CSV核算与纯比较自检。',
 'judge_contract':{'integer':'exact','ratio_rel_tol':1e-9,'ratio_abs_tol':1e-7,'null':'not equal zero','group_identity':'month key exact; allow row reorder, reject missing/extra/duplicate/mislabeled groups'},
 'metric_coverage':{m:[r['id'] for r in records] for m in ['monthly_buyer_count','monthly_repeat_buyer_count','monthly_repeat_rate']},
 'cases':records})
# 接口证据：仅读取静态公开代码及已安装库的序列化实现，不生成/执行业务SQL。
segments=[('platform/fde_product/metrics/engine.py',117,120,'月度限制与统计月ID'),
 ('platform/fde_product/metrics/engine.py',157,157,'日期类值str序列化'),
 ('.venv/lib/python3.11/site-packages/dbt_metricflow/cli/dbt_connectors/adapter_backed_client.py',172,178,'适配器结果经MetricFlowDataTable.create_from_rows'),
 ('.venv/lib/python3.11/site-packages/metricflow/data_table/mf_table.py',186,192,'create_from_rows进入builder'),
 ('.venv/lib/python3.11/site-packages/metricflow/data_table/mf_table.py',254,279,'date统一为午夜datetime，datetime去时区'),
 ('.venv/lib/python3.11/site-packages/metricflow/sql/render/expr_renderer.py',286,295,'自然月DATE_TRUNC输出月首')]
evidence=[]
for name,start,end,purpose in segments:
    p=ROOT/name
    evidence.append({'path':name,'lines':[start,end],'purpose':purpose,'sha256':sha(p),'excerpt':'\n'.join(p.read_text().splitlines()[start-1:end])})
save(OUT/'interface-evidence.json',{'month_dimension':'metric_time__month','month_key_examples':['2026-07-01 00:00:00','2026-08-01 00:00:00'],
 'conclusion':'适配器进入MetricFlowDataTable后date和datetime均规范为无时区datetime；engine最终str，月首固定YYYY-MM-01 00:00:00。不是只看engine猜日期类型。',
 'no_native_calls':True,'business_expected_uses_interface_output':False,'evidence':evidence})
# 仅导入纯比较judge；“actual”均为显式合成期望副本或错误副本，没有真实Agent结果。
spec=importlib.util.spec_from_file_location('existing_pure_judge',ROOT/'customer/w03/judge.py')
j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
checks=[]
def compare_check(name,want,actual,should_pass):
    result=j.compare(want,actual)
    assert result['passed']==should_pass,(name,result)
    checks.append({'name':name,'input_origin':'synthetic_expected_copy_only','should_pass':should_pass,**result})
for t in small+fixture:compare_check('self_equal_'+t['id'],t['expected'],copy.deepcopy(t['expected']),True)
m=all_tests['B6-M01']['expected'];n=all_tests['B6-N01']['expected'];z=all_tests['B6-Z01']['expected']
a=copy.deepcopy(m);a['rows'].reverse();compare_check('legal_month_row_reorder',m,a,True)
mutations=[('wrong_date',n,lambda a:a['intent'].__setitem__('end','2026-08-31')),
 ('wrong_metric',n,lambda a:a['intent']['metrics'].__setitem__(0,'buyer_count')),
 ('added_channel',n,lambda a:a['intent']['filters'].append({'field':'order__channel','op':'eq','value':'小程序'})),
 ('wrong_unit',n,lambda a:a['units'].__setitem__('monthly_repeat_rate','count')),
 ('wrong_count',n,lambda a:a['rows'][0].__setitem__(0,16)),
 ('error_with_original_numbers',n,lambda a:a.__setitem__('status','error')),
 ('wrong_locked_data_id',n,lambda a:a.__setitem__('data_version','not-this-fixture')),
 ('missing_month',m,lambda a:a['rows'].pop()),
 ('duplicate_month',m,lambda a:a['rows'].append(copy.deepcopy(a['rows'][0]))),
 ('extra_month',m,lambda a:a['rows'].append(['2026-06-01 00:00:00',0,0,None])),
 ('wrong_month_identity',m,lambda a:a['rows'][0].__setitem__(0,'2026-06-01 00:00:00')),
 ('swapped_month_numbers',m,lambda a:a.__setitem__('rows',[[a['rows'][0][0]]+a['rows'][1][1:],[a['rows'][1][0]]+a['rows'][0][1:]])),
 ('null_to_zero',z,lambda a:a['rows'][0].__setitem__(2,0)),
 ('number_to_string',n,lambda a:a['rows'][0].__setitem__(0,'15')),
 ('number_to_bool',n,lambda a:a['rows'][0].__setitem__(0,True)),
 ('rate_times_100',n,lambda a:a['rows'][0].__setitem__(2,80)),
 ('wrong_denominator_20',n,lambda a:a['rows'][0].__setitem__(2,12/20))]
for name,want,change in mutations:
    a=copy.deepcopy(want);change(a);compare_check(name,want,a,False)
save(OUT/'judge-selfcheck.json',{'kind':'pure_comparison_synthetic_inputs_not_native_run','judge_path':'customer/w03/judge.py','judge_sha256':sha(ROOT/'customer/w03/judge.py'),
 'checks':checks,'passed':True,'positive_checks':8,'negative_checks':len(mutations)})
# 逐账户人工锚点，可让审阅者不运行算法直接复算关键边界。
(OUT/'account-ledger-notes.md').write_text('''# B6 逐账户月度台账说明

`ledger-small.csv`为原small全部24个月×20账户=480行，`ledger-fixture.csv`为人工隔离数据同范围480行。每行列出全部订单、有效订单、排除订单、CSV行号、日期、状态、实付/退款与纳排原因；无订单行保留空集合。等级、卡ID只作为审查上下文，不参与核算。`monthly-summary-*.json`列出每个月买家与复购买家完整ID集合。

人工独立校准：

- 7月购买：M00002、05、06、08、10、11、12、13、14、19、20，共11；复购只有M00006（O0000008与O0000009），共1，率1/11。
- 8月购买：M00001、02、05、07、09、10、11、12、13、14、15、16、18、19、20，共15；复购为M00001、02、09、10、11、12、13、14、15、18、19、20，共12，率12/15=0.8。
- M00005在7月O0000006和8月O0000007各1有效单，不是任何一个月的复购。不能拿观测期后续订单替代月内复购。
- 8月排除：M00003 O0000004全退、M00008 O0000012全退；M00004 O0000005取消；M00017 O0000039取消、O0000040全退。M00002部分退款O0000003仍有效。
- 5月：原orders全月无行，买家/复购买家集合均空，0、0、null；manifest覆盖此月。不是0%或覆盖外。
- 人工R01：M00001仅FXB6-001有效，002全退、003取消；M00002的004/005有效（005部分退）；M00003仅006有效；M00004仅007取消。3买家、1复购买家，1/3。M00001原两张卡保留，不能复制其一笔有效单凑复购。

原small缺“同账户同月1有效加1全退”的组合，因此R01隔离fixture替换orders为7条人工数据，其他三表逐字节复制，全部订单/卡/member/store外键检查通过。不将此fixture描述为原课程数据或客户事实。没有真实Agent问数。
''')
review={'reviewer_role':'design_author_selfcheck_only','external_independent_review':'pending_separate_agent',
 'passed_author_preflight':True,'source_manifest_sha_counts_pk_fk_checks':True,'calculation_manual_anchors':True,'order_dates_not_before_account_registration':True,
 'seven_designs_mapped_to_seven_candidates':True,'all_success_fields_present':True,'non_ok_no_success_fields':True,
 'all_month_group_identity_required':True,'null_is_known_undefined_not_unknown':True,
 'no_unloaded_catalog_hash':True,'actual_freeze_file_hashes':True,'interface_type_path_statically_verified':True,
 'pure_comparison_checks':{'positive':8,'negative':len(mutations),'all_expected_outcomes':True},
 'data_limits':['small为课程干净合成数据，不是真实CRM或规模验证。','原small缺混合有效+全退账户月，单独人工fixture补齐。',
 '没有测试零月按月分组补行；Z01只测单月不分组。','没有单独第8题验证索要跨月合计时的拒绝回答；M01已有按月并拒绝混算的结构化约束。'],
 'native_builds':0,'native_queries':0,'explanation_review':'criteria_prepared_no_real_answers',
 'blocked_business_decisions':[],'next':'由另一独立审阅Agent复核设计/原CSV/冻结哈希；本轮止于设计，不构建或问数。'}
save(OUT/'preflight-review.json',review)
(OUT/'preflight-review.md').write_text('''# B6 作者自检（不是独立终审）

七个设计已映射七个完整中文候选：原small六题（八月、七八月分组、五月零月、三个unsupported）＋隔离人工fixture一题。独立CSV核算及人工集合锚点相符；原small manifest四表hash、行数、主键和外键已核，fixture另有真实manifest。

五月原数据在覆盖内且无订单：0、0、null。七月11、1、1/11；八月15、12、0.8；人工R01为3、1、1/3。月组ID与日期序列化已沿公开engine→适配器→MetricFlowDataTable静态核实，证据在interface-evidence.json。

现有纯比较judge通过8个正向副本及17个负向注入自检；这些输入是期望副本，不是真实Agent结果或新的问数运行。缺组/多组/重复组/换月份/数字字符串/布尔值/null→0均能拒绝。未修改judge或正式tests。

渠道不支持的依据是当前full_month_only契约和实现，不写成03业务原文禁止。普通月内3项不套用B7付费资格、等级或多卡筛选。

边界：没有声称测试零月按月补行，也未单加跨月合计拒绝题；两项不是此次七设计的独立新覆盖。paid实付零沿既有B2边界另证，不冒称本批新增。没有业务未决阻断。

当前状态：作者自检通过，等待另一Agent独立审核。无构建、无真实问数、无真实解释评分，不能将7候选记作7通过。
''')
(OUT/'summary.md').write_text('''B6 已准备7个设计与冻结期望：原small 6题＋人工隔离R01 1题。7月11/1/1÷11，8月15/12/0.8，原small覆盖内5月0/0/null；R01人工7订单为3/1/1÷3，补原样本缺失的一有效＋全退/取消与多卡放大边界。

完整映射见design.json；全部24个月逐账户订单集合见ledger-small.csv、ledger-fixture.csv；独立核算入口calculate_expected.py；接口序列化依据、原料与产物文件hash已留存。preflight-review只是作者自检，外部独立审核待进行。未构建、未真实Agent问数、未改正式测试/Skill/模型/W02；未锁未加载catalog。
''')
# 锁定真实文件哈希，不把文件hash伪装成data_sha256或catalog_sha256；freeze自身不递归哈希。
inputs=['materials/w03/01_订单日报说明.md','materials/w03/03_会员运营周报.md','materials/w03/05_数据字典.md',
 'docs/w03/business_model.md','docs/w03/contract.md','docs/w03/test-guide.md','customer/w03/judge.py',
 'templates/w03/dimension_targets.json']+[f'materials/data/small/{n}' for n in ['manifest.json','orders.csv','members.csv','stores.csv','cards.csv']]
inputs += sorted({x[0] for x in segments})
files={str(p.relative_to(ROOT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='expected-freeze.json' and '__pycache__' not in p.parts}
save(OUT/'expected-freeze.json',{'stage':'design_and_independent_expectations_frozen_pending_external_review',
 'business_values_origin':'原业务材料+stdlib CSV账户月订单集合核算；非生成SQL/metric库/actual',
 'inputs_sha256':{p:sha(ROOT/p) for p in inputs},'artifacts_sha256':files,
 'data_version_ids':[load(ROOT/'materials/data/small/manifest.json')['id'],load(OUT/'fixture-data/manifest.json')['id']],
 'catalog_sha256_policy':'omitted: no cumulative32 library loaded; do not fabricate a catalog hash',
 'data_sha256_policy':'expected does not claim loaded dataset hash; raw manifest/four CSV hashes frozen above; compare to actual load before future execution',
 'native_build_calls':0,'native_queries':0,'external_review':'pending_separate_agent'})
print(json.dumps({'design_cases':7,'small_cases':6,'fixture_cases':1,'selfcheck_positive':8,'selfcheck_negative':len(mutations),'frozen_artifacts':len(files)},ensure_ascii=False))
