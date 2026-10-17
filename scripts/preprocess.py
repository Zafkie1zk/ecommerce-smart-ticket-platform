import json
import os
from pathlib import Path

def preprocess_data(input_file, output_file, report_file):
    print(f"开始清洗数据: {input_file}")
    
    raw_records = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                raw_records.append(json.loads(line))
                
    initial_count = len(raw_records)
    cleaned_records = []
    seen_messages = set()
    
    # 统计过滤原因
    stats = {
        "empty_or_too_short": 0,
        "duplicates": 0,
        "invalid_category": 0
    }
    
    valid_categories = {"商品咨询", "物流异常", "商品质量", "退货换货", "退款售后", "其他/边界"}

    for r in raw_records:
        inp = r.get("input_data", {})
        out = r.get("output_data", {})
        msg = inp.get("user_message", "").strip()
        cat = out.get("category", "")
        
        # 1. 过滤空文本或过短文本 (< 5个字符)
        if len(msg) < 5:
            stats["empty_or_too_short"] += 1
            continue
            
        # 2. 精确去重 (基于用户消息内容)
        if msg in seen_messages:
            stats["duplicates"] += 1
            continue
        seen_messages.add(msg)
        
        # 3. 过滤非法枚举类别
        if cat not in valid_categories:
            stats["invalid_category"] += 1
            continue
            
        cleaned_records.append(r)

    final_count = len(cleaned_records)
    
    # 写入清洗后的数据
    os.makedirs(Path(output_file).parent, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for r in cleaned_records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
            
    # 生成清洗报告
    report_content = f"""# 数据清洗报告 (Cleaning Report)

- **原始数据量**: {initial_count} 条
- **清洗后数据量**: {final_count} 条

## 过滤明细
- **文本过短/为空**: {stats['empty_or_too_short']} 条
- **重复数据**: {stats['duplicates']} 条
- **非法类别**: {stats['invalid_category']} 条

**结论**: 清洗管道运行正常，去重与格式校验已完成。
"""
    os.makedirs(Path(report_file).parent, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
        
    print(f"清洗完成！有效数据: {final_count} 条。报告已保存至 {report_file}")

if __name__ == "__main__":
    INPUT = "data/processed/eval_set_v1.jsonl"
    OUTPUT = "data/processed/cleaned_tickets.jsonl"
    REPORT = "reports/cleaning_report.md"
    preprocess_data(INPUT, OUTPUT, REPORT)