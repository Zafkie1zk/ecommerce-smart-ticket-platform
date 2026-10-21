import json
import random
import os
from pathlib import Path

# 1. 为每个产品配置一些混杂的自动回复配置
PRODUCT_MATERIALS = {
    "电热水壶": "食品级304不锈钢材质，耐腐蚀易清洗。",
    "电饭煲": "复合黑晶防粘涂层内胆，安全不粘锅。",
    "电磁炉": "耐高温防刮微晶玻璃面板。",
    "微波炉": "内部采用纳米涂层，防油污易擦洗。",
    "空气炸锅": "食品级特氟龙不粘涂层炸篮。",
    "电烤箱": "加厚镀锌板内胆与防爆钢化玻璃门。",
    "破壁机": "加厚高硼硅玻璃杯体，食品级精钢刀头。",
    "榨汁机": "婴儿食品级Tritan材质（不含BPA）。",
    "咖啡机": "外壳为ABS阻燃材质，内部核心部件为不锈钢。",
    "电煮锅": "陶瓷釉不粘内胆，健康无异味。",
    "电吹风": "耐高温PC磨砂阻燃材质。",
    "电动牙刷": "医用级杜邦软毛刷头与全身防水硅胶机身。",
    "剃须刀": "机身为防滑橡胶，刀网为自研精钢材质。",
    "卷发棒": "表面覆盖植物蛋白陶瓷涂层，不伤发。",
    "加湿器": "高品质ABS+PP抑菌材质水箱。",
    "电风扇": "高韧性AS材质扇叶与加厚合金网罩。",
    "取暖器": "V0级阻燃防火外壳材料，内置PTC陶瓷发热体。",
    "吸尘器": "航空级高强度ABS工程塑料外壳。",
    "挂烫机": "加厚铝合金伸缩杆与特氟龙烫头面板。",
    "按摩仪": "亲肤透气PU皮与记忆海绵内芯。"
}

# 询问材质的常见提问句式库
QUESTION_TEMPLATES = [
    "这个{product}链接是什么材质的？",
    "你好，这款{product}什么材料做的？",
    "{product}是啥材质的呀，安全吗？",
    "我想问下这个{product}的内胆/外壳是什么材质？",
    "你家这个{product}质量咋样，用的什么材质？",
    "这个{product}材质耐用吗？是什么做的？",
    "请问{product}具体材质是什么？",
    "链接里的{product}材质能说明一下吗？",
    "{product}的材质是食品级的吗，具体叫什么？",
    "麻烦告诉我一下这个{product}的主要材质是什么。"
]

INSTRUCTION = "你是电商客服坐席辅助系统。请根据客户对话，输出工单分类、风险等级、实体、是否需要人工审核、建议回复和升级理由。只输出 JSON。涉及退款审批时必须转人工，不得承诺未经核实的退款结果。"

def create_material_rules():
    """生成 200 条材质问答规则的 SFT 训练对"""
    rule_samples = []
    
    for product, material in PRODUCT_MATERIALS.items():
        # 每个产品生成 10 条
        for template in QUESTION_TEMPLATES:
            question = template.format(product=product)
            
            output_json = {
                "category": "商品咨询",
                "priority": "P2",
                "entities": {
                    "product": product,
                    "issue": "材质咨询",
                    "request": "查询材质"
                },
                "requires_human": False,
                "suggested_reply": f"您好！这款{product}使用的是{material}。您可以放心购买使用哦！",
                "escalation_reason": None
            }
            
            sample = {
                "instruction": INSTRUCTION,
                "input": f"客户：{question}",
                "output": output_json
            }
            rule_samples.append(sample)
            
    return rule_samples

def mix_and_save_dataset():
    # 1. 生成 200 条材质问答新数据
    new_rules = create_material_rules()
    random.seed(42)
    random.shuffle(new_rules)
    
    # 按照 80/20 切分这批新数据 (160 条进训练集，40 条进评测集)
    train_rules = new_rules[:160]
    eval_rules = new_rules[160:]
    
    # 2. 读取原有的数据集
    train_path = "data/processed/train.jsonl"
    eval_path = "data/eval/eval_set_v1.jsonl"
    
    train_existing = []
    eval_existing = []
    
    if os.path.exists(train_path):
        with open(train_path, 'r', encoding='utf-8') as f:
            train_existing = [json.loads(line) for line in f if line.strip()]
            
    if os.path.exists(eval_path):
        with open(eval_path, 'r', encoding='utf-8') as f:
            eval_existing = [json.loads(line) for line in f if line.strip()]
            
    # 3. 混合并打乱 (掺沙子)
    final_train = train_existing + train_rules
    final_eval = eval_existing + eval_rules
    
    random.shuffle(final_train)
    random.shuffle(final_eval)
    
    # 4. 写回文件
    def save_jsonl(data, path):
        with open(path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                
    save_jsonl(final_train, train_path)
    save_jsonl(final_eval, eval_path)
    

    print(f"- 训练集 (Train) 现有数据量: {len(final_train)} 条 (新增 {len(train_rules)} 条材质问答)")
    print(f"- 冻结评测集 (Eval) 现有数据量: {len(final_eval)} 条 (新增 {len(eval_rules)} 条材质问答)")

if __name__ == "__main__":
    mix_and_save_dataset()