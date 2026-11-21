# W04 c3 前序 checkpoint：供 W05 接续

> 版本 `fde-checkpoint-w04-c3-for-w05-20261008.1`，随 W05 材料包提供。这是一份可单独采用的 W04 结束状态；优先使用自己版本匹配的 W04 成果。

本包使用原独立 W04 试做者的适配器和指标库，在公开 c3 数据上重新清洗、导入并验证；完整业务模型、修订记录及部分依据由课程方后补。采用者必须说明采用范围，不能将前序代码、课程补充或原访谈登记为本人完成。原试做的交付缺项没有因制作本包而追认通过。

## 1. 包内内容

| 路径 | 内容与用途 |
| --- | --- |
| `customer/w04/` | 原适配器与 8 项测试，源码保持 |
| `artifacts/w04/cleaning_rules.yaml`、`confirmed_tags.txt` | c3 运行规则及原标签表；计算参数保持，更名依据已确认 |
| `artifacts/w04/library/` | 38 项前序指标库；SQL、ID、公式和维度定义保持；新增显式默认维度文件 |
| `artifacts/w04/cleaned/` | 本次实际生成的 7 份 CSV 与 manifest，数据 ID 为 `qinghe-w04-v1.1` |
| `docs/w04/` | 完整业务模型、修订记录、指标接续说明及有来源标记的旧访谈摘要 |
| `materials/w03/`、`materials/w04/` | 支撑上述定义的公开业务材料，以及课程方补充的 W04 事实 |
| `originals/w03-reference/business_model.md` | 保留的旧阶段模型；其后续修订以 `docs/w04/business_model.md` 为准 |
| `examples/w04/public-check/` | 原 W04 c2 工程随附的公开检查样本，供前序适配器测试 |
| `MANIFEST.json` | 本 checkpoint 的文件、版本及 SHA-256 清单 |

复现清洗需要的 W04 c3 源数据 `qinghe-w04-v1.1.zip` 不在本目录，它与 W04 材料包 `数据/qinghe-w04-v1.1.zip` 是同一个文件（SHA-256 `447eeb9b699c79edcb9d640049487895f7c964f2ab391aacae5452fe0cffb552`），需要时从 W04 材料包取用，放到工程的 `data/` 下。

先读[来源与采用说明](来源与采用说明.md)及[验证摘要](验证摘要.md)。本包不包含 W05 客户函数、统一会员映射、候选名单或未来周答案，也不包含模型配置与访谈登录信息。

## 2. 接到 W05 工程

1. 将 W05 材料包中的现行工程（`w05-linkml-candidate-20261014.2`）解压到新的工作目录，按其说明配置 Python 3.11 和依赖。保留自己的原 W04 提交。
2. 将本包的 `customer/w04/`、`artifacts/w04/`、`docs/w04/`、`materials/w03/`、`materials/w04/`、`originals/w03-reference/`、`examples/w04/public-check/` 复制到新工程的同名路径；需要复现清洗时，另从 W04 材料包把 `qinghe-w04-v1.1.zip` 复制到 `data/`。只在新工作副本采用这些文件；不要覆盖已有个人实现或整目录覆盖 `customer/`、`docs/`。本包根目录的 README 和 MANIFEST 留在 checkpoint 内，不覆盖工程自己的文件。
3. W05 `prepare` 请求中的 `w04_cleaned` 指向 `artifacts/w04/cleaned/`，`library` 指向 `artifacts/w04/library/`；`raw` 仍指向另外提供的 W05 v2 数据目录，`code` 指向自己将要实现的 `customer/w05/solution.py`。运行命令时使用相对当前工作目录的路径或实际绝对路径。
4. 在已有业务模型修订记录／作业报告中写明本 checkpoint 版本及采用的文件，然后根据 W05 新材料开发和验证。本包不增加一份必交报告。

W05 工程中的 YAML 模型和客户函数仍是 TODO。空白工程运行 `prepare` 时，W04 前序检查通过后先报 `MODEL_TODO_FILL_CUSTOMER_SOURCE`，表示 YAML 模型还没填；填完 YAML 后再报 `CUSTOMER_IDENTITY_RULES_REQUIRED`，表示 ID-Mapping 还没实现。这两个都不是让你忽略的错误，也不是本周作业完成的证据。先完成 YAML 和三个客户函数，再按 W05 任务书继续。

## 3. 复查前序能力

完成上述受控复制后，在新工程根目录执行；下列输出路径必须尚不存在。

```bash
python customer/w04/test_solution.py
python tools/w04.py load --data artifacts/w04/cleaned --library artifacts/w04/library --project artifacts/w04/checkpoint-project
```

需要从原始 c3 数据复现时（先从 W04 材料包取得数据 ZIP，放到 `data/`）：

```bash
python -m zipfile -e data/qinghe-w04-v1.1.zip data/w04-c3
python tools/w04.py adapt --source data/w04-c3/qinghe-w04-v1.1 --rules artifacts/w04/cleaning_rules.yaml --code customer/w04/solution.py --output artifacts/w04/rebuilt-c3 --library artifacts/w04/library --project artifacts/w04/rebuilt-project
```

清洗结果的 `manifest.json` 记录数据 ID、6 份源文件指纹和 7 份清洗文件指纹。重建应由原始文件及规则实际生成，不能只改旧 manifest 的 ID 或哈希。小林工作账在 W04 仅作对照，c3 的分组与参考日期修订不改变经营基础表。

本包已经完成前序技术核对：2026-10-08 在 W05 `.10` 工程上完成，2026-10-19 在现行 `20261014.2` 工程上复查原适配器 8 项测试和指标库导入，均通过且导入数量一致。2026-11-05 在现行 `-r6` 封包上复查：8 项测试、导入、从原始数据重建清洗结果（与本包逐字节相同）和 `prepare` 的 W04 前序检查均通过。2026-11-18 在现行 `-r7` 封包上按同样四项复查，均通过。后续修改需要由采用者验证。本包没有完成 W05 全链路、真实模型、业务访谈或独立学员试做。
