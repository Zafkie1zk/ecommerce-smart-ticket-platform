from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import sys
from pathlib import Path

# 确保能正确导入 src.schemas
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.schemas import TicketInput, TicketOutput

app = FastAPI(
    title="电商智能客服工单处理平台 API",
    description="提供工单文本智能解析与处理建议接口",
    version="1.0.0"
)

def simple_rule_baseline(ticket: TicketInput) -> TicketOutput:
    """
    Week 1 的规则基线系统：通过关键词匹配模拟工单分类和风险判定
    后续 Week 3 这里将被替换为调用 vLLM 部署的大模型大语言模型
    """
    msg = ticket.user_message
    
    # 规则 1：高风险投诉与退款
    if any(kw in msg for kw in ["退款", "投诉", "12315", "差评"]):
        return TicketOutput(
            category="退款售后" if "退款" in msg else "其他/边界",
            priority="P0",
            entities={"issue": "用户情绪激动或涉及退款维权"},
            requires_human=True,
            suggested_reply="非常抱歉给您带来不好的体验，您的诉求我已经记录并加急反馈给专员，请稍等。",
            escalation_reason="涉及退款或情绪激动，必须人工审核"
        )
    # 规则 2：质量与换货
    elif any(kw in msg for kw in ["坏", "歪", "划痕", "换", "漏水"]):
        return TicketOutput(
            category="商品质量",
            priority="P1",
            entities={"issue": "商品瑕疵"},
            requires_human=True,
            suggested_reply="非常抱歉，产品问题我们绝不推诿。麻烦您提供一下异常部位的照片。",
            escalation_reason="质量问题需要人工核实图片证据"
        )
    # 规则 3：常规咨询
    else:
        return TicketOutput(
            category="商品咨询",
            priority="P2",
            entities={},
            requires_human=False,
            suggested_reply="您好，感谢您的咨询，相关功能您可以参考产品说明书哦。",
            escalation_reason=None
        )

@app.post("/analyze-ticket", response_model=TicketOutput, summary="单条工单分析接口")
async def analyze_ticket(ticket: TicketInput):
    """
    接收单条工单文本，返回结构化的意图、风险评级和回复建议
    """
    try:
        result = simple_rule_baseline(ticket)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", summary="健康检查接口")
def read_root():
    return {"message": "电商智能客服工单系统API已成功启动运行！"}
