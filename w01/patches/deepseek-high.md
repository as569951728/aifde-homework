# DeepSeek 高强度推理配置

日期：2026-10-22。用户要求使用高强度推理；本改动由助手完成，保留课程发放工程作为来源，不计作学员独立代码修改验收。

实操副本新增 `FDE_MODEL_PROFILE=deepseek-high`，使官方 DeepSeek 直连请求发送顶层 `thinking: {"type": "enabled"}` 和 `reasoning_effort: "high"`。原配置名称和行为保留，输出 token 上限及超时沿用现有设置。

改动文件：

- `platform/fde_product/models.py`：允许新 profile，并选择 high 强度。
- `tests/test_model_policy.py`：在 HTTP 请求体序列化检查中增加 high 场景，核对参数位置和强度。
- `docs/model-configuration.md`：说明本地扩展和启用方式。

依据：[DeepSeek 官方思考模式说明](https://api-docs.deepseek.com/guides/thinking_mode/)。

验证：实际执行 `.venv/bin/python -m pytest tests/test_model_policy.py -q`，13 项通过；另以 `FDE_MODEL_PROFILE=deepseek-high` 启动本地配置检查，确认环境变量能选择新 profile，请求参数为顶层 thinking enabled 和 effort high，无网关 extra_body。以上检查均未调用网络；真实模型、工具闭环及高强度模式表现待实际分析和基线评估。
