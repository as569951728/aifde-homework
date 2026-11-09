"""Adopt this pair only after both independent final reviews and native results pass."""
import copy
import hashlib
import json
from pathlib import Path

B = Path(__file__).resolve().parent
ROOT = B.parents[2]
REL = B.relative_to(ROOT).as_posix()
rd = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def save(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")

def main():
    assert not (B / 'completion.json').exists(), 'Preserve completed versions'
    review_paths = [f'{REL}/independent-b3/query-review-v1.json', f'{REL}/independent-b4/final-review-v1.json']
    reviews = [rd(ROOT / p) for p in review_paths]
    corrections_path = f'{REL}/independent-b3/reviewed-corrections-v1.json'
    corrections = rd(ROOT / corrections_path)
    assert not reviews[0]['approved_for_batch_closeout']
    assert reviews[1]['approved_for_batch_closeout'] and not reviews[1]['failed_checks']
    assert corrections['approved_for_supervised_closeout'] and not corrections['failed_checks']
    assert set(corrections['corrected_case_ids']) == {'B3-U01','B1-Z01'}
    for r in reviews + [corrections]:
        for p, h in r['evidence_sha256'].items():
            assert sha(ROOT / p) == h, p
    reports = [rd(B / f'test-{s}-v1/metric_test_report.json') for s in ('new', 'regression', 'fixture')]
    assert [r['total'] for r in reports] == [12, 21, 1]
    assert all(r['complete'] and r['passed'] == r['total'] for r in reports)
    actual_cases = [c for r in reports for c in r['cases']]
    assert len({c['id'] for c in actual_cases}) == 34
    reviewed = [cid for r in reviews for cid in r['reviewed_case_ids']]
    assert len(reviewed) == len(set(reviewed)) == 34
    assert set(reviewed) == {c['id'] for c in actual_cases}
    for file in ['b3-result-controls.json', 'judge-injections-v1.json']:
        assert rd(B / file)['status'] == 'passed', file
    # B4's final review includes its own real-result-copy controls and hashes.
    guard = rd(B / 'protected.json')
    assert all(sha(ROOT / p) == h for p, h in guard.items())
    for i in (3, 4):
        f = rd(B / f'independent-b{i}/expected-freeze.json')
        inputs = f['sources'] if i == 3 else f['inputs_sha256']
        outputs = f['files'] if i == 3 else f['outputs_sha256']
        assert all(sha(ROOT / p) == h for p, h in inputs.items())
        assert all(sha(B / f'independent-b{i}' / p) == h for p, h in outputs.items())
    tests = rd(B / 'tests-small-all.json')
    old_tests = rd(B / 'before/customer/w03/tests.json')
    assert tests[12:] == old_tests == rd(ROOT / 'customer/w03/tests.json')
    assert rd(B / 'tests-fixture-b2.json') == rd(ROOT / 'customer/w03/tests-fixtures/b2-order-boundaries.json')
    bindings = [rd(B / f'version-binding-{s}-v1.json') for s in ('new','regression','fixture')]
    assert len({d['catalog_sha256'] for d in bindings}) == 1
    assert bindings[0]['data_sha256'] == bindings[1]['data_sha256'] != bindings[2]['data_sha256']
    traces = [B / 'build-v1/trace.json']
    for sub in ('new', 'regression', 'fixture'):
        traces += sorted((B / f'test-{sub}-v1/traces').glob('*/*-trace.json'))
    calls = [{'trace': str(p.relative_to(ROOT)), 'http_attempts': len(rd(p)['call']['attempts'])} for p in traces]
    audit = dict(logical_model_calls=len(calls), http_attempts=sum(c['http_attempts'] for c in calls),
                 build_runs=1, natural_language_tests=34, successful_sql_queries=sum(c['actual']['status']=='ok' for c in actual_cases),
                 calls=calls, protected_files=len(guard), all_protected_unchanged=True,
                 original21_questions_and_business_expectations_unchanged=True,
                 skill_judge_config_business_model_unchanged=True, fixture_separate=True,
                 combined_report_is_derived_index=True)
    save(B / 'execution-audit.json', audit)
    scope = rd(B / 'scope.json')
    completion = dict(status='B3_B4_numeric_complete_with_reviewed_answer_corrections', batches=['B3','B4'],
                      cumulative_metric_count=24, new_metrics=scope['new_metrics'],
                      small_passed=33, small_total=33, small_new_questions=12, small_regression_questions=21,
                      fixture_passed=1, fixture_total=1, explanations_passed=32, explanations_total=34,
                      original_explanation_failed_cases=['B3-U01','B1-Z01'], reviewed_corrections_passed=2,
                      correction_review=corrections_path, automatic_answer_pipeline_fixed=False,
                      library=f'{REL}/library-v1', primary_project=bindings[0]['project'], fixture_project=bindings[2]['project'],
                      reviews=review_paths, scale_run=False, next_pair=['B5','B6'], next_cumulative_metric_count=32,
                      native_reports=[f'{REL}/test-{s}-v1/metric_test_report.json' for s in ('new','regression','fixture')],
                      derived_small_index=f'{REL}/combined-small-report.json',
                      data_bindings=bindings, attribution='导师执行，独立Agent审核；不记作本人独立掌握、客户验收或提交')
    reg = rd(ROOT / 'customer/w03/metric_register.json')
    reg.update(version='w03-metric-register-v4', updated_at='2026-11-08',
               purpose='每轮两批，独立冻结与核查；统一汇报，不逐指标停点',
               execution_review=review_paths, correction_review=corrections_path, current_library=completion['library'])
    for batch in reg['batches']:
        if batch['id'] in ['B1','B2','B3','B4']:
            batch.update(status='completed_small', current_regression_reference=f'{REL}/completion.json')
            if batch['id'] in ['B3','B4']:
                batch.update(already_small_passed=batch['new_scope_metric_ids'],result_reference=f'{REL}/completion.json')
        elif batch['id'] in ['B5','B6']:
            batch['status']='next_pair'
    for m in reg['metrics']:
        if m['batch'] not in ['B1','B2','B3','B4']: continue
        m['before_B34_reference']=f'{REL}/before/customer/w03/metric_register.json#{m["id"]}'
        review = review_paths[1 if m['batch']=='B4' else 0]
        m.update(build_status='B3+B4累计24项build-v1/library-v1已构建加载',
                 current_adopted_library_scope='B1至B4累计24项小样本库',result_reference=f'{REL}/completion.json',
                 review_reference=review,catalog_sha256=bindings[0]['catalog_sha256'])
        if m['batch'] in ['B3','B4']:
            m.update(definition_status='已核字段、粒度、ordered_at、单位与范围',
                     test_design_status='6道多指标small题通过；专项解释/副本负例另记',
                     expected_status='原CSV独立核算，构建/查询前冻结',small_status='6/6本批题通过',
                     explanation_status='6份原生回答通过独立审核' if m['batch']=='B4' else '6份原生回答5通过、1含退款账户错句；另有已审导师纠正稿',
                     known_pending='规模、未见问法及其他维度行为待后续；自动解释2条原失败未修管线，交付材料用已审修订；无新业务缺口',
                     expected_reference=f'{REL}/independent-{m["batch"].lower()}/tests-new-small.json')
            if m['batch']=='B4':
                m['test_case_ids']=[c['id'] for c in tests[:12] if c['id'].startswith('B4-')]+['B4-U01']
        else:
            m['small_status']='B34累计库已回归本指标原题；原21题整体通过'
            m['explanation_status']='本指标对应原生回答已审；B1-Z01日期错句用已审导师纠正稿' if m['batch']=='B1' else 'B34对应完整回答通过独立审核'
        if m['batch'] in ['B1','B3']:m['correction_review_reference']=corrections_path
    reg['summary'].update(metrics_with_frozen_existing_tests=24,metrics_with_small_pass=24,metrics_with_scale_pass=0,
        existing_real_cases=34,native_small_tests=33,isolated_fixture_tests=1,new_design_entries=56,
        new_design_query_entries_executed=26,new_design_auxiliary_entries_checked=2,
        new_design_answer_audit_entries_checked=1,new_design_expanded_parent_entries=1,new_design_entries_not_run=26,
        new_model_calls=audit['logical_model_calls'],new_queries=audit['successful_sql_queries'],
        new_http_attempts=audit['http_attempts'],last_batch='B3+B4',next_batch='B5+B6',
        original_explanations_passed=32,original_explanations_total=34,reviewed_answer_corrections=2,
        automatic_answer_pipeline_fixed=False)
    plan=rd(ROOT / 'customer/w03/test-plans/metric_cases.json')
    plan.update(version='w03-metric-test-plan-v6',status='24_metrics_numeric_passed_2_explanations_corrected_in_separate_copies',
                rule='每轮两批。small33及fixture1题数值通过，原解释32/34；2条导师纠正稿已独立审核，不改原分。另2辅助、1解释专项、1拆分父项；余26设计未执行。')
    parent=next(c for c in plan['cases'] if c['id']=='B4-D01')
    for cid in ('B4-D01-store','B4-D01-all'):
        c=copy.deepcopy(parent);c.update(id=cid,parent_design_id='B4-D01');plan['cases'].append(c)
    all_tests={c['id']:c for c in tests+rd(B/'tests-fixture-b2.json')}
    for c in plan['cases']:
        if c['id'] in all_tests:
            t=all_tests[c['id']];is_fixture=c['id']=='B2-Z01'
            sub='fixture' if is_fixture else ('new' if c['id'].startswith(('B3-','B4-')) else 'regression')
            review=review_paths[1 if c['id'].startswith('B4-') else 0]
            c.update(before_B34_reference=f'{REL}/before/customer/w03/test-plans/metric_cases.json#{c.get("parent_design_id",c["id"])}',
                     state='passed_on_B34_library_v1',executable=True,expected_state='frozen_before_build_and_actual',
                     execution_state='passed_and_explanation_reviewed',execution_question=t['question'],question_or_fixture=t['question'],
                     expected_reference=f'{REL}/'+('tests-fixture-b2.json' if is_fixture else 'tests-small-all.json')+'#'+c['id'],
                     result_reference=f'{REL}/test-{sub}-v1/metric_test_report.json#{c["id"]}',review_reference=review,
                     data_version=bindings[2 if is_fixture else 0]['data_version'],catalog_sha256=bindings[0]['catalog_sha256'],
                     dataset_kind='artificial_isolated_fixture' if is_fixture else 'course_small')
            if c['batch'] in ['B3','B4']:c['data_state']='原small CSV独立逐单/账户/分子分母台账；未新建fixture'
            if c['id']=='B3-U01':
                c['coverage_limit']='原样本分别覆盖多卡多单、重复退款、同额不同账户；未覆盖同账户同时多卡且多次退款的组合。'
            if c['id'] in ['B3-U01','B1-Z01']:
                c.update(state='numeric_passed_original_explanation_failed_reviewed_copy_available',
                         execution_state='native_numeric_passed_explanation_failed',
                         correction_reference=f'{REL}/mentor-corrections/{c["id"]}.json',
                         correction_review_reference=corrections_path,automatic_pipeline_fixed=False)
        elif c['id']=='B4-D01':
            c.update(state='expanded_parent_completed',executable=False,execution_state='children_passed',
                     expected_state='frozen_as_two_child_cases',child_case_ids=['B4-D01-store','B4-D01-all'],
                     result_reference=f'{REL}/test-new-v1/metric_test_report.json',review_reference=review_paths[1])
        elif c['id']=='B4-U01':
            c.update(state='answer_audit_passed',executable=False,execution_state='six_existing_answers_reviewed',
                     expected_state='unit_contract_frozen',reviewed_case_ids=[t['id'] for t in tests[:12] if t['id'].startswith('B4-')],
                     result_reference=review_paths[1],new_query_count=0)
    plan['common_design']['B34_current_evidence']=dict(reviews=review_paths,generic_controls=f'{REL}/judge-injections-v1.json',
        b3_controls=f'{REL}/b3-result-controls.json',b4_controls='见B4独立最终审核的实际返回副本控制及哈希',
        combined_report_is_derived_index=True,fixture_separate=True)
    assert len(plan['cases'])==64 and sum(c.get('executable',False) for c in plan['cases'])==34
    assert len({c['id'] for c in plan['cases']})==64
    # No change to the 14 unexecuted metric definitions or 26 later design entries.
    old_reg=rd(B/'before/customer/w03/metric_register.json')
    old_plan=rd(B/'before/customer/w03/test-plans/metric_cases.json')
    assert [m for m in reg['metrics'] if m['batch'] in ['B5','B6','B7']]==[m for m in old_reg['metrics'] if m['batch'] in ['B5','B6','B7']]
    assert [c for c in plan['cases'] if c['batch'] in ['B5','B6','B7']]==[c for c in old_plan['cases'] if c['batch'] in ['B5','B6','B7']]
    save(ROOT/'customer/w03/tests.json',tests)
    save(ROOT/'customer/w03/metric_register.json',reg)
    save(ROOT/'customer/w03/test-plans/metric_cases.json',plan)
    save(B/'completion.json',completion)
    save(B/'bookkeeping-update.json',dict(frozen_inputs_snapshot=f'{REL}/before',
        updated_after_execution=['customer/w03/tests.json','customer/w03/metric_register.json','customer/w03/test-plans/metric_cases.json'],
        source_definitions_and_csv_unchanged=True,expected_artifacts_unchanged=True))
    save(B/'progress.json',dict(stage='B3_B4_numeric_complete_reviewed_copies_available',completion=f'{REL}/completion.json',next_pair=['B5','B6'],original_explanation_passed='32/34',reviewed_corrections='2/2',automatic_pipeline_fixed=False))
    print(json.dumps({'status':completion['status'],'small':'33/33','fixture':'1/1','metrics':'24/38','original_explanations':'32/34','reviewed_corrections':'2/2','calls':len(calls)},ensure_ascii=False))

if __name__=='__main__':main()
