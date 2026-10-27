import os
import json
import pandas as pd
from openai import OpenAI



API_KEY = "sk-bd38db160a5545908b282d6bee9d59e2" 
BASE_URL = "https://api.deepseek.com" 
MODEL_NAME = "deepseek-flash"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

PROMPT_TEMPLATE = """
你是一个严谨的电商客服数据标注专家。请根据以下用户诉求，进行细粒度的信息抽取和意图分类。

【明确的标注规范】
1. category (分类): 仅限 退款售后、退货换货、商品质量、物流问题、常规咨询、其他/边界。
2. priority (优先级): P0(安全隐患/重大投诉), P1(资金退赔/质量鉴定), P2(常规业务)。
3. entities (实体): 必须包含 product(商品名称), issue(具体问题), request(用户诉求)。
   -  强规则制约：必须结合上下文理解真实意图！例如“这个锅是什么涂层？”是询问材质（issue:材质咨询），绝不能判为涂层脱落（质量问题）；“没有坏”代表无故障（拒绝否定词误判）。
4. requires_human (是否转人工): true/false。涉及资金退赔或质量鉴定的必须为 true。
5. suggested_reply (建议回复): 一句专业得体的客服话术。
6. escalation_reason (升级理由): 若 requires_human 为 true，给出具体理由，否则填 null。

请严格仅输出一段合法的 JSON，不要包含任何 Markdown 标记 (如 ```json) 或额外解释：
{
  "category": "...",
  "priority": "...",
  "entities": {"product": "...", "issue": "...", "request": "..."},
  "requires_human": true,
  "suggested_reply": "...",
  "escalation_reason": "..."
}

客户对话：{user_input}
"""

def generate_candidate_label(user_input: str) -> dict:
    try:
        # 使用 replace 替换变量，完美避开 Python 对 JSON 花括号的误解析
        prompt_content = PROMPT_TEMPLATE.replace("{user_input}", user_input)
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一个无情的 JSON 生成机器。只输出合法的 JSON，绝对不要包含任何 markdown 标记、问候语或解释。"},
                {"role": "user", "content": prompt_content}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}  # 强制大模型输出 JSON 格式
        )
        result = response.choices[0].message.content.strip()
        
        # 暴力提取 JSON
        start_idx = result.find('{')
        end_idx = result.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            clean_json = result[start_idx:end_idx+1]
            return json.loads(clean_json)
        else:
            print(f"未匹配到有效的 JSON 结构: {result}")
            return None
            
    except Exception as e:
        print(f"API 调用或解析失败: {user_input} | 错误: {e}")
        return None

def main():
    print("启动大模型 API 辅助打标流水线")
    excel_path = "data/raw/ecommerce_tickets_500_v1.xlsx"
    if not os.path.exists(excel_path):
        excel_path = "data/raw/500_v1.xlsx"
        
    xls = pd.ExcelFile(excel_path)
    
    all_texts = []
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        if '1st message' in df.columns:
            # 提取当前 Sheet 里的有效文本并加入总列表
            texts_in_sheet = df['1st message'].dropna().astype(str).tolist()
            # 过滤掉空字符串
            texts_in_sheet = [t.strip() for t in texts_in_sheet if t.strip()]
            all_texts.extend(texts_in_sheet)
            
    total_count = len(all_texts)
    
    candidates = []
    for i, text in enumerate(all_texts):
        print(f"正在处理 [{i+1}/{total_count}]: {text}")
        label = generate_candidate_label(text)
        if label:
            candidates.append({"input": text, "candidate_output": label, "human_verified": False})
            
    # 保存全量数据
    output_path = "data/processed/llm_candidates_all_for_review.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)
        
    print(f"\n成功生成 {len(candidates)} 条候选标注，已保存至 {output_path}")



if __name__ == "__main__":
    main()