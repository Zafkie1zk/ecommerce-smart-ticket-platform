# 智能客服工单处理平台 - 业务架构图

本项目基于数据流驱动，涵盖数据工程、模型微调、在线评测与服务化四个主要阶段：

```text
[1. 工单数据工程]
原始脱敏对话 / 合成工单集
       │
       ▼ (清洗、拆分、规范化 Schema)
   Train / Dev / Test (500+评测集)
       │
       ├────────────────────────────────────────┐
       ▼                                        ▼
[2. 模型微调 (LoRA)]                      [3. 自动评测 (Base/SFT 对比)]
指令微调数据集构造                          固定测试集哈希防泄漏
       │                                        │
    PEFT/LoRA 训练                              ▼ (输出指标)
(Rank/Alpha/LR 等实验)                  分类 F1 / JSON 格式合法率
       │                               人工升级 Recall / 鲁棒性漏检
       ▼
[4. 服务化部署 (vLLM)]
   加载 SFT 权重
       │
OpenAI-compatible API
(/analyze-ticket & /batch)
       │
       ▼
[5. 性能与量化实验 (INT8)]
对比 Base/INT8 的推理延迟 (P50/P95)
吞吐量 (Throughput) 与显存开销对比