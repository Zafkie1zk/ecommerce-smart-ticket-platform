import pandas as pd
import json
import uuid
import re
from pathlib import Path
import sys

# 动态添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.schemas import TicketInput, TicketOutput, TicketRecord

# 1. 实体抽取词库
PRODUCTS = [
    "电热水壶", "电饭煲", "电磁炉", "微波炉", "空气炸锅", "电烤箱", "破壁机", "榨汁机", "咖啡机", 
    "电煮锅", "电吹风", "电动牙刷", "剃须刀", "卷发棒", "加湿器", "电风扇", "取暖器", "吸尘器", 
    "挂烫机", "按摩仪"
]

def extract_dynamic_labels(msg: str, category: str, is_human_required: bool):
    """
    核心引擎：动态提取实体、判定真实风险等级并生成合规的建议回复。
    彻底取代硬编码！
    """
    # --- 1. 动态实体抽取 (Entities) ---
    product_name = "未知商品"
    for p in PRODUCTS:
        if p in msg:
            product_name = p
            break
            
    issue = "常规诉求"
    if "漏电" in msg or "冒烟" in msg or "火花" in msg or "炸" in msg: issue = "安全隐患"
    elif "降价" in msg or "差价" in msg: issue = "保价/退差价"
    elif "券" in msg or "满减" in msg: issue = "优惠活动异常"
    elif "坏" in msg or "不加热" in msg or "噪音" in msg: issue = "商品故障"
    elif "单号" in msg or "发货" in msg or "物流" in msg: issue = "物流查询"
    
    # --- 2. 动态判定风险等级 (Priority) ---
    priority = "P2"
    escalation_reason = None
    
    # P0 判定逻辑
    if any(w in msg for w in ["漏电", "冒烟", "起火", "跳闸", "烫伤", "投诉", "12315", "泄露"]):
        priority = "P0"
        escalation_reason = "触发 P0 高风险安全隐患或严重公关投诉，必须由高级专员紧急介入"
    # P1 判定逻辑
    elif category in ["退货换货", "退款售后", "商品质量"] or any(w in msg for w in ["专票", "差价", "运费"]):
        priority = "P1"
        escalation_reason = "涉及资金退赔、质量故障鉴定或对公业务，需人工核实凭证后处理"
    
    if not is_human_required:
        escalation_reason = None

    # --- 3. 动态生成符合业务规范的建议回复 (Suggested Reply) ---
    suggested_reply = ""
    
    if priority == "P0":
        if "漏电" in msg or "冒烟" in msg or "炸" in msg:
            suggested_reply = f"【安全提醒】请您立即拔掉{product_name}的电源并停止使用！非常抱歉让您受到惊吓，安全最重要。我已为您加急接通高级安全售后专员为您处理退换与补偿。"
        else:
            suggested_reply = "非常抱歉给您带来极其糟糕的体验。您的反馈我们高度重视，我已为您连线高级客诉主管，亲自为您彻查并给出满意的交代。"
            
    elif priority == "P1":
        if category == "退款售后":
            suggested_reply = "您好，了解您的退款或差价诉求。由于涉及具体金额的核算与审批，我马上为您转接财务售后专员帮您核对订单明细并办理打款。"
        elif category == "商品质量":
            suggested_reply = f"非常抱歉，{product_name}出现质量问题我们绝不推诿。麻烦您拍摄一张异常部位的照片，已为您转接专员帮您优先办理换新或退货。"
        else:
            suggested_reply = "您好，您反馈的情况已记录。已为您转接人工客服帮您查验订单状态并提供专属售后通道。"
            
    else: # P2
        if category == "物流异常":
            suggested_reply = "您好，系统已为您查询最新物流轨迹。包裹正在正常流转中，请您耐心等待。如遇停滞，我们会协助催促快递网点。"
        else:
            suggested_reply = f"您好，感谢您的咨询。关于{product_name}的参数详情或使用说明，您可以直接下拉查看商品详情页的图文介绍哦。"

    return {
        "priority": priority,
        "entities": {
            "product": product_name,
            "issue": issue,
            "request": category
        },
        "suggested_reply": suggested_reply,
        "escalation_reason": escalation_reason
    }

def convert_excel_to_jsonl(input_excel: str, output_jsonl: str):
    print(f"正在加载并动态打标数据集: {input_excel} ...")
    try:
        xls = pd.ExcelFile(input_excel)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_excel}。")
        return

    valid_records = []
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        for index, row in df.iterrows():
            msg_col = "1st message"
            if msg_col not in row or pd.isna(row[msg_col]): continue
            
            user_msg = str(row[msg_col]).strip()
            if not user_msg: continue
            
            # 读取人工介入状态
            status = str(row.get('介入状态', '全程未接入人工'))
            is_human_required = status != '全程未接入人工'
            
            
            dynamic_data = extract_dynamic_labels(user_msg, sheet_name, is_human_required)
            
            try:
                ticket_input = TicketInput(
                    ticket_id=f"T_{uuid.uuid4().hex[:8]}",
                    user_message=f"客户：{user_msg}", 
                    product_name=dynamic_data["entities"]["product"],
                    order_status="delivered",
                    source="sft_auto_labeled"
                )
                
                ticket_output = TicketOutput(
                    category=sheet_name,
                    priority=dynamic_data["priority"],
                    entities=dynamic_data["entities"],
                    requires_human=is_human_required,
                    suggested_reply=dynamic_data["suggested_reply"],
                    escalation_reason=dynamic_data["escalation_reason"]
                )
                
                record = TicketRecord(input_data=ticket_input, output_data=ticket_output)
                
                sft_format = {
                    "instruction": "你是电商客服坐席辅助系统。请根据客户对话，输出工单分类、风险等级、实体、是否需要人工审核、建议回复和升级理由。只输出 JSON。涉及退款审批时必须转人工，不得承诺未经核实的退款结果。",
                    "input": ticket_input.user_message,
                    "output": ticket_output.model_dump()
                }
                
                # 这里我们依然保存为 jsonl 格式
                valid_records.append(json.dumps(sft_format, ensure_ascii=False))
                
            except Exception as e:
                print(f"数据格式校验失败，已跳过: {e}")

    output_path = Path(output_jsonl)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for r in valid_records:
            f.write(r + '\n')
            
    print(f"\n打标完成！成功转换并动态标记了 {len(valid_records)} 条 SFT 训练数据。")

if __name__ == "__main__":
   
    INPUT_FILE = "data/raw/ecommerce_tickets_500_v1.xlsx"
    OUTPUT_FILE = "data/processed/sft_dataset_v1.jsonl"
    convert_excel_to_jsonl(INPUT_FILE, OUTPUT_FILE)