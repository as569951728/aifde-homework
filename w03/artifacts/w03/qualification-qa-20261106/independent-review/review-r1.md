# 首批17题实际问答独立回归评审 R1

结果：17 pass，0 needs_revision，0 indeterminate。仅对这17题本次回归成立。

R0的6题实质失败在R1均未再出现，原11题在同一判据下未见实质回归。17题通过；仍保留4题非阻塞表述观察，不将本轮通过写为业务模型全文完备、所有测试通过或生产可用。

模型正文、原题、fixture、预期、GUARD、runner和模型参数不变；仅客户层回答提示变更，配置路径改到隔离副本。批准新提示hash与实际请求逐题一致。

模型 SHA256：`63e0452d7501934cdeed98e7dab7a38c3d3ef7e3d38d59bcdeb63b1a94e620e8`
提示 SHA256：`c2947d4bb17dcd5faf3a4da8740983c4ade6b91310d570ce18e228bfc4beaa63`
运行索引 SHA256：`f8092b72aee38369f94fb910d2d7fd9601900ffa8a7f0353150371cf7378054a`

17份实际请求、原生快照和答案分别核对；各1次成功尝试，无长度/语义重试，无预期、其他题或工具泄漏。正式保护文件hash均不变。

## 逐题

### U02 — pass（R0：needs_revision）

- 七项身份与概念：七项分列，账户不等于自然人、卡可多张、等级与资格分开；付费资格非活跃/购买事实。；资格/有效购买/活跃：规则保持同一卡产品+有效期，支付净额>0才有效购买，活跃定义未知不判负。；例子与不可推出：明确为构造例：金卡账户一有效纳入卡和一失效卡，订单部分有效/全退无效，活跃未知。；复购率：群体指标，定义与结果分开；没有强行补入正文未写出的客户具体指标公式。；R0来源与字段失败复查：有明确来源规则按原范围使用；未笼统归成未确认学员选择，提前终止为空未扩成计划结束为空。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/U02.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-f562fde6c0f44f12bc1ae58a81d9184d/run.json`
- 输出 SHA256：`924adb575b77ec7ba8b66cc11e79d7826426d251a91e5401c90b41f9f98f4afc`
- 首轮问题本轮未再出现：R0-U02-01, R0-U02-02

非阻塞观察：例子中“是否构成复购或复购率变化，也不能由该账户单独得出”把个体复购判断和群体指标写在一起，不够精确。当前例子未给复购定义、统计期间或完整历史，未知结论可成立；若今后已有这些条件，单账户是否复购可以判断，不宜抽象成永远不能判断。此题核心是复购率的群体含义，完整答复没有输出错误的具体复购判定，本轮不判失败。

### U03 — pass（R0：pass）

- 关系基数：账户多卡/多订单、卡订单各归一账户、账户当前归属店与订单成交店分列，门店可多账户/订单。；成交门店：明确归B；A仅归属。；订单用卡：明确现有账户关系不能证明实际用哪卡，需订单—卡使用记录。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/U03.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-043a24fc016c4c3faee78edc30e29421/run.json`
- 输出 SHA256：`a428e21adeeb810c7451e753ae5d3763f765ce1fca12cbe56318cfc23f86db68`

非阻塞观察：“没有直接关系／无关联”按全文明确的本期字典关系边界解读；宜统一为“本期资料未提供直接关联”，避免读成生产业务不存在关联。答案多次明确实际用卡未知并需记录，故未判实质失败。

### P01 — pass（R0：pass）

- 结论：有本期资格。；理由与负例：有效悦享年卡满足，普通等级/购卡实付不能代替规则。；范围：只用完整人工情境，非生产事实。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/P01.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-27fdeeaedec641d3bdb83d57fd182ba2/run.json`
- 输出 SHA256：`19ef3e154b9ec550f3e2766ecd01836a5c5a042ece7796daac49994f6f7e0f7f`

### P02 — pass（R0：pass）

- 结论：有本期资格。；理由与负例：有效家庭季卡满足同卡条件，普通等级/3000分不改变。；范围：完整卡记录与已知状态允许情境判断，正式文件缺失不拦题目结论。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/P02.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-bc6621f26a60425bbb2200b8cca7c593/run.json`
- 输出 SHA256：`269019b477722f7217918286abc09ff01680c8d36b88adc949d0ff33edad514c`

非阻塞观察：仍使用“本期口径下的建模选择”泛称。全文同时逐项指明原访谈依据，并未否定其有来源或将人工条件改成未核，所以按R0同一原则不因该词单独判失败。

### P03 — pass（R0：pass）

- 结论：无本期资格。；理由与负例：唯一悦享卡失效，完整记录无其他合格卡，金卡/金额不补足。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/P03.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-a15296a00f004dc0b4f8da7af72f535f/run.json`
- 输出 SHA256：`329e9a67f5539ea47bd32224087d0f47a30787dd13bbc2409802c4e204994f60`

### P04 — pass（R0：pass）

- 结论：无本期资格。；理由与负例：唯一有效联名卡不纳入，收费/等级不改变。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/P04.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-d42f7e3e0d5a4d6e88f519dbc83704f6/run.json`
- 输出 SHA256：`3eef9dc4a7d2aeedfff07c046e97d825fc1d701d681e690f06aef5277b0c64da`

### P05 — pass（R0：pass）

- 结论：无本期资格。；理由与负例：体验卡产品范围不合，非由0分或普通等级否定。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/P05.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-9276154585cf4993a0e97a3a07e6e43e/run.json`
- 输出 SHA256：`4d313f3f274a151ae855744c56cfd749be17fc287125bb8bc6064b1a44b03565`

### P06 — pass（R0：pass）

- 结论：有本期资格。；理由与负例：有效家庭季卡即满足，0分不排除，普通等级不阻止。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/P06.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-f170b38f84d34a2295fd2d8f2404d73f/run.json`
- 输出 SHA256：`9c129956818f1dcb724af0af46052c98ee86b605e95b0efafc316e3dfc56aa06`

### P07 — pass（R0：pass）

- 未知处理：不能判有/无，金卡不能代替。；缺失信息：需要账户卡类型/起止/提前终止及业务范围、判定日；不给卡不等于无卡。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/P07.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-bcd4e7f99c80408ba8c35c3d4aaaefc4/run.json`
- 输出 SHA256：`069ee7dffa14f95e438930b83635acc0295ea918e9ff811147e3a20c95ff0657`

### P08 — pass（R0：pass）

- 范围：只本期，不直接套历史/合作方。；下一步：按报表核用途、期间、产品、判定日、覆盖、规则来源，合作方独立确认。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/P08.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-60020d845f8d4a0c96ef1d71ef798eae/run.json`
- 输出 SHA256：`943e253c9f102dd5529b5c03b607c88fbb86131840d77d2e2e892ce891edb5aa`

### P09 — pass（R0：needs_revision）

- 两项主结论：不确定全系统免费，不能证明绝对互斥。；理由：本期资格与系统类别两种规则；互斥/重叠未有记录核验。；R0条件漂移复查：保持“A仅持有有效异业联名卡”，未再把其他卡作为当前未决条件。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/P09.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-10cbf5ec3d244b69b80933d00d2cb094/run.json`
- 输出 SHA256：`4aa84a34a3678b161f7c70100644f8bc6d27443c0881a4d4740636a3f4d3b447`
- 首轮问题本轮未再出现：R0-P09-01

### C01 — pass（R0：needs_revision）

- 数与身份：1有资格账户、2笔订单，O1/O2各一次。；关联：卡资格收敛到账户层，再按订单识别计数，避免卡×订单组合。；R0证据降级复查：本期模型及原消息作为规则依据，未把规则整组归为待确认学员选择。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/C01.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-73717a8a0381442dbcde314b7146cd49/run.json`
- 输出 SHA256：`249bd910434a379d90f2f8fee09f7c360ea9265cb1769274795f54cf67fe6371`
- 首轮问题本轮未再出现：R0-C01-01

非阻塞观察：“账户按人去重”建议改为“按CRM账户标识去重”。本答同时明确1个账户、资格收敛到账户层及订单标识粒度，没有提出跨系统自然人合并，故按完整语义本轮通过，而非按单个词判错。此题只有一个账户，不能据本结果宣称已测试跨账户自然人映射。

### C02 — pass（R0：pass）

- 存在条件：有效家庭季卡即可，失效悦享/联名不否定。；题设：接受本题完整卡记录和有效状态。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/C02.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-d5f3eeba06d64f9fa1e7b586a0ec7432/run.json`
- 输出 SHA256：`41139771c78f294ee0fb16d048db37814c1b428355da6de7aa34e8e7748f45d5`

### C03 — pass（R0：needs_revision）

- 同卡条件：不能跨卡拼接；两卡各不满足完整条件。；R0完整性漂移复查：直接写“在题设条件下结论是不具备本期付费资格”，不再索取生产完整性才能判。；R0角色引用复查：仅准确列消息ID，未将小林消息归陈姐。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/C03.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-6008532005c44d31a2837c51e8a82c7a/run.json`
- 输出 SHA256：`e2ad3454b7f4ed11ab121b15f1c2b86f676b2a66976f6f934a9788242c9593eb`
- 首轮问题本轮未再出现：R0-C03-01, R0-C03-02

### C04 — pass（R0：needs_revision）

- 完整无卡：明确无本期资格。；未提供：缺信息则未知，不当成无卡。；R0作者归属复查：引用字典/模型/消息，没有补造导师/审查建议身份。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/C04.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-0ebf562a1daf4d8e97f6547c8c2114b0/run.json`
- 输出 SHA256：`26a925bafbaa9a029d87765091f978f2527499b465cc9e587d7c2c731a2ddcf2`
- 首轮问题本轮未再出现：R0-C04-01

### C05 — pass（R0：needs_revision）

- 资格：8月月末有本期资格，未购不取消。；购买：完整订单记录无有效购买，paid净额>0解释一致。；活跃：无法判活跃或不活跃，需定义。；R0来源分层复查：资格归具体模型/消息，有效购买归订单/财务材料，活跃未知归模型和01719/01754，没有说成学员选定状态。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/C05.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-8807c81e5bd945cfa66c1bd748aa0209/run.json`
- 输出 SHA256：`4117623ec9882f3bc17e6c269dee4c661c5ee217c70d4b32891d5bc26950f8bd`
- 首轮问题本轮未再出现：R0-C05-01

### C06 — pass（R0：pass）

- 混合产品多卡：1账户、2有效订单，悦享+家庭不累加人次/订单。；关联：卡侧按同卡条件和账户去重，订单侧order_id，按账户联系，禁止卡数复制订单。；边界：本题人工推导不是客户查询，无订单实际卡关系。
- 实际输出：`artifacts/w03/qualification-qa-20261106-r1/output/C06.json`
- 原生记录：`artifacts/w02/knowledge_runs/RUN-9aee6d3599ae4fbcaa444f629a5a7303/run.json`
- 输出 SHA256：`fa7e0864553c3d8b023e2389721c54dbe1dd125899303b8d3f97e046d328c972`

## 保留边界

- 同一已见17题测试集的一次有界回归，不证明未见题泛化，不证明长期稳定性。
- 两轮共34次成功调用都保留；不覆盖R0失败，不用R1回改R0。
- 正式v0.4、现用prompt、Skill及配置未替换，未apply。
- 未做日期专题、其余模型题、38项指标SQL/数值独立对账、客户验收或课程提交。
- 当前这17题没有需用户做真实业务裁决的冲突；正式规则文件、生产历史凭据和活跃定义等原未知继续保留。
