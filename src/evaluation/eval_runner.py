import json
import os
import sys
from pathlib import Path

# 确保能正确导入 src 目录下的模块
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.schemas import TicketInput
# 注意这里：导入路径已经更新为刚才抽离的独立基线文件
from src.baselines.rule_baseline import simple_rule_baseline
from src.evaluation.metrics import calculate_metrics

def run_baseline_evaluation(eval_file, result_file, metrics_file):
    print(f"开始运行基线评测，读取数据集: {eval_file}")
    
    true_records = []
    pred_records = []
    
    with open(eval_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            true_records.append(record)
            
            # 提取输入构造 TicketInput
            inp_data = record["input_data"]
            ticket = TicketInput(**inp_data)
            
            # 运行规则基线
            try:
                pred_output = simple_rule_baseline(ticket)
                # 构造预测记录
                pred_record = {
                    "input_data": inp_data,
                    "output_data": pred_output.model_dump()
                }
            except Exception as e:
                print(f"预测失败 {ticket.ticket_id}: {e}")
                pred_record = {"input_data": inp_data, "output_data": {}, "error": str(e)}
                
            pred_records.append(pred_record)

    # 计算指标
    metrics = calculate_metrics(true_records, pred_records)
    
    # 写入结果和指标
    os.makedirs(Path(result_file).parent, exist_ok=True)
    
    with open(result_file, 'w', encoding='utf-8') as f:
        for p in pred_records:
            f.write(json.dumps(p, ensure_ascii=False) + '\n')
            
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=4)
        
    print("\n评测完成！")
    print(f"分类准确率: {metrics.get('category_accuracy', 0):.2%}")
    print(f"转人工召回率: {metrics.get('requires_human_recall', 0):.2%}")
    print(f"详细预测结果保存至: {result_file}")
    print(f"指标统计保存至: {metrics_file}")

if __name__ == "__main__":
    
    EVAL_DATA = "data/eval/eval_set_v1.jsonl"
    PRED_OUT = "reports/baseline/results.jsonl"
    METRICS_OUT = "reports/baseline/metrics.json"
    
    run_baseline_evaluation(EVAL_DATA, PRED_OUT, METRICS_OUT)
