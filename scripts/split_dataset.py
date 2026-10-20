import json
import os
import random
from pathlib import Path

def split_dataset(input_file, train_out, eval_out, seed=42):
    # 固定随机种子，保证每次切分结果绝对一致且可复现
    random.seed(seed)
    print(f"开始切分数据集，随机种子: {seed}")
    
    records = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                
    # 全局打乱数据
    random.shuffle(records)
    total = len(records)
    
    # 按照 80% / 20% 比例进行绝对的物理隔离切分 (废弃 dev 和 test_candidates)
    train_end = int(total * 0.8)
    
    train_data = records[:train_end]
    eval_data = records[train_end:]
    
    def save_jsonl(data, path):
        os.makedirs(Path(path).parent, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
                
    # 分别保存到独立的目录
    save_jsonl(train_data, train_out)
    save_jsonl(eval_data, eval_out)
    
    print(f"切分彻底完成！总计: {total} 条")
    print(f"- 训练集 (Train): {len(train_data)} 条 -> {train_out}")
    print(f"- 冻结评测集 (Eval): {len(eval_data)} 条 -> {eval_out}")

if __name__ == "__main__":
    # 输入为清洗后的 500 条数据
    INPUT = "data/processed/cleaned_tickets.jsonl"
    
    # 输出 1：80% 作为训练集
    TRAIN = "data/processed/train.jsonl"
    # 输出 2：20% 放入独立的 eval 目录彻底冻结
    EVAL = "data/eval/eval_set_v1.jsonl"
    
    split_dataset(INPUT, TRAIN, EVAL)