from pydantic import BaseModel, Field
from typing import Dict, Literal, Optional

# 定义输入的工单结构
class TicketInput(BaseModel):
    ticket_id: str = Field(..., description="工单的唯一标识符")
    user_message: str = Field(..., description="客户发出的原始咨询或投诉文本")
    product_name: Optional[str] = Field(None, description="涉及的商品名称（如有）")
    order_status: Optional[str] = Field(None, description="当前的订单状态（如有）")
    source: str = Field(default="unknown", description="数据的来源（例如：公开数据集、合成数据）")

# 定义模型预测/标注输出的结构
class TicketOutput(BaseModel):
    category: Literal[
        "商品咨询", "物流异常", "商品质量", "退货换货", "退款售后", "其他/边界"
    ] = Field(..., description="工单的意图分类")
    
    priority: Literal["P0", "P1", "P2"] = Field(
        ..., description="工单处理的风险等级与优先级"
    )
    
    entities: Dict[str, str] = Field(
        default_factory=dict, 
        description="从对话中抽取的结构化实体（如 {'product': '316奶锅', 'issue': '划痕'}）"
    )
    
    requires_human: bool = Field(
        ..., description="是否必须转交人工审核（如退款、补偿、情绪激烈等高风险场景）"
    )
    
    suggested_reply: str = Field(
        ..., description="基于业务规则生成的建议回复草稿"
    )
    
    escalation_reason: Optional[str] = Field(
        None, description="如果需要转交人工，说明具体的升级理由（如：退款请求需要人工核查）"
    )

# 统一的完整工单数据结构（常用于保存到 JSONL）
class TicketRecord(BaseModel):
    input_data: TicketInput
    output_data: Optional[TicketOutput] = None
