import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import json_repair

app = FastAPI(title="Ecommerce Ticket AI API")

# 加载合并后的独立模型
MODEL_PATH = "models/ecommerce_ticket_model_v1"
print("正在加载模型与分词器...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
).eval()
print("模型加载完成！")

class TicketRequest(BaseModel):
    text: str

@app.post("/api/v1/ticket/analyze")
async def analyze_ticket(request: TicketRequest):
    try:
        system_prompt = "你是电商客服坐席辅助系统。请根据客户对话，输出工单分类、风险等级、实体、是否需要人工审核、建议回复和升级理由。只输出 JSON。涉及退款审批时必须转人工，不得承诺未经核实的退款结果。"
        full_prompt = f"{system_prompt}\n客户：{request.text}"
        messages = [{"role": "user", "content": full_prompt}]
        
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
        
        raw_response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        
        clean_text = raw_response.split('</think>')[-1].strip()
        parsed_json = json_repair.loads(clean_text)
        
        return {"status": "success", "data": parsed_json}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))