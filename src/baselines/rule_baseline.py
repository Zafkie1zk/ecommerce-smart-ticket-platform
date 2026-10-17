from src.schemas import TicketInput, TicketOutput

def simple_rule_baseline(ticket: TicketInput) -> TicketOutput:
    """
    基于关键词匹配的规则基线，用于在 Week 1 建立评测标尺，
    后续将在 Week 2 与 LoRA 微调模型进行对比。
    """
    msg = ticket.user_message
    
    if any(kw in msg for kw in ["退款", "差价", "投诉", "12315", "假货", "曝光"]):
        return TicketOutput(
            category="退款售后" if any(k in msg for k in ["退款", "差价"]) else "其他/边界",
            priority="P0",
            entities={"issue": "高风险售后维权"},
            requires_human=True,
            suggested_reply="非常抱歉给您带来不便，您的诉求已记录并加急转交售后专员处理。",
            escalation_reason="涉及退款或情绪激烈的投诉"
        )
    elif any(kw in msg for kw in ["坏", "歪", "划痕", "漏水", "破", "瑕疵", "变色"]):
        return TicketOutput(
            category="商品质量",
            priority="P1",
            entities={"issue": "商品质量瑕疵"},
            requires_human=True,
            suggested_reply="非常抱歉，产品质量问题我们一定负责到底。请您提供相关异常照片。",
            escalation_reason="质量问题需人工审核图片证据"
        )
    elif any(kw in msg for kw in ["换", "颜色", "退货"]):
        return TicketOutput(
            category="退货换货",
            priority="P1",
            entities={"issue": "退换货申请"},
            requires_human=False,
            suggested_reply="亲，非质量问题的七天无理由退换货，请保证包装完好，直接在订单页面申请即可。"
        )
    elif any(kw in msg for kw in ["发货", "物流", "快递", "签收", "驿站"]):
        return TicketOutput(
            category="物流异常",
            priority="P2",
            entities={"issue": "物流进度咨询"},
            requires_human=False,
            suggested_reply="亲，我们会尽快为您核实物流状态，请您耐心等待。"
        )
    else:
        return TicketOutput(
            category="商品咨询",
            priority="P2",
            entities={},
            requires_human=False,
            suggested_reply="您好，感谢咨询，此款商品正常使用即可，具体参数请参考详情页。"
        )