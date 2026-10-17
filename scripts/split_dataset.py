import json
import os
import random
from pathlib import Path

def split_dataset(input_file, train_out, dev_out, test_out, seed=42):
    # 文档要求：固定 seed=42，保证每次切分可复现
    random.seed(seed)
    print(f"开始切分数据集，随机种子: {seed}")
    
    records = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                
    # 打乱数据
    random.shuffle(records)
    total = len(records)
    
    # 按照 70% / 10% / 20% 切分
    train_end = int(total * 0.7)
    dev_end = int(total * 0.8)
    
    train_data = records[:train_end]
    dev_data = records[train_end:dev_end]
    test_data = records[dev_end:]
    
    def save_jsonl(data, path):
        os.makedirs(Path(path).parent, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
                
    save_jsonl(train_data, train_out)
    save_jsonl(dev_data, dev_out)
    save_jsonl(test_data, test_out)
    
    print(f"切分完成！总计: {total} 条")
    print(f"- 训练集 (Train): {len(train_data)} 条 -> {train_out}")
    print(f"- 验证集 (Dev):   {len(dev_data)} 条 -> {dev_out}")
    print(f"- 测试集候选 (Test Candidates): {len(test_data)} 条 -> {test_out}")

if __name__ == "__main__":
    INPUT = "data/processed/cleaned_tickets.jsonl"
    TRAIN = "data/processed/train.jsonl"
    DEV = "data/processed/dev.jsonl"
    TEST = "data/processed/test_candidates.jsonl"
    
    split_dataset(INPUT, TRAIN, DEV, TEST)