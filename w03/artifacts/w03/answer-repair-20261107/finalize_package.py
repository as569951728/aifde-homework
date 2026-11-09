"""Publish reviewed repair results and continuity; never calls or grades a model."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
REPO = ROOT.parent.parent

def read(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save_new(p, value):
    with p.open('x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    ledger = read(BASE / 'execution_ledger.json')
    final = [x for x in ledger['executions'] if x['stage'] == 'stage5-compact-evidence']
    assert len(final) == 22
    passed = sum(x['verdict'] == 'passed' for x in final)
    failures = [x['id'] for x in final if x['verdict'] == 'failed']
    no_answers = [x['id'] for x in final if x['native_status'] != 'succeeded']
    reviewed = read(BASE / 'stage5-compact-evidence/independent-review/review.json')
    assert reviewed['summary']['semantic_passed'] == passed
    all_pass = passed == len(final)
    verdicts = {x['id']: x['verdict'] for x in final}
    now = datetime.now(timezone.utc).isoformat()
    next_step = ('在最新同一提示下补核尚未重跑的66道原题，再整理正式采用候选；不重复已执行22题。'
                 if all_pass else '基于U01证据卡，准备区分“已知/待核”和保留三类对象名称的隔离正文澄清候选及固定验证范围；不继续堆提示或无变化抽样，未通过前不替换正式模型或Skill。')
    status = f'最新版本22题：{passed}通过、{len(failures)}语义失败、{len(no_answers)}技术无答。'
    rows = []
    for batch in ledger['batches']:
        v = batch['verdicts']
        rows.append(f"| {batch['stage']} | {batch['native_runs']} | {batch['http_attempts']} | {v.get('passed', 0)} | {v.get('failed', 0)} | {batch['native_runs'] - batch['native_successes']} |")
    closure = []
    for row in ledger['failure_closure']:
        value = '通过' if row['final_verdict'] == 'passed' else row['final_verdict']
        closure.append(f"| {row['id']} | {row['origin']} | {value} |")
    counts = ledger['counts']
    expansions = [f"{x['stage']}/{x['id']}" for x in ledger['executions'] if x['http_attempts'] > 1]
    expansion_note = '、'.join(expansions) or '无'
    report = f'''# W03 模型问答修复结果

2026-11-07；导师实际执行，两位独立评审按18+4题分工审核，另由独立审计检查汇总。本人授权修复，不登记为本人独立作答或客户采纳。

**{status}** 语义失败：{', '.join(failures) or '无'}；技术无答：{', '.join(no_answers) or '无'}。

本轮修改隔离的回答提示，业务模型正文保持同一候选。原11个失分项、本轮出现的U04回退和TRACECTRL01来源错误均纳入最新版本检查；逐项结果见下表。实际回答由模型重新生成，导师给出的修正示范不计模型通过。

## 修了什么、怎样查

- 来源：核对提问预设、回答承接、新观察及限定语；来源不明保持待核，不改写成已不同或已发生。有效W02材料仍按实际适用范围使用。
- 数量与计算：不补题目未给的卡数；分别核分子、分母和金额单位；逐项日期条件判定后再合并，不用整体无效替代每个条件。
- 表达与格式：严格保留原生JSON要求，未放宽解析器。证据审查最终采用每项一份“判定—可记录内容—直接依据与缺口”，取消表格后再次全文复述。
- 验证：原题、原材料、原预期和业务模型均冻结；新对照由独立评审设计，包含合理角色观察、已知可比条件、不完整卡记录、格式转义及排班来源迁移。每版先审输入再运行，原生调用与答案、独立评分均留存。

## 各版本真实结果

| 版本 | 原生运行 | HTTP尝试 | 语义通过 | 语义失败 | 技术无答 |
| --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

合计{counts['native_runs']}次原生运行、{counts['http_attempts']}次HTTP、{counts['successful_native_answers']}份原生合格格式答复，覆盖{counts['unique_original_questions']}道不同原题和{counts['unique_controls']}道不同控制题。多版本重复执行分别计数，不称为同数量的不同问题。框架按已确认截断扩容的题为{expansion_note}，额外HTTP另计；Stage1、Stage4各有1次无响应网络失败。两个网络恢复准备均取消、未调用；语义/格式失败没有同版本重抽样。

阶段3的E01回退、阶段4的U05和TRACECTRL01失败均保留。不能从“长回答后出错”推定长度就是原因；最终版本的改变及实测结果分别记录。

## 历史失分项在最新版本的结果

| 项目 | 失分来源 | 最新结果 |
| --- | --- | --- |
{chr(10).join(closure)}

## 适用边界与下一步

原全套结果仍为71/82完整通过、10语义失败、1格式失败，原记录不改分。最新提示验证了16道原题及6道控制题；另外66道原题未在最新提示重跑，不能拼成“新版本82/82通过”。静态审查与数值指标验证另计。

正式模型仍为W02 v0.4；现用Skill、正式提示、awaiting_apply工作流及旧proposal3未替换。38项指标查询/独立数值验证未在本轮执行。没有新增需本人裁决的业务事实；这一轮解决的是作答机制与证据一致性。

**下一小步：** {next_step}

尚未修好的U01涉及两处：把定义/范围/时点/来源待核写成已不同，以及改写“统计人群、待业务审核的候选人群、实际执行名单”的原分类。已另存[导师证据核对与待验证修订](U01-证据核对与待验证修订.md)，只修正两处并提出正文表述澄清；这份稿不是模型新答，不计入通过率。正文未决表的压缩措辞可能引入歧义，但没有证据证明它导致了本次模型错误。

核查入口：[最新逐题评审](stage5-compact-evidence/independent-review/review.md)、[完整执行账本](execution_ledger.json)、[历史全套结果](../full-validation-20261107/结果速览.md)。最终汇总审核单独保存在aggregate-review，未出结论前不得写为审核通过。
'''
    report_path = BASE / '修复结果.md'
    assert not report_path.exists()
    report_path.write_text(report)
    matrix_path = BASE / 'issue_matrix.json'
    matrix = read(matrix_path)
    save_new(BASE / 'progress-history/issues-before-final.json', matrix)
    for item in matrix['items']:
        item.update(latest_observed_stage='stage5-compact-evidence', latest_observed_verdict=verdicts[item['id']],
                    regression_pass=verdicts[item['id']] == 'passed',
                    repair_status='passed_latest_targeted_regression' if verdicts[item['id']] == 'passed' else 'unresolved')
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + '\n')
    progress_path = BASE / 'progress.json'
    progress = read(progress_path)
    save_new(BASE / 'progress-history/before-final.json', progress)
    progress.update(updated_at=now, status='targeted_results_recorded_pending_aggregate_review',
                    actual_model_calls=counts['native_runs'], http_attempts=counts['http_attempts'])
    progress['stages']['stage5-compact-evidence'].update(actual_calls=22, status='independently_reviewed',
        native_answers=22-len(no_answers), semantic_pass=passed, semantic_fail=len(failures), failed_ids=failures,
        network_no_answer_ids=no_answers, http_attempts=sum(x['http_attempts'] for x in final),
        completed_case_records=22, started_case_records=22, pending_case_ids=[])
    progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n')
    (BASE / 'README.md').write_text('# 问答修复与针对性回归\n\n' + status + '\n\n见[修复结果](修复结果.md)与[逐次执行账本](execution_ledger.json)。原11失败及调优中新失败均保留；最新版本仅覆盖16道原题与6控制，不宣称全82通过。正式模型与Skill未替换。\n')

    before = read(BASE / 'before-continuity/manifest.json')
    continuity = {'recorded_at': now, 'files': {}}
    for relative, old in before['files'].items():
        path = REPO / relative
        assert sha(path) == old['before_sha256'], 'continuity changed concurrently: ' + relative
        content = path.read_text()
        result_link = os.path.relpath(report_path, path.parent)
        if path.name == 'W03-学习笔记.md':
            insertion = f'''\n2026-11-07修复实操补充：{status} 导师执行与独立审核见[修复结果]({result_link})；不登记为本人独立掌握。\n\n概念速查：证据状态要在转述中保留。未知不等于已不同，回答重复提问前提不等于独立证实；后续新增信息不能挂到前条消息。使用时每个判断记录直接依据与缺口，避免多次复述改变主体或限定。日期先判各条件再合并；例：计划已结束可以使整卡无效，但不能因此把尚未触发的提前终止条件判为不满足。需记住上述区分，具体消息号查原文即可。\n\n针对性回归只证明本版已执行的范围：最新22题含16道原题和6控制，不能与旧版成绩拼成新82/82。来源为本次真实失败与独立复审，非新增青禾业务事实。\n'''
            head, rest = content.split('\n', 1)
            content = head + '\n' + insertion + '\n' + rest
        else:
            marker = '**全套验证停点（2026-11-07，最新）：**'
            assert content.count(marker) == 1
            new = f'''**修复验证停点（2026-11-07，最新）：** {status} 原11失分项及调优中新出现的U04、TRACECTRL01均按新原答独立复审；历史失败保留。见[修复结果]({result_link})。\n\n**当前边界与下一步：** 最新提示只测16道原题+6控制，其余66原题未在本版重跑，不合并为新82/82。{next_step} 正式模型仍W02 v0.4、Skill/正式提示/awaiting_apply及旧proposal3未替换，38项指标数值验证未运行。导师执行不登记为本人独立作答；无新增待本人业务裁决。以下为历史停点。\n\n'''
            content = content.replace(marker, new + '**全套验证停点（2026-11-07，历史）：**', 1)
        path.write_text(content)
        continuity['files'][relative] = {**old, 'after_sha256': sha(path)}
    save_new(BASE / 'continuity_manifest.json', continuity)
    completion = {'status': 'results_recorded_pending_aggregate_review', 'recorded_at': now,
        'result': 'targeted_regression_passed' if all_pass else 'repair_not_fully_passed',
        'counts': counts, 'latest': {'stage': 'stage5-compact-evidence', 'cases': 22,
            'passed': passed, 'semantic_failed_ids': failures, 'technical_no_answer_ids': no_answers},
        'failure_closure': ledger['failure_closure'], 'report': '修复结果.md',
        'ledger_sha256': sha(BASE / 'execution_ledger.json'), 'report_sha256': sha(report_path),
        'continuity_manifest_sha256': sha(BASE / 'continuity_manifest.json'),
        'formal_model_applied': False, 'formal_prompt_or_skill_replaced': False,
        'metric_queries_executed': 0, 'next_step': next_step}
    save_new(BASE / 'completion.json', completion)
    print(json.dumps({'latest': completion['latest'], 'counts': counts, 'continuity_files': len(continuity['files'])}, ensure_ascii=False))

if __name__ == '__main__':
    main()
