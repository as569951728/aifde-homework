"""Record independently reviewed results and continuity. No model calls or grading."""
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
REPO = ROOT.parent.parent

def read(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save_new(p, obj):
    with p.open('x') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def main():
    rows, stages = [], []
    for stage in ['qa-01', 'qa-02-u05-recovery']:
        b = BASE / stage
        review_path = b / 'independent-review/review.json'
        review = read(review_path)
        grades = {x['id']: x for x in review['cases']}
        audit = read(b / 'protocol_audit.json')
        assert not audit['index_errors']
        selected = read(b / 'input/selected_questions.json')['cases']
        assert set(grades) == {x['id'] for x in selected} == {x['id'] for x in audit['cases']}
        for item in audit['cases']:
            assert item['audit_status'] == 'passed' and not item['errors']
            cid = item['id']; p = b / 'output' / (cid + '.json')
            output = read(p); grade = grades[cid]; native = ROOT / output['result']['run']
            assert sha(p) == grade['output_sha256'] == item['output_sha256']
            assert sha(native) == grade['native_run_sha256']
            if grade['verdict'] == 'passed':
                assert output['status'] == 'succeeded' and isinstance(output['actual_answer'], str)
            rows.append({'stage': stage, 'id': cid, 'verdict': grade['verdict'],
                'native_status': output['status'], 'http_attempts': item['api_attempt_count'],
                'output': str(p.relative_to(ROOT)), 'output_sha256': sha(p),
                'native_run': str(native.relative_to(ROOT)), 'native_run_sha256': sha(native),
                'review': str(review_path.relative_to(ROOT)), 'review_sha256': sha(review_path),
                'reason': grade['reason']})
        stages.append({'stage': stage, 'review_sha256': sha(review_path),
            'protocol_audit_sha256': sha(b / 'protocol_audit.json'), 'summary': review['summary']})
    latest = {x['id']: x for x in rows}
    assert len(latest) == 6 and len(rows) == 7
    unresolved = [x['id'] for x in latest.values() if x['verdict'] != 'passed']
    passed = len(latest) - len(unresolved)
    counts = {'unique_cases': 6, 'passed_cases': passed, 'unresolved_ids': unresolved,
        'original_cases': 5, 'control_cases': 1, 'native_runs': len(rows),
        'http_attempts': sum(x['http_attempts'] for x in rows),
        'successful_native_answers': sum(x['native_status'] == 'succeeded' for x in rows),
        'original_82_not_rerun_on_new_body': 77}
    assert latest['U01']['stage'] == 'qa-01'
    ledger = {'client_date': '2026-11-08', 'counts': counts, 'stages': stages, 'executions': rows,
        'current_case_results': list(latest.values()), 'original_qa01_U05_retained': True,
        'technical_recovery_selection_rule': 'QA01 U05 has no complete answer; one pre-approved new run only, not best-of semantic selection',
        'formal_model_applied': False, 'prompt_or_skill_replaced': False, 'metric_queries_executed': 0}
    save_new(BASE / 'execution_ledger.json', ledger)
    verdict_label = lambda x: '通过' if x == 'passed' else ('语义未通过' if x == 'failed' else '技术未完成')
    labels = {'U01': '业务目标与关键未知', 'U05': '材料证据审查', 'E03': '两项人数可比性',
        'REG01': '运营支持建议', 'P01': '资格判断正例', 'CTRL02': '可比条件明确的计算正例'}
    table = '\n'.join(f"| {cid} | {labels[cid]} | {verdict_label(r['verdict'])} | {'单独技术恢复' if r['stage'] != 'qa-01' else '首批新答'} |" for cid, r in latest.items())
    status = f'本次局部回归{passed}/6通过；U01为{verdict_label(latest["U01"]["verdict"])}。'
    next_step = ('冻结本次正文与既有提示，核对并分批接续其余77道原题的覆盖；不把旧版分数填入新版。'
                 if not unresolved else '单独处理' + '、'.join(unresolved) + '的引用生成：将断言、消息编号和原句逐项绑定再复核；保留本轮原答，暂不继续改正文/提示或重抽样，不直接采用。')
    report = f'''# W03 U01 正文澄清与验证结果

2026-11-08。**{status}** 尚未完成项：{('、'.join(unresolved)) or '本轮六题无'}。

本轮由导师整理与实际执行，新独立来源评审先读原访谈再审候选，另一独立评审按冻结判据逐答审核。不是本人独立作答或客户新增确认。

## 正文改动

1. 将第5节中压缩的“范围不同”展开：保留沈总80万活跃、老周120万全量及老周明确说不同口径的陈述；具体定义、范围、时点和统计来源仍待核。
2. 将规则5原有三个名称分别列出：统计人群、待业务审核的候选人群、实际执行名单。保留不可等同，不引入互斥集合、审批阶段或筛选规则。

除此两处和标题版本，业务正文原样；Stage5提示、原题、预期、源材料与运行策略均未改。取舍过程保留在[变更说明](变更说明.md)，业务正文只保存业务知识。[候选正文](candidate/business_model.md) · [来源审查](independent-review/candidate-review.md)。

## 实际验证

| 用例 | 检查对象 | 当前结果 | 答复来源 |
| --- | --- | --- | --- |
{table}

首批6次原生运行、7次HTTP：5份完整答复通过；U05先在8192上限截断，框架按原策略扩至16384时遇网络中断。首个公开部分文本和两次尝试均保留；U05原记录仍为技术不可判。

独立新门禁批准U05仅一次新的隔离原生运行。正文、提示、完整问题、材料和参数与原请求相同，未送入部分答案、纠错或预期；不是workflow resume，也未对完整语义失败重抽。恢复结果为{verdict_label(latest['U05']['verdict'])}，原失败未覆盖。全轮共{counts['native_runs']}次原生运行、{counts['http_attempts']}次HTTP、{counts['successful_native_answers']}份完整原生答复；6道不同题，不能按运行次数称为7道题。

U05本次A—E主要业务判断基本正确，但将MSG-01921的后续限定具体挂到MSG-01919，又把“不构成审批或承诺”作为MSG-03911的原句引用。来源定位和引用准确性仍未通过。已另存[导师引用核对稿](U05-引用核对稿.md)，修正稿的静态审核与模型原答分数分别记录，不将导师改答计作新运行通过。

[首批逐题评审](qa-01/independent-review/review.md) · [U05恢复评审](qa-02-u05-recovery/independent-review/review.md) · [完整执行账本](execution_ledger.json)。

## 结论边界

U01按新原答评分，未用导师核对稿或旧通过答复替代。语义等价的名称简写、顺序变化按完整上下文判断，不要求逐字背诵；不可丢掉统计集合或把候选拆成两个审批阶段。报告保留出处定位与措辞的非阻塞建议，不把“已通过”说成所有表达完美。

本版只覆盖5道原题和1道控制；其余77道原题未在这份新正文上重跑。此前21/22与82题历史结果保持原样，不合并为本版全过。一次局部通过不证明长期稳定，也不能确定正文改动是表现变化的唯一原因。

正式业务模型仍为W02 v0.4，现用提示/Skill未替换；旧proposal3及awaiting_apply未动，不能把旧proposal3当成本次候选直接采用。38项指标查询与独立数值校验未在本轮执行。已有业务待核项仍保留，本次澄清不需要新增业务裁决。

**下一小步：** {next_step}
'''
    report_path = BASE / '验证结果.md'
    with report_path.open('x') as f: f.write(report)
    before = read(BASE / 'before-continuity/manifest.json')
    continuity = {'client_date': '2026-11-08', 'files': {}}
    for rel, old in before['files'].items():
        p = REPO / rel; assert sha(p) == old['before_sha256'], rel
        content = p.read_text(); link = os.path.relpath(report_path, p.parent)
        if p.name == 'W03-学习笔记.md':
            head, rest = content.split('\n', 1)
            addition = f'\n2026-11-08实操补充：{status} 见[正文澄清与验证]({link})。这是导师执行及独立审查，不登记为本人独立掌握。\n\n概念速查：角色明确说“不是同一口径”和具体统计属性尚待核可以同时成立。保留前者，逐属性核后者，避免把所有属性一律判同或判异。对象名称可等义简写，但不能改变集合身份。完整问答、技术失败与补测分别计数；一次局部通过只证明已测范围。来源：本轮原访谈审查与新原答，不是新增客户事实。\n'
            content = head + '\n' + addition + '\n' + rest
        else:
            marker = '**修复验证停点（2026-11-07，最新）：**'
            assert content.count(marker) == 1, rel
            addition = f'**正文澄清停点（2026-11-08，最新）：** {status} 原题/预期/提示保持，正文两处澄清及标题更新已独立审查。U05首批混合技术失败保留，单独恢复结果见[验证报告]({link})；本轮7次原生运行/{counts["http_attempts"]}次HTTP，6道不同题。\n\n**当前边界与下一步：** 新正文仅测5道原题+1控制，77道原题未在本版重跑。{next_step} 正式模型v0.4、Skill/提示、旧proposal3与awaiting_apply未替换；38项指标数值验证未运行。导师执行不登记为本人独立作答；业务原待核项不自动关闭。以下为历史停点。\n\n'
            content = content.replace(marker, addition + '**修复验证停点（2026-11-07，历史）：**', 1)
        p.write_text(content)
        continuity['files'][rel] = {**old, 'after_sha256': sha(p)}
    save_new(BASE / 'continuity_manifest.json', continuity)
    completion = {'client_date': '2026-11-08', 'status': 'recorded_pending_final_audit',
        'result': 'bounded_regression_passed' if not unresolved else 'bounded_regression_incomplete',
        'counts': counts, 'candidate_model_sha256': sha(BASE / 'candidate/business_model.md'),
        'unchanged_prompt_sha256': sha(BASE / 'qa-01/input/knowledge_prompt.txt'),
        'ledger_sha256': sha(BASE / 'execution_ledger.json'), 'report_sha256': sha(report_path),
        'continuity_manifest_sha256': sha(BASE / 'continuity_manifest.json'), 'next_step': next_step,
        'formal_model_applied': False, 'skill_replaced': False, 'metric_queries_executed': 0}
    save_new(BASE / 'completion.json', completion)
    (BASE / 'progress.json').write_text(json.dumps({'client_date': '2026-11-08',
        'status': 'results_recorded', 'counts': counts, 'report': '验证结果.md',
        'next_step': next_step}, ensure_ascii=False, indent=2) + '\n')
    (BASE / 'README.md').write_text('# W03 U01 正文澄清与局部验证\n\n' + status + '\n\n见[验证结果](验证结果.md)。原失败与正式模型保留；六题局部回归不等于新版本82题全部通过。scope.json为初始准备快照，当前状态见progress.json与completion.json。\n')
    print(json.dumps(counts, ensure_ascii=False))

if __name__ == '__main__':
    main()
