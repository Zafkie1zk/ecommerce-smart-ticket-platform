import pandas as pd
import json
import uuid
import math
from pathlib import Path
import sys

# 动态添加项目根目录到 Python 路径，解决导包问题
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.schemas import TicketInput, TicketOutput, TicketRecord

def ordinal(n):
    """辅助函数：生成列名序号"""
    if 10 <= n % 100 <= 20: return str(n) + 'th'
    return str(n) + {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')

def convert_excel_to_jsonl(input_excel: str, output_jsonl: str):
    print(f"正在加载 Excel 数据集: {input_excel} ...")
    
    try:
        xls = pd.ExcelFile(input_excel)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_excel}。")
        return

    valid_records = []
    
    # 遍历 Excel 中的 6 个 Sheet
    for sheet_name in xls.sheet_names:
        print(f"正在处理分类: {sheet_name}")
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        for index, row in df.iterrows():
            # 1. 拼接多轮对话
            conversation_history = []
            for i in range(1, 16):
                msg_col = f"{ordinal(i)} message"
                sender_col = f"{ordinal(i)} sender"
                
                # 检查列是否存在且有内容
                if msg_col in row and sender_col in row:
                    msg = row[msg_col]
                    sender = row[sender_col]
                    # 判断非空 (处理 NaN 和空字符串)
                    if pd.notna(msg) and pd.notna(sender) and str(msg).strip() != "":
                        conversation_history.append(f"[{sender}]: {msg}")
            
            # 将对话列表合并为单一的长文本
            full_user_message = "\n".join(conversation_history)
            
            if not full_user_message:
                continue # 跳过空行
                
            # 2. 类别名映射修复 (处理 Excel 命名限制)
            mapped_category = "其他/边界" if sheet_name == "其他边界" else sheet_name
            
            # 3. 介入状态映射
            status = str(row.get('介入状态', '全程未接入人工'))
            is_human_required = status != '全程未接入人工'

            try:
                # 构造符合 Schema 校验的输入
                ticket_input = TicketInput(
                    ticket_id=f"T_{uuid.uuid4().hex[:8]}",
                    user_message=full_user_message,
                    product_name="提取自文本", # 简化处理，暂时占位
                    order_status="unknown",
                    source="synthetic_excel"
                )
                
                # 构造符合 Schema 校验的输出目标 (补全必填占位符，为微调打标做准备)
                ticket_output = TicketOutput(
                    category=mapped_category,
                    priority="P2", # 默认占位，后续可基于规则更新
                    entities={},
                    requires_human=is_human_required,
                    suggested_reply="等待模型生成",
                    escalation_reason=status if is_human_required else None
                )
                
                # 组合成完整的 Record
                record = TicketRecord(input_data=ticket_input, output_data=ticket_output)
                valid_records.append(record.model_dump_json())
                
            except Exception as e:
                print(f"数据格式校验失败，已跳过: {e}")

    # 4. 写入统一的 JSONL 文件
    output_path = Path(output_jsonl)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for r in valid_records:
            f.write(r + '\n')
            
    print(f"\n映射完成！成功转换 {len(valid_records)} 条多轮对话工单。")
    print(f"数据已按照 Pydantic Schema 规范保存至: {output_jsonl}")

if __name__ == "__main__":
    # 配置输入(你刚生成的Excel) 和 输出(标准的JSONL)
    INPUT_FILE = "data/raw/ecommerce_dialogues_coherent_500.xlsx"
    OUTPUT_FILE = "data/processed/eval_set_v1.jsonl"
    
    convert_excel_to_jsonl(INPUT_FILE, OUTPUT_FILE)