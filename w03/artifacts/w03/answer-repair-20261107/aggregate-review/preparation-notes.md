# 收尾核验准备记录

- 新增 stage5-compact-evidence 22题支持；其结果必须待真实执行与独立语义评审，不预记通过。
- 四个取消批均按原生 settings 与 batch output 检查零调用，含 stage4-network-recovery。
- stage3 的 E01 语义失败、stage4 的 U05/TRACECTRL01 语义失败及 E01 网络无答已保存在 stage3-stage4-preservation.json；不回改旧分。
- 六份 before-continuity 备份哈希与 manifest 一致，准备检查时六份现文件亦仍等于 before 哈希。
- pre-stage5-check.json 的 KeyError 是本审计器误假设每条合并评审都含 http_attempts：数学/格式四行没有该字段。未更动受审文件；改为从每条原生 attempts 独立计数，同时比对存在的每题计数及评审总数。原误报保留，修订检查 pre-stage5-check-r2.json 通过。
- 此处机械通过仅证明计数和留档完整性；最终 completion/ledger/报告及六接续变更内容仍待审。
