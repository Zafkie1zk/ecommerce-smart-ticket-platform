import torch
import json
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


base_model_path = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
lora_weights_path = "LLaMA-Factory/saves/ecommerce_ticket_lora"

print("正在加载 Tokenizer 和 基座模型...")
tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_path,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
)

print("正在注入 LoRA 适配器权重...")
model = PeftModel.from_pretrained(base_model, lora_weights_path)
model.eval()

# 2. 构造测试数据
system_prompt = "你是电商客服坐席辅助系统。请根据客户对话，输出工单分类、风险等级、实体、是否需要人工审核、建议回复和升级理由。只输出 JSON。涉及退款审批时必须转人工，不得承诺未经核实的退款结果。"
test_inputs = [
    "刚买的破壁机怎么底座直接裂开了，一通电还滋滋响，赶紧给我退货赔钱！",
    "我那个扫地机器人是凑单用花呗分期买的，现在想退货，分期手续费和用掉的淘金币能退吗？"
]

# 3. 执行推理
print("开始推理测试...\n" + "="*50)
for text in test_inputs:
    full_prompt = f"{system_prompt}\n客户：{text}"
    messages = [{"role": "user", "content": full_prompt}]
    
    # 使用模型的 chat template 拼接标准对话格式
    input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_new_tokens=512, 
            temperature=0.1, 
            top_p=0.9,
            repetition_penalty=1.05
        )
    
    # 截取模型生成的回答部分
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    
    print(f"【用户输入】: {text}")
    print(f"【模型输出】:\n{response}\n" + "="*50)