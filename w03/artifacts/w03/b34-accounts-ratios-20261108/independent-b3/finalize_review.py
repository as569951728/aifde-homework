import json,hashlib,datetime,copy,csv
from pathlib import Path
OUT=Path(__file__).resolve().parent;B=OUT.parent;ROOT=OUT.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(name,d):p=OUT/name;assert not p.exists(),name;p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
progress=read(OUT/'case-review-progress.json');assert len(progress['cases'])==28 and progress['explanation_passed']==26
expected={c['id']:c for name in ['tests-new-small.json','tests-regression-original21.json','tests-fixture-b2-unchanged.json'] for c in read(OUT/name)}
freeze=read(OUT/'expected-freeze.json');assert all(sha(OUT/f)==h for f,h in freeze['files'].items())
combo=read(B/'combined-freeze.json');assert all(sha(B/f)==h for f,h in combo['files'].items())
library_hash=hashlib.sha256(json.dumps({p.name:sha(p) for p in sorted((B/'library-v1').iterdir()) if p.suffix in ['.json','.yml','.sql']},sort_keys=True).encode()).hexdigest()
evidence={};reports=[];actuals={};sql_count=0
for lane in ['new','regression','fixture']:
 binding=read(B/f'version-binding-{lane}-v1.json');proj=ROOT/binding['project'];dataset=read(proj/'dataset.json');fingerprint=hashlib.sha256(json.dumps({k:v for k,v in dataset.items() if k!='library_sha256'},sort_keys=True).encode()).hexdigest();assert fingerprint==binding['data_sha256'];assert dataset['library_sha256']==binding['catalog_sha256']==library_hash
 source_data=ROOT/('artifacts/w03/b2-order-counts-20261108/independent/fixture-data' if lane=='fixture' else 'materials/data/small')
 assert all(sha(source_data/f)==h for f,h in dataset['sha256'].items())
 rp=B/f'test-{lane}-v1/metric_test_report.json';report=read(rp);assert report['complete'];reports.append(dict(lane=lane,report_cases=len(report['cases']),complete=True))
 for f in [rp,B/f'version-binding-{lane}-v1.json',B/f'execution-tests-{lane}-v1.json',proj/'dataset.json']:evidence[str(f.relative_to(ROOT))]=sha(f)
 for c in report['cases']:
  if c['id'] not in expected:continue
  original=expected[c['id']];unlocked=copy.deepcopy(c['expected']);unlocked.pop('data_sha256',None);unlocked.pop('catalog_sha256',None)
  assert c['question']==original['question'] and unlocked==original['expected']
  a=c['actual'];actuals[c['id']]=a;assert c['comparison']['passed'];manual=progress['cases'][c['id']]
  assert all(sha(ROOT/f)==h for f,h in manual['evidence_sha256'].items());evidence.update(manual['evidence_sha256'])
  if a['status']=='ok':
   sql_count+=1;assert a['data_sha256']==fingerprint and a['catalog_sha256']==library_hash and a['data_version']==dataset['id'];assert 'cards' not in a['sql'].lower()
for f in ['combined-freeze.json','tests-new-small.json','tests-regression-small.json','tests-fixture-b2.json','b3-result-controls.json','independent-b3/expected-freeze.json','independent-b3/generation-review-v1.json']:evidence[str((B/f).relative_to(ROOT))]=sha(B/f)
assert len(actuals)==28 and sql_count==26
query=dict(status='failed_original_explanation_review',approved_for_batch_closeout=False,reviewed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='B3新6、small原21、旧B2隔离fixture1',reviewed_case_ids=list(progress['cases']),machine_contract_passed=28,machine_contract_total=28,numeric_ok_cases_passed=26,numeric_ok_cases_total=26,non_ok_status_cases_passed=2,successful_sql_reviewed=26,explanation_passed=26,explanation_total=28,failed_checks=progress['failed_checks'],cases=list(progress['cases'].values()),evidence_sha256=evidence,reports=reports,notes=['所有成功SQL及完整解释逐题已读；另核answer-trace输入/输出与当前实际结果、catalog及版本一致。','原21对象与fixture题保持不变；执行只增加数据/库哈希锁，冻结业务期望和原数据未改。','初轮28/28是完整结构/意图/数值或非ok状态比较；其中26题有数值SQL、2题为clarify/unsupported原因检查。','原首轮两条解释失败不随导师审校副本修改，不称原生端到端全通过。','人工fixture仅技术边界；U01各错误模式分别有证据，不声称同一账户多卡且多退款交叉覆盖；规模0。'])
write('query-review-v1.json',query)
(OUT/'query-review-v1.md').write_text('''# 原生首轮独立审查：数值正确，解释有两条失败\n\n本范围为B3新6题、原small21题、B2旧人工fixture1题，共28题。结构/意图/数值或状态判定28/28；其中26条成功SQL已逐条审核、2条非成功原因符合缺时间与覆盖外规则。完整原回答审查26/28，`approved_for_batch_closeout=false`。\n\n- B3-U01：数值17/5/3/50及SQL正确，回答却将退款账户限定为“发生退款的有效已支付订单”。原定义包含全退paid订单，错误限有效单会把5个退款账户变成3个，漏M00003、M00017。\n- B1-Z01：五项0及SQL正确；实际窗口[2026-06-01,2026-06-30)，即6月1–29日含首尾，回答却说实际包含6月30日且没有截到29日。原数据6月30日另有O0000015，错误范围不能对应五项0。\n\n其余26条解释无阻断，包括原fixture五天逐日条件、覆盖内零、缺时间澄清和覆盖外不支持。所有分组键、筛选、日期、单位和数值均逐项比对；无多卡连接或金额去重，退款按原下单日期归属。\n\n本文件保留首轮失败。允许另存导师审校副本并独立复审，不能改原分或宣称自动解释链路已修。完整原生报告、逐题result/answer-trace、冻结期望、数据及库版本哈希均在同名JSON锁定。\n''')
# Review correction as a separate artifact; never overwrite original answer or grade.
corrections=[];cevidence={};manifest=read(B/'mentor-corrections/manifest.json')
for mid in ['B3-U01','B1-Z01']:
 p=B/'mentor-corrections'/f'{mid}.json';d=read(p);original=read(ROOT/d['original_trace']);assert sha(ROOT/d['original_trace'])==d['original_trace_sha256'];assert d['original_actual']==actuals[mid] and d['original_answer']==original['answer']==actuals[mid]['answer'];assert d['model_calls']==d['queries']==0 and not d['native_score_changed'] and not d['automatic_product_fix']
 assert d['corrected_answer']!=d['original_answer']
 if mid=='B3-U01':
  assert '有效已支付' not in d['corrected_answer'] and '包含全额退款订单所关联的账户' in d['corrected_answer']
  detail='移除退款账户的有效单限制并明确包含全退账户；17/5/3/50、日期、账户/成交门店角色、原始件数与未筛选范围均保持正确。'
 else:
  assert '实际查询已包含6月29日、排除6月30日' in d['corrected_answer']
  rr=list(csv.DictReader((ROOT/'materials/data/small/orders.csv').open()));assert not [r for r in rr if '2026-06-01'<=r['ordered_at']<'2026-06-30']
  detail='准确说明6月1–29日含首尾、排除6月30日；窗口无订单由原CSV独立支持；五项零分/0.00元、paid范围及退款日期归属正确。'
 corrections.append(dict(id=mid,passed=True,full_corrected_answer_read=True,original_trace_preserved=True,source_and_sql_review=detail))
 for f in [p,p.with_suffix('.md'),p.with_suffix('.diff'),ROOT/d['original_trace']]:cevidence[str(f.relative_to(ROOT))]=sha(f)
for item in manifest['items']:assert sha(ROOT/item['file'])==item['sha256']
for f in [OUT/'query-review-v1.json',B/'mentor-corrections/manifest.json',ROOT/'materials/w03/01_订单日报说明.md',ROOT/'docs/w03/contract.md',ROOT/'materials/data/small/orders.csv']:cevidence[str(f.relative_to(ROOT))]=sha(f)
corr=dict(status='approved_for_supervised_closeout',approved_for_supervised_closeout=True,approved_for_native_end_to_end_pass=False,failed_checks=[],corrected_case_ids=['B3-U01','B1-Z01'],corrections_passed=2,corrections_total=2,original_machine_contract_passed=28,original_explanation_passed=26,original_explanation_total=28,new_model_calls=0,new_queries=0,automatic_explanation_fixed=False,native_scores_unchanged=True,reviews=corrections,evidence_sha256=cevidence,limitations=['仅允许本批监督审校方式收束和使用已复审副本；原生自动解释2处失败仍留档。','后续B5+B6继续回归原题，自动解释可靠性待解决；本结论不是客户验收/提交/生产许可。'])
write('reviewed-corrections-v1.json',corr)
(OUT/'reviewed-corrections-v1.md').write_text('''# 两条导师审校副本：独立复审通过\n\nB3-U01与B1-Z01完整修订均通过，`approved_for_supervised_closeout=true`、`failed_checks=[]`。只批准本批在监督审校方式下收束及使用这两份已复审材料，未批准原生端到端全绿。\n\nB3-U01已去除退款账户的有效单限制，明确包含全额退款账户，原数值、时间、成交门店角色及原始件数均正确。B1-Z01已明确6月1–29日含首尾且排除6月30日，五项0及窗口无订单可由实际SQL、原CSV和半开契约复核。\n\n原回答、原结果、SQL、期望及库未变；本范围原机器判定28/28、原解释26/28，修订副本2/2另计。新增模型调用和查询均0，自动解释链路未修，原首轮失败不回改。版本与原/改文本哈希见同名JSON，后续批次仍应回归原题。\n''')
print(json.dumps(dict(query_review='failed_original_explanation_review',machine=28,explanation=26,total=28,corrected=2,approved_for_supervised_closeout=True),ensure_ascii=False))
