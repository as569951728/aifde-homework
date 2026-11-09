import json,pathlib,hashlib,copy,re,datetime
root=pathlib.Path.cwd();base=root/'W03/实操工程/artifacts/w03/source-semantics-audit-20261108';out=base/'reviews/source_context';oldrun=root/'W03/实操工程/artifacts/w03/context-application-qa-20261107'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
orig=json.loads((base/'input/reviewer_expectations.json').read_text());cand=json.loads((base/'candidate/reviewer_expectations.json').read_text());r=json.loads((out/'review.json').read_text());criteria=json.loads((out/'source-criteria.json').read_text());ch=json.loads((base/'candidate/change_manifest.json').read_text());manifest=json.loads((oldrun/'input/manifest.json').read_text());materials=json.loads((oldrun/'input/materials_index.json').read_text());qs=json.loads((base/'input/original_questions.json').read_text());qmap={x['id']:x for x in qs['cases']}
assert H(base/'candidate/reviewer_expectations.json')=='f799da7f4420620386e73f6b447efe219ed37f22ef881f08595f995b2b5280a2'
expected=copy.deepcopy(orig); patch_checks=[]
for patch in r['suggested_json_field_changes']:
 pp=patch['path'].split('/')[1:];v=expected
 for k in pp[:-1]:v=v[int(k)] if isinstance(v,list) else v[k]
 if patch['op']=='add':
  assert pp[-1]=='-';v.append(patch['value'])
 else:
  if isinstance(v,list):v[int(pp[-1])]=patch['value']
  else:v[pp[-1]]=patch['value']
 matched=[x for x in ch['patches'] if x['patch']['path']==patch['path']]
 assert len(matched)==1 and matched[0]['patch']==patch
 if patch['op']=='replace':
  prev=orig
  for k in pp:prev=prev[int(k)] if isinstance(prev,list) else prev[k]
  assert matched[0]['old_value']==prev
 patch_checks.append({'field':patch['path'],'op':patch['op'],'reason':patch['reason'],'status':'exactly_applied_and_manifest_preserved_old_value'})
changed=['F07','A02','A03','E06'];case_results=[]
why={
'F07':'配合说明不构成权限授权/接通证明，与否定权限存在分开；保留可配合范围、无固定交付承诺。新增07引用已在原题fixed_materials及冻结输入内。',
'A02':'保留03930提问前提，03931/03933具体人、额度及执行方不掌握；并列保留03931审批安排未定和03933收益目标/预算金额/正式批准未定，未把总体安排替换具体额度。',
'A03':'费用与结算框架对应03927；付款安排语词注明来自03932提问总结，未冒称03927原话或03933付款批准。可等价转述未确认状态，无逐字引用门槛。',
'E06':'03885范围与03886新增规则分别列明，保留日期/空值/账户规则和文件历史缺口；03910方案、03911新增核查要求、03932总结、03933认可及03931全文限制有区分。'}
for prev in r['cases']:
 i=prev['candidate_case_index'];id=prev['id'];assert cand['cases'][i]==expected['cases'][i]
 ischanged=cand['cases'][i]!=orig['cases'][i];assert ischanged==(id in changed)
 case_results.append({'id':id,'status':'pass_source_semantics_revision' if ischanged else 'pass_source_semantics_unchanged','checked_claims':[{'field':f'/cases/{i}','check':'candidate_equals_original_with_exact_suggested_patches' if ischanged else 'candidate_equals_original_entire_case','result':True,'reason':why.get(id,'整题结构与文本均未变化，保留首审来源语义结论。')}],'source_refs':prev['source_refs'],'findings':[]})
visible=[]
for id in ['E06','A03','F07','A02']:
 for src,mi in materials[id].items():
  p=oldrun/mi['snapshot'];text=p.read_text(); actual=H(p);assert actual==mi['sha256']==manifest['files'][mi['snapshot']]
  assert src in qmap[id]['fixed_materials']
  record={'case_id':id,'rendered_path':str(p.relative_to(root)),'source_path':src,'sha256':actual,'manifest_sha256_match':True,'materials_index_sha256_match':True,'source_already_in_original_questions_fixed_materials':True}
  if src.endswith('.json'):
   d=json.loads((root/src).read_text()); parsed={m.group(1):{'speaker':m.group(2),'content':m.group(3).strip()} for m in re.finditer(r'(MSG-\d+) · (user|assistant)\n(.*?)(?=\n\nMSG-\d+ · |\Z)',text,re.S)}
   missing=[m['id'] for m in d['messages'] if m['id'] not in parsed]
   differs=[m['id'] for m in d['messages'] if m['id'] in parsed and (m['speaker']!=parsed[m['id']]['speaker'] or m['content'].strip()!=parsed[m['id']]['content'])]
   assert not missing and not differs
   record.update({'full_transcript_message_count':len(d['messages']),'rendered_message_count':len(parsed),'full_original_messages_visible':True,'missing_ids':missing,'content_mismatches':differs,'message_ids':list(parsed)})
   critical=['MSG-03885','MSG-03886','MSG-03926','MSG-03927','MSG-03930','MSG-03931','MSG-03932','MSG-03933','MSG-03875','MSG-03877','MSG-03881','MSG-03883']
   record['critical_visible_excerpts']={k:parsed[k] for k in critical if k in parsed}
   if 'MSG-03931' in parsed:assert '但审批安排还没定' in parsed['MSG-03931']['content'];record['03931_latter_clause_visible']=True
  else:
   assert text.strip()==(root/src).read_text().strip();record['full_original_document_visible']=True
  visible.append(record)
preservation=[]
for p,h in criteria['source_hashes'].items():assert H(root/p)==h;preservation.append({'path':p,'sha256':h,'unchanged_since_independent_criteria':True})
assert H(base/'input/reviewer_expectations.json')==r['criteria_before_expectations']['candidate_expectations_sha256']==ch['expected_before_sha256']
assert H(out/'source-criteria.json')==r['criteria_before_expectations']['criteria_sha256']
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
data={'created_at_utc':now,'reviewer':'independent source_context subagent','status':'pass_source_semantics_revision','scope':'复审F07/A02/E06/A03精确修订及其余10题未变，核定原始冻结材料可见性；不评候选模型01731修订、不扩展到全维度或运行结论。','model_api_calls':0,'candidate_expected_sha256':H(base/'candidate/reviewer_expectations.json'),'baseline_expected_sha256':H(base/'input/reviewer_expectations.json'),'prior_review_sha256':H(out/'review.json'),'candidate_change_manifest_sha256':H(base/'candidate/change_manifest.json'),'counts':{'reviewed_cases':14,'revised_cases_passed':4,'unchanged_cases_passed':10,'exact_patch_checks':len(patch_checks),'rendered_files_verified':len(visible)},'cases':case_results,'exact_patch_checks':patch_checks,'visible_input_checks':visible,'input_visibility_conclusion':'E06的03931全文及后半句、陈姐完整上下文；A03的03926/27/32/33；F07完整老周访谈及07全文；A02完整王经理访谈，均已在此前冻结输入中。新增reviewer sources只扩展评审定位，没有新增模型输入。','citation_grading_boundary':'现有全局grading允许等价表达，不要求机械逐字引用；候选中的原句和消息定位用于精确归属，不能将审查者可见而模型未见的原句设为必引。此次新增定位实际已可见；若未来裁剪输入，必须重新核可见性，不能沿用本记录宣称可见。','preserved_inputs_and_sources':preservation,'historical_record_handling':{'historical_answers_or_grades_reread':False,'historical_grades_modified_by_this_review':False,'original_criteria_and_review_preserved':True,'writes_limited_to':'reviews/source_context/revision-review.json/md and build_revision_review.py'},'not_claimed':['未开展新模型问答运行','未改历史评分','不是全部85项全维度设计验收','不是正式模型/Skill采纳','不是指标执行或客户验收'],'findings':[],'business_decisions_needed':[]}
(out/'revision-review.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
md=['# 来源上下文专项修订复审',f'复审时间（UTC）：{now}','结论：F07、A02、A03、E06四题修订通过来源语义复审；其余十题全文未改，保留首审通过结论。10处建议与实际候选、变更清单精确一致。0模型API。',f"候选预期 SHA256：`{data['candidate_expected_sha256']}`。",'本结论仅覆盖本组14题来源语义，不表示85项全维度设计、实际问答、指标执行或正式采纳通过。','## 修订核对']
for id in changed:md += [f'- {id}：{why[id]}']
md += ['## 冻结输入的可见范围','核对了历史input/manifest.json、materials_index.json登记值，并逐条比较渲染文本与原始访谈；完整消息内容一致，未只靠字符串命中判断。']
for v in visible:md += [f"- {v['case_id']} `{v['rendered_path']}`：SHA256与两份登记一致；原文完整可见。"]
md += ['E06-02含03931全文及“但审批安排还没定”，A03-01含03932提问方付款安排总结和03933回复；F07-01/02分别含完整老周访谈、07沟通文档。A02-01亦是完整王经理访谈。','新增reviewer sources是评审定位修订，没有改变模型输入。全局判读规则允许等价表达，不能把逐字引用变成新的通过条件，也不能要求模型引用不可见原句。若以后重新裁剪材料，需重新核输入。','## 保留情况','原input、原始来源及独立判据哈希未变；原审查记录、历史答案与分数均未改。本复审只写本子目录，新候选模型的01731措辞由model组负责审查。','无新增来源语义问题，无需本人决定的新业务取舍。']
(out/'revision-review.md').write_text('\n\n'.join(md)+'\n')
print(json.dumps({'status':data['status'],'counts':data['counts'],'candidate_sha256':data['candidate_expected_sha256']},ensure_ascii=False))
