import pytest
from pydantic import ValidationError
from src.schemas import TicketInput, TicketOutput, TicketRecord

def test_valid_ticket_input():
    data = {
        "ticket_id": "T001",
        "user_message": "我买的316奶锅收到有划痕，想退款",
        "product_name": "316不锈钢奶锅",
        "order_status": "delivered"
    }
    ticket = TicketInput(**data)
    assert ticket.ticket_id == "T001"
    assert ticket.source == "unknown"

def test_valid_ticket_output():
    data = {
        "category": "退款售后",
        "priority": "P1",
        "entities": {"product": "316不锈钢奶锅", "issue": "划痕"},
        "requires_human": True,
        "suggested_reply": "很抱歉影响您的体验，请提供照片以便售后核实处理。",
        "escalation_reason": "用户要求退款，需人工核对照片并审批"
    }
    output = TicketOutput(**data)
    assert output.category == "退款售后"
    assert output.requires_human is True

def test_invalid_category_raises_error():
    data = {
        "category": "随便写的错误分类",
        "priority": "P1",
        "requires_human": False,
        "suggested_reply": "测试"
    }
    with pytest.raises(ValidationError):
        TicketOutput(**data)

def test_invalid_priority_raises_error():
    data = {
        "category": "商品咨询",
        "priority": "P999", 
        "requires_human": False,
        "suggested_reply": "测试"
    }
    with pytest.raises(ValidationError):
        TicketOutput(**data)
