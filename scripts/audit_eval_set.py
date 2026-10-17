import json
import hashlib
import os
from collections import Counter
from pathlib import Path

def audit_evaluation_set(eval_file, audit_report_file):
    print(f"开始审计评测集: {eval_file}")
    
    with open(eval_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        
    total_samples = len(lines)
    
    # 1. 计算 SHA256 进行版本冻结
    file_hash = hashlib.sha256("\n".join(lines).encode('utf-8')).hexdigest()
    
    categories = []
    priorities = []
    human_required_count = 0
    anomalies = []
    seen_ids = set()
    
    for i, line in enumerate(lines):
        try:
            record = json.loads(line)
            inp = record.get("input_data", {})
            out = record.get("output_data", {})
            
            # 查重
            t_id = inp.get("ticket_id")
            if t_id in seen_ids:
                anomalies.append(f"行 {i+1}: 发现重复的 ticket_id {t_id}")
            seen_ids.add(t_id)
            
            # 类别与枚举收集
            cat = out.get("category", "MISSING")
            categories.append(cat)
            priorities.append(out.get("priority", "MISSING"))
            if out.get("requires_human") is True:
                human_required_count += 1
                
            # 空值检测
            if not inp.get("user_message"):
                anomalies.append(f"行 {i+1}: user_message 为空")
                
        except json.JSONDecodeError:
            anomalies.append(f"行 {i+1}: JSON 格式非法")
            
    cat_counts = Counter(categories)
    
    # 2. 生成审计报告
    report_content = f"""# 评测集审计报告 (Evaluation Set Audit)

## 1. 基础信息冻结
- **文件路径**: `{eval_file}`
- **有效样本数**: {total_samples} 条
- **文件 SHA256 哈希**: `{file_hash}` (用于防篡改和泄漏追踪)

## 2. 类别配额核对
- **退款售后**: {cat_counts.get('退款售后', 0)} / 目标 120
- **商品咨询**: {cat_counts.get('商品咨询', 0)} / 目标 100
- **退货换货**: {cat_counts.get('退货换货', 0)} / 目标 90
- **物流异常**: {cat_counts.get('物流异常', 0)} / 目标 80
- **商品质量**: {cat_counts.get('商品质量', 0)} / 目标 70
- **其他/边界**: {cat_counts.get('其他/边界', 0)} / 目标 40

## 3. 风险分布
- **需人工介入比例**: {human_required_count} / {total_samples} ({(human_required_count/total_samples)*100:.2f}%)
- **风险等级分布**: {dict(Counter(priorities))}

## 4. 异常诊断
- **发现异常数**: {len(anomalies)}
"""
    if anomalies:
        report_content += "\n".join([f"- {a}" for a in anomalies[:10]])
        if len(anomalies) > 10: report_content += "\n- ...(更多异常已省略)"
    else:
        report_content += "\n- 无格式异常、无缺失值、无重复 ID，数据完全健康。"
        
    os.makedirs(Path(audit_report_file).parent, exist_ok=True)
    with open(audit_report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
        
    print(f"审计完成！共处理 {total_samples} 条数据。")
    print(f"评测集 SHA256 冻结指纹: {file_hash}")
    print(f"审计报告已保存至: {audit_report_file}")

if __name__ == "__main__":
    EVAL_FILE = "data/eval/eval_set_v1.jsonl"
    REPORT_FILE = "reports/eval_audit.md"
    audit_evaluation_set(EVAL_FILE, REPORT_FILE)