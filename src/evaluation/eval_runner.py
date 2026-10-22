import json
import os
import sys
from pathlib import Path

# 确保能正确导入 src 目录下的模块
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.schemas import TicketInput
# 注意这里：导入路径更新为抽离的独立基线文件
from src.baselines.rule_baseline import simple_rule_baseline
from src.evaluation.metrics import calculate_metrics

def run_baseline_evaluation(eval_file, result_file, metrics_file):
    print(f"开始运行基线评测，读取最新 SFT 格式评测集: {eval_file}")
    
    true_records = []
    pred_records = []
    error_count = 0
    
    with open(eval_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            
            # 【修复问题3】：适配新的 SFT 三段式结构
            # 真实答案保存在 output 字段中 (可能包含 raw_output，优先取 raw_output 确保是字典格式)
            true_output = record.get("raw_output", record.get("output", {}))
            if isinstance(true_output, str):
                try:
                    true_output = json.loads(true_output)
                except Exception:
                    true_output = {}
                    
            # 重构真实的记录以便计算指标
            true_records.append({"output_data": true_output})
            
            # 从 input 字段中提取用户的核心诉求作为基线的输入
            # 格式形如: "客户：刚买的电热水壶漏电..."
            raw_input_text = record.get("input", "")
            clean_user_message = raw_input_text.replace("客户：", "").strip()
            
            # 为了能够传给基线模型，临时将其包装为 TicketInput 对象
            # 注：这里 product_name 等在真实场景下也是未知的，我们重点评测的是 user_message
            ticket = TicketInput(
                ticket_id=f"EVAL_{len(true_records)}",
                user_message=clean_user_message,
                product_name="未知", 
                order_status="unknown",
                source="sft_eval_set"
            )
            
            # 运行规则基线
            try:
                pred_output = simple_rule_baseline(ticket)
                # 构造预测记录
                pred_record = {
                    "input_text": raw_input_text,
                    "true_output": true_output,
                    "output_data": pred_output.model_dump()
                }
            except Exception as e:
                print(f"预测失败 {ticket.ticket_id}: {e}")
                pred_record = {"input_text": raw_input_text, "true_output": true_output, "output_data": {}, "error": str(e)}
                error_count += 1
                
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
        
    print(f"总计处理样本: {len(true_records)} 条，失败 {error_count} 条")
    print(f"分类准确率 (Category Accuracy): {metrics.get('category_accuracy', 0):.2%}")
    print(f"转人工召回率 (Human Recall): {metrics.get('requires_human_recall', 0):.2%}")
    print(f"详细预测明细已保存至: {result_file}")
    print(f"指标统计已保存至: {metrics_file}")

if __name__ == "__main__":
    EVAL_DATA = "data/eval/eval_set_v1.jsonl"
    PRED_OUT = "reports/baseline/results.jsonl"
    METRICS_OUT = "reports/baseline/metrics.json"
    
    run_baseline_evaluation(EVAL_DATA, PRED_OUT, METRICS_OUT)