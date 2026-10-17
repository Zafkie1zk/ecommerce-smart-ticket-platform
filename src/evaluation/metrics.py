def calculate_metrics(true_records, pred_records):
    """
    计算分类准确率和人工升级的 Precision/Recall/F1
    """
    total = len(true_records)
    if total == 0:
        return {}

    correct_category = 0
    true_human_positive = 0
    pred_human_positive = 0
    true_pred_human_positive = 0

    for true_rec, pred_rec in zip(true_records, pred_records):
        true_out = true_rec.get("output_data", {})
        pred_out = pred_rec.get("output_data", {})

        # 1. 意图分类 Accuracy
        if true_out.get("category") == pred_out.get("category"):
            correct_category += 1
            
        # 2. 转人工 (requires_human) 指标统计
        t_human = true_out.get("requires_human", False)
        p_human = pred_out.get("requires_human", False)
        
        if t_human: true_human_positive += 1
        if p_human: pred_human_positive += 1
        if t_human and p_human: true_pred_human_positive += 1

    # 计算指标
    accuracy = correct_category / total
    recall = true_pred_human_positive / true_human_positive if true_human_positive > 0 else 0
    precision = true_pred_human_positive / pred_human_positive if pred_human_positive > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "total_samples": total,
        "category_accuracy": round(accuracy, 4),
        "requires_human_recall": round(recall, 4),
        "requires_human_precision": round(precision, 4),
        "requires_human_f1": round(f1, 4)
    }