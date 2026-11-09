# 独立输入与预期核查

结论：17题作者预期与来源优先判据无业务冲突，全部冻结文件、题目等同性、model_only轨道、正式文件保护hash及运行器hash通过。

C05 作者预期列出的 L-03848/03868 和会员运营周报可支持资格与购买区分，但活跃未知宜同时引用 W02 老周 MSG-01745–01746/01754；独立判据已有该原文支持，此为来源清单补全，不是业务冲突。

U02 原始判据中本期月报复购公式是原材料可支持的具体例，不将背出完整公式和零分母作为本题概念说明的额外通过门槛；题面及作者预期要求区分群体指标、范围及定义与结果。答复如主动写公式必须正确且限定范围。此说明在读取任何实际答案前保存；原 source-first-criteria 文件不覆盖。

run_batch.question_for 仅拼本题题面和fixture；execute传expected空串；natural_knowledge.messages_for 只建立system GUARD+知识表达prompt以及 user{business_model,question}；model.complete(messages,[])不载其他题或期望；每题独立ContextModel和Agent runtime。原extraction元数据仅原生流程校验，不进入messages。

仍须实际request逐份核对。preflight的0调用不算实际QA成功。运行器对已保存output跳过，但runner_error没有同名output，若未来重调会再次请求；本批不得人工重跑失败以挑过。
