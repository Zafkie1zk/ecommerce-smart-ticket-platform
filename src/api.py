from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.schemas import TicketInput, TicketOutput
import uuid

app = FastAPI(title="智能工单处理平台API")


def simple_rule_baseline(ticket: TicketInput) -> TicketOutput:
    msg = ticket.user_message
    if "退款" in msg or "换" in msg or "坏" in msg or "歪" in msg:
        return TicketOutput(
            category="退货换货" if "换" in msg else "商品质量",
            priority="P1",
            entities={"issue": "商品瑕疵或要求退换"},
            requires_human=True,
            suggested_reply="非常抱歉给您带来不便，我们需要人工核实您的订单和照片。",
            escalation_reason="涉及退换货或商品质量"
        )
    else:
        return TicketOutput(
            category="商品咨询",
            priority="P2",
            entities={},
            requires_human=False,
            suggested_reply="您好，感谢咨询，此款商品正常使用即可，具体可参考说明书。"
        )

@app.post("/analyze-ticket", response_model=TicketOutput)
async def analyze_ticket(ticket: TicketInput):
    try:
        # 在这里调用你的模型或规则基线
        result = simple_rule_baseline(ticket)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "电商智能客服工单系统已启动"}
