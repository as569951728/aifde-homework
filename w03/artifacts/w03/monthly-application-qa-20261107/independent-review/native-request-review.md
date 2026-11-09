# R组原生请求隔离核验

7题、7次HTTP，各一次成功；70项逐题核验通过，冻结输入与正式保护hash通过。

独立从原题和原始材料重建每题输入，逐份比较原生请求/尝试/settings及答案；仅读check_run，不发模型调用。材料原文保存在question/settings/request中并由批次hash冻结，不称为原生source_manifest新增节点。expected为空，未混入其他题、预期、原始访谈或工具。

运行索引SHA256：`de09a082d98bb3c2b32b75d6d7feb9042e54051adbf90a10fb02e7235a7a8f33`

本组是model_with_fixed_materials，不是model_only，也未运行指标SQL。
