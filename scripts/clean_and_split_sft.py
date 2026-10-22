import json
import os
from pathlib import Path

def clean_and_isolate_dataset():
    print("开始执行数据去重与防泄漏隔离清洗...")
    
    eval_path = "data/eval/eval_set_v1.jsonl"
    train_path = "data/processed/train.jsonl"
    cleaned_train_path = "data/processed/sft_dataset_v1.jsonl" # 明确唯一的正式训练文件
    
    # 1. 加载冻结评测集的输入集合（用于比对查重）
    eval_inputs = set()
    if os.path.exists(eval_path):
        with open(eval_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    # 提取 input 的核心文本用于去重
                    eval_inputs.add(item.get("input", "").strip())
        print(f"成功加载冻结评测集 (Eval): {len(eval_inputs)} 条。")
    else:
        print("警告：未找到评测集文件！")

    # 2. 读取原始训练数据
    raw_train_records = []
    if os.path.exists(train_path):
        with open(train_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    raw_train_records.append(json.loads(line))
    print(f"读取到原始训练候选数据: {len(raw_train_records)} 条。")

    # 3. 查重过滤与输出格式统一
    final_train_records = []
    overlap_count = 0
    
    for record in raw_train_records:
        inp = record.get("input", "").strip()
        
        # 检查是否与评测集重叠
        if inp in eval_inputs:
            overlap_count += 1
            continue
            
        # 统一格式处理
        out = record.get("output", {})
        if isinstance(out, str):
            try:
                out = json.loads(out)
            except Exception:
                pass
        record["output"] = out
        
        # 确保包含标准的 4 个字段
        if "instruction" not in record:
            record["instruction"] = "你是电商客服坐席辅助系统。请根据客户对话，输出工单分类、风险等级、实体、是否需要人工审核、建议回复和升级理由。只输出 JSON。涉及退款审批时必须转人工，不得承诺未经核实的退款结果。"
            
        final_train_records.append(record)

    # 4. 保存唯一的正式训练文件
    os.makedirs(Path(cleaned_train_path).parent, exist_ok=True)
    with open(cleaned_train_path, 'w', encoding='utf-8') as f:
        for r in final_train_records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    print(f"生成唯一的正式训练文件: {cleaned_train_path} (共计 {len(final_train_records)} 条)")

if __name__ == "__main__":
    clean_and_isolate_dataset()