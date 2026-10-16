# 企业级电商客服工单智能处理平台

本项目基于大模型实现电商售后客服工单的智能辅助处理。重点通过大语言模型进行工单结构化意图识别与处理建议生成，并提供合规的转人工审核干预。

## 目录结构说明

- `configs/`：模型与训练参数配置
- `data/`：包含 raw（原始数据）, processed（清洗后格式化数据）, eval（评测集）
- `docs/`：系统架构图与业务分类标签体系文档
- `scripts/`：数据合成、清洗、导入与转换脚本
- `src/`：核心业务逻辑（schemas 结构、baseline 规则、FastAPI 服务）
- `tests/`：Pytest 单元测试
- `reports/`：评测指标结果与数据质量分析报告

## 环境配置

1. **创建并激活虚拟环境**：
   
   ```bash
   python -m venv venv
   
   # Windows 用户激活环境：
   .\venv\Scripts\Activate.ps1
   
   # Mac/Linux 用户激活环境：
   source venv/bin/activate

2. **安装相关依赖**：

```bash
pip install -r requirements.txt
```

## 核心接口说明

`POST /analyze-ticket`：单条工单分析接口，接收原始对话，返回意图分类、风险评级(P0/P1/P2)及建议回复。