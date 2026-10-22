import pandas as pd
import json
import os
import re
from pathlib import Path
import sys

# 动态添加项目根目录到 Python 路径，确保能导入 src.schemas
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.schemas import TicketOutput

# 1. 核心商品词库 (20类小家电)
PRODUCTS = [
    "电热水壶", "电饭煲", "迷你电饭锅", "电磁炉", "微波炉", "空气炸锅", "电烤箱", 
    "破壁机", "豆浆机", "榨汁机", "原汁机", "咖啡机", "电煮锅", "多功能料理锅", 
    "电吹风", "电动牙刷", "剃须刀", "卷发棒", "直发夹板", "加湿器", "电风扇", 
    "循环扇", "取暖器", "小太阳", "吸尘器", "手持除尘器", "挂烫机", "蒸汽熨斗", 
    "按摩仪", "颈椎按摩器"
]

INSTRUCTION_TEXT = (
    "你是电商客服坐席辅助系统。请根据客户对话，输出工单分类、风险等级、实体、"
    "是否需要人工审核、建议回复和升级理由。只输出 JSON。"
    "涉及退款审批时必须转人工，不得承诺未经核实的退款结果。"
)

def extract_fine_grained_features(msg: str, category: str):
    """
    """
    # --- A. 提取商品实体 (Product) ---
    product = "未提及"
    for p in PRODUCTS:
        if p in msg:
            product = p
            break
    if product == "未提及" and ("发票" in msg or "专票" in msg or "订单" in msg):
        product = "订单"

    # --- B. 细粒度提取问题 (Issue) 与 诉求 (Request) ---
    issue = "常规咨询"
    request = "请求解答或处理"

    # 1. 安全与高危红线 (P0)
    if "漏电" in msg or "带电" in msg or "麻感" in msg:
        issue, request = "漏电安全隐患", "要求退货并追责"
    elif "冒烟" in msg or "起火" in msg or "火花" in msg or "打火" in msg:
        issue, request = "冒烟/打火安全隐患", "要求立即停用退货"
    elif "焦糊味" in msg or "焦味" in msg:
        issue, request = "电机焦糊味隐患", "安全咨询与售后处理"
    elif "炸裂" in msg or "开裂" in msg:
        issue, request = "面板/玻璃炸裂", "安全处理与退货"
    elif "烫伤" in msg or "刮伤" in msg or "刺痛" in msg or "过敏" in msg:
        issue, request = "使用造成人身不适/伤害", "要求退货并赔偿说明"
    elif "倾倒" in msg or ("水开" in msg and "不断电" in msg):
        issue, request = "防干烧/倾倒断电保护失效", "担心安全隐患要求退货"
    elif "泄露" in msg or "骚扰电话" in msg:
        issue, request = "个人隐私信息泄露", "维权与严肃投诉"
    elif "承诺没兑现" in msg or "要投诉" in msg or "12315" in msg:
        issue, request = "客服未履约/服务不満", "要求投诉与主管介入"

    # 2. 退款售后与价格优惠 (P1)
    elif "降价" in msg or "保价" in msg or "买贵" in msg or "退差价" in msg or "补差" in msg:
        issue, request = "商品降价/保价申诉", "申请退补差价"
    elif "凑满减" in msg or ("满" in msg and "减" in msg):
        issue, request = "满减凑单退单件优惠计算", "退单件并咨询优惠分摊"
    elif "标价" in msg and "结算" in msg:
        issue, request = "页面标价与结算价不符", "查询差价原因"
    elif "学生认证" in msg or "新人" in msg:
        issue, request = "身份/新人特权优惠未生效", "追究优惠原因并补差"
    elif "券" in msg or "红包" in msg or "积分" in msg:
        issue, request = "优惠券/红包/积分退还异常", "查询优惠退回规则"
    elif "运费险" in msg or "垫了" in msg or "运费" in msg:
        issue, request = "退货运费及运费险争议", "咨询运费承担方或报销时效"
    elif "分期" in msg or "手续费" in msg or "花呗" in msg or "白条" in msg:
        issue, request = "分期手续费与退款路径疑问", "查询退款去向及手续费退还"
    elif "以旧换新" in msg:
        issue, request = "以旧换新补贴未到账", "催促发放补贴"
    elif "秒杀" in msg and "取消" in msg:
        issue, request = "秒杀订单被异常取消", "要求恢复订单或赔偿"
    elif "少" in msg and ("退款" in msg or "差额" in msg or "不一致" in msg or "扣" in msg):
        issue, request = "实际退款金额与实付不符", "核对退款差额明细"
    elif "三天" in msg or "到账慢" in msg or "没到" in msg or "没收到" in msg and "退款" in msg:
        issue, request = "退款迟迟未到账", "查询退款进度并催促加急"
    elif "赠品" in msg or "送" in msg:
        issue, request = "赠品漏发/折价争议", "要求补发赠品或折现"

    # 3. 退货换货与商品质量 (P1)
    elif "影响二次销售" in msg or "被拒" in msg or "驳回" in msg:
        issue, request = "售后退货申请被拒", "申诉要求重新通过退货退款"
    elif "拆封" in msg or "七天无理由" in msg:
        issue, request = "七天无理由及拆封退货规则", "要求办理退货退款"
    elif "先寄新" in msg or "换货太慢" in msg:
        issue, request = "换货时效过慢", "申请闪电换新或直接退款"
    elif "退货地址" in msg:
        issue, request = "多仓退货地址确认", "确认正确退回地址"
    elif "维修" in msg or "过保" in msg or "保修" in msg:
        issue, request = "设备保修与寄修流程", "咨询维修费用或换新方案"
    elif "不通电" in msg or "没反应" in msg or "不亮" in msg or "充不进电" in msg:
        if category == "商品咨询":
            issue, request = "指示灯/通电状态疑问", "咨询是否属于正常现象"
        else:
            issue, request = "设备完全不通电/无法启动", "反馈质量故障要求换新或退货"
    elif "用一次就坏" in msg or "两次换货" in msg or "翻新机" in msg:
        issue, request = "严重质量缺陷/质疑翻新", "要求售后追责与退换"
    elif "涂层" in msg or "掉漆" in msg or "生锈" in msg or "糊底" in msg or "粘锅" in msg:
        issue, request = "内胆涂层脱落/糊底生锈", "要求更换配件或整机退换"
    elif "漏水" in msg or "渗水" in msg or "滴水" in msg or "溢锅" in msg:
        issue, request = "机身/水箱密封不良漏水", "申请换新或退货"
    elif "噪音" in msg or "异响" in msg or "晃动" in msg:
        if category == "商品咨询":
            issue, request = "运行分贝与噪音参数", "咨询正常工作音量"
        else:
            issue, request = "运行噪音过大/异常抖动", "反馈质量问题要求退换"
    elif "不加热" in msg or "加热很慢" in msg or "温控" in msg or "夹生" in msg or "不热" in msg:
        issue, request = "加热故障/温控失准", "质疑功率虚标或申请售后"
    elif "划痕" in msg or "破损" in msg or "变形" in msg or "断了" in msg or "松动" in msg:
        issue, request = "外观瑕疵/零部件破损", "要求补发配件或换货"
    elif "塑料味" in msg or "异味" in msg:
        issue, request = "机器散发刺鼻异味", "质疑材质安全要求退换"
    elif "续航" in msg or "没电" in msg:
        if category == "商品咨询":
            issue, request = "电池续航参数", "咨询满电使用时长"
        else:
            issue, request = "电池续航严重缩水虚标", "要求退换货"
    elif "吸力" in msg or "风量" in msg or "出汁率" in msg or "不出雾" in msg or "不出蒸汽" in msg:
        issue, request = "核心性能不达标/功能失效", "要求退货或换新"

    # 4. 物流异常 (P1 / P2)
    elif "顺丰" in msg and ("中通" in msg or "圆通" in msg):
        issue, request = "指定快递与实际不符", "质疑虚假发货要求补偿或重发"
    elif "五天" in msg or "四天" in msg or "没单号" in msg:
        issue, request = "严重超时未发货", "紧急催促发货"
    elif "签收" in msg and "没收到" in msg:
        issue, request = "物流虚假签收/丢件", "核实包裹下落并追责"
    elif "压坏" in msg or "外包装破损" in msg:
        issue, request = "暴力运输导致包装/商品破损", "要求拒收补发或赔偿"
    elif "发错" in msg or "少发" in msg:
        issue, request = "仓库错发/漏发商品", "要求补发或换货"
    elif "改地址" in msg or "拦截" in msg:
        issue, request = "修改收货地址与物流拦截", "请求拦截包裹并改址"
    elif "加急" in msg or "急用" in msg:
        issue, request = "急用商品催促配送", "请求优先加急发货"
    elif "没揽收" in msg or "不更新" in msg or "无轨迹" in msg or "停滞" in msg:
        issue, request = "物流轨迹停滞/未揽收", "查询真实发货状态并催件"
    elif "驿站" in msg or "快递柜" in msg:
        issue, request = "未经同意投放驿站/快递柜", "投诉快递并要求送货上门"

    # 5. 其他边界与常规商品咨询 (P1 / P2)
    elif "专票" in msg or "发票" in msg:
        issue, request = "发票开具/重开抬头", "申请补开或修改专票/普票"
    elif "包安装" in msg and "收费" in msg:
        issue, request = "安装服务违规乱收费", "投诉安装网点并退还费用"
    elif "批量" in msg or "采购" in msg:
        issue, request = "企业批量采购部分故障", "确认对公局部退换方案"
    elif "既想退又想换" in msg:
        issue, request = "同一订单复合退换诉求", "咨询拆单退换操作流程"
    elif "哪个划算" in msg:
        issue, request = "保价与重新下单优惠对比", "请求客服帮忙算账对比"
    elif "不会安装" in msg or "看不懂" in msg or "怎么用" in msg or "模式" in msg or "度" in msg:
        issue, request = "产品操作与使用指导", "索取教程或咨询使用方法"
    elif "能用" in msg or "可以放" in msg or "兼容" in msg:
        issue, request = "配件/耗材/容器兼容性", "咨询是否支持混用"
    elif "材质" in msg or "304" in msg or "涂层" in msg:
        issue, request = "商品材质与安全标准", "确认核心部件材质"
    elif "容量" in msg or "功率" in msg or "几档" in msg or "多久" in msg or "多大" in msg:
        issue, request = "商品规格参数查询", "咨询具体性能指标"

    # 如果处于退货换货前30条跨界样本（带有“如果换不了，麻烦直接办理退款”）
    if "如果换不了，麻烦直接办理退款" in msg or "换不了的话就直接退款" in msg:
        request = "要求优先换货，若无法满足则直接全额退款"

    # --- C. 严格判定 Priority 与 人工介入 (Requires Human) ---
    priority = "P2"
    requires_human = False
    escalation_reason = None

    # P0 触发条件：安全、隐私泄露、明确投诉
    p0_keywords = ["漏电", "带电", "麻感", "冒烟", "起火", "火花", "打火", "焦糊味", "焦味", 
                   "炸裂", "开裂", "烫伤", "刮伤", "刺痛", "过敏", "泄露", "骚扰电话", 
                   "要投诉", "12315", "曝光", "倾倒断电失效", "不断电"]
    
    # P1 触发条件：钱、退换、质量、错发漏发、虚假签收、企业专票
    p1_categories = ["退款售后", "退货换货", "商品质量"]
    p1_keywords = ["发错", "少发", "压坏", "破损", "签收但我没收到", "签收未收到", "顺丰", 
                   "五天", "四天", "拦截", "偏远", "发票", "专票", "收费", "批量", 
                   "既想退又想换", "折现", "补偿", "赔偿", "差价", "划算"]

    if any(k in msg for k in p0_keywords):
        priority = "P0"
        requires_human = True
        escalation_reason = f"触发最高风险 P0（{issue}），存在安全或严重合规隐患，必须立即由高级专员人工介入处理"
    elif category in p1_categories or any(k in msg for k in p1_keywords):
        priority = "P1"
        requires_human = True
        escalation_reason = f"涉及{issue}与具体售后裁定，机器人无权自动审批，需转人工核实订单与凭证后处理"
    else:
        priority = "P2"
        requires_human = False
        escalation_reason = None

    # --- D. 生成极具针对性的建议回复 (Suggested Reply) ---
    prod_str = product if product not in ["未提及", "订单"] else "商品"
    
    if priority == "P0":
        if "泄露" in msg or "投诉" in msg or "兑现" in msg:
            suggested_reply = f"非常抱歉给您带来如此糟糕的体验！您反馈的{issue}问题我们高度重视，我已为您紧急转接高级客诉主管彻查此事，定会给您一个满意的交代。"
        else:
            suggested_reply = f"【安全提醒】请您立即拔掉电源并停止使用该{prod_str}！非常抱歉让您受到惊吓，您的安全最重要。我已为您加急转接安全售后专员，马上为您优先办理退货退款及后续处理。"
    elif priority == "P1":
        if category == "退款售后" or "差价" in request or "优惠" in issue:
            suggested_reply = f"您好，关于您反映的{prod_str}{issue}问题，由于涉及具体的订单实付金额与活动规则核算，我马上为您转接人工财务专员帮您查验明细并跟进处理，请稍等。"
        elif category in ["退货换货", "商品质量"]:
            suggested_reply = f"您好，非常抱歉{prod_str}的{issue}问题影响了您的体验。请您放心，质量与售后问题我们绝不推诿。已为您转接人工售后专员，请您提供一下相关照片或单号，专员将为您优先办理。"
        elif category == "物流异常":
            suggested_reply = f"您好，非常抱歉物流问题耽误了您的使用！针对{issue}的情况，我已为您紧急转接人工物流专员，马上联系仓库与快递网点为您核实拦截或安排补发。"
        else:
            suggested_reply = f"您好，您反馈的{issue}诉求已详细记录。由于该业务需要特殊人工权限处理，我已经为您转接专属人工客服为您一对一跟进办理，请您稍候。"
    else:
        if category == "物流异常":
            suggested_reply = f"您好，系统已为您查询{prod_str}的最新物流状态。包裹目前在正常流转時效内，偶有网点扫描延迟请您谅解。我们已在后台发起催促，请留意最新轨迹更新。"
        else:
            suggested_reply = f"您好，感谢您的咨询！关于{prod_str}的{issue}，标准操作与参数说明均已在商品详情页及附带的说明书中详细列出，您可以随时查阅并放心使用哦。"

    # 修正类别名称以严格符合 Pydantic Schema 的 Literal 定义
    schema_category = "其他/边界" if category == "其他边界" else category

    # 用 Pydantic 模型做一次强制校验，确保生成的数据 100% 合法
    validated_output = TicketOutput(
        category=schema_category,
        priority=priority,
        entities={
            "product": product,
            "issue": issue,
            "request": request
        },
        requires_human=requires_human,
        suggested_reply=suggested_reply,
        escalation_reason=escalation_reason
    )

    return validated_output.model_dump()


def build_sft_dataset(input_excel: str, golden_json: str, output_jsonl: str):
   

    # 1. 自动寻找 Excel 文件路径 (兼容不同命名)
    if not os.path.exists(input_excel):
        alt_excel = "data/raw/ecommerce_tickets_500_v1.xlsx"
        if os.path.exists(alt_excel):
            input_excel = alt_excel
        else:
            print(f" 错误：找不到 {input_excel} 或 {alt_excel}，请检查 data/raw/ 目录！")
            return

    print(f"正在读取原始数据源: {input_excel}")

    # 2. 加载 30 条人工精标的样本
    golden_map = {}
    if os.path.exists(golden_json):
        with open(golden_json, 'r', encoding='utf-8') as f:
            golden_list = json.load(f)
            for item in golden_list:
                # 统一清洗 key 以便精准匹配
                clean_key = item["input"].replace("客户：", "").strip()
                
                if item["output"].get("category") == "其他边界":
                    item["output"]["category"] = "其他/边界"
                golden_map[clean_key] = item["output"]
        print(f"成功加载 {len(golden_map)} 条手动标注。")
    else:
        print(f"未找到 {golden_json}。")

    # 3. 遍历 Excel 的 6 个 Sheet 进行处理
    xls = pd.ExcelFile(input_excel)
    final_records = []
    golden_hit_count = 0
    engine_gen_count = 0

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        for _, row in df.iterrows():
            if '1st message' not in row or pd.isna(row['1st message']):
                continue
            
            user_msg = str(row['1st message']).strip()
            if not user_msg:
                continue

            # 优先匹配 30 条
            if user_msg in golden_map:
                output_dict = golden_map[user_msg]
                golden_hit_count += 1
            else:
                output_dict = extract_fine_grained_features(user_msg, sheet_name)
                engine_gen_count += 1

            # 构造标准 SFT 训练对
            
            sft_sample = {
                "instruction": INSTRUCTION_TEXT,
                "input": f"客户：{user_msg}",
                "output": json.dumps(output_dict, ensure_ascii=False),
                # 保留结构化字段供内部 eval_runner 评测脚本直接读取，一举两得
                "raw_output": output_dict
            }
            final_records.append(sft_sample)

    # 4. 保存结果
    out_path = Path(output_jsonl)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        for rec in final_records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')

    print("\n 数据集构建圆满完成！")
    print(f" 统计明细：总计 {len(final_records)} 条 = 原样本命中 {golden_hit_count} 条 + 细粒度引擎精标 {engine_gen_count} 条")
    print(f" 输出路径：{output_jsonl}")

if __name__ == "__main__":

    EXCEL_PATH = "data/raw/ecommerce_tickets_500_v1"
    GOLDEN_PATH = "data/manually_label_data_30.json"
    OUTPUT_PATH = "data/processed/cleaned_tickets.jsonl"
    
    build_sft_dataset(EXCEL_PATH, GOLDEN_PATH, OUTPUT_PATH)
