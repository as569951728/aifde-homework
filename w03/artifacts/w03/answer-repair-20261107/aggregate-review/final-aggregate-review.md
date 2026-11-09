# 最终独立汇总审核

结论：**汇总与留档审核通过；候选修复仍未全部通过。** 未发现实质性计数、来源、版本混算或失败覆盖问题。本审核未调用模型 API、未改受审包、未重评原答语义。

| 实际版本 | 原生运行 | HTTP | 语义通过 | 语义失败 | 技术无答 |
| --- | ---: | ---: | ---: | ---: | ---: |
| stage1 | 18 | 18 | 15 | 2 | 1 |
| stage1-r2 | 18 | 19 | 18 | 0 | 0 |
| stage2-r2 | 8 | 8 | 8 | 0 | 0 |
| stage3-r2 | 17 | 17 | 16 | 1 | 0 |
| stage4-evidence-trace | 22 | 22 | 19 | 2 | 1 |
| stage5-compact-evidence | 22 | 23 | 21 | 1 | 0 |
| 合计 | 105 | 107 | 97 | 6 | 2 |

共103份原生合格格式答复，涉及21道不同原题、8道不同控制题。两次额外HTTP分别来自stage1-r2/REG01和stage5/A03的框架既定截断扩容。四个未执行批（包括两次取消的网络恢复准备）均为0调用。

最新Stage5仅覆盖16道原题与6道控制；21/22通过，**U01仍失败**。原11个失分项本版10项通过；新增历史失分U04和TRACECTRL01本版通过。13项历史失分及所有旧原答/旧分完整保留。其余66道原题没有按最新提示重跑，不能将跨版结果拼成82/82。

已独立核对105条账本到原生run、output、实际输入与语义评审的对应关系；Stage5的18题来源审查与4题数学/日期/格式审查分工完整、互不重叠。结构核验通过；终包校验1162项通过。详见[机械核验](final-integrity-check.json)与[终包校验](final-package-check.json)。

六份接续文件的before/after哈希与清单一致。五个入口仅增加当前停点，并将旧“最新”标题改为“历史”；学习笔记只增加内容。既有历史文字逐字保留，未把导师工作登记成本人独立掌握。完整差异见[接续差异](reviewed-continuity.diff)。

正式W02 v0.4、候选业务正文、12项保护、现用Skill/正式提示、旧proposal-3及awaiting_apply状态未变化；未执行38项指标数值验收、apply或客户验收。U01导师核对稿仅替换原答两处，15项静态审核通过；审核前完整稿、现稿和不变的核对正文哈希均可追溯。它不是模型新答，U01失败和21/22结果未改。

**允许的最后封包范围：** completion.json仅可更新status并添加aggregate_review、aggregate_review_path、aggregate_review_sha256、aggregate_review_status等本审核引用字段；progress.json仅可把status改为reviewed_with_unresolved_failure。所有结果、计数、闭环、原分及其他受审正文不变。已保留[受审completion快照](reviewed-completion.json)与[受审progress快照](reviewed-progress.json)；主控须另存最终字段差异与hash核验，超出范围须重审。

两处非阻断追踪文字：U01核对稿中的“下一步先独立审”保留了先前计划，当前已通过状态由顶部、15项审核及metadata明确；progress/issue_matrix中的possible与target_stage属于原追踪/计划字段，当前结论以failed_ids及latest_observed字段为准。无需为此改动已审正文。
