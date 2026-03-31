import json

def update_bongard_rules(input_json, output_json):
    # 1. 读取原始 JSON
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = data['questions']
    
    # 2. 建立一个映射表，存储每个 BP 对应的 Left Rule
    # 格式: { "BP1002": "Vaguely self-similar..." }
    left_rule_map = {}
    for q in questions:
        if q['target_side'] == 'left':
            left_rule_map[q['bp']] = q['rule_description']

    # 3. 遍历并更新 Neg 题目的规则
    updated_count = 0
    for q in questions:
        if q['target_side'] == 'right':
            # 获取当前 BP 对应的左侧规则
            positive_rule = left_rule_map.get(q['bp'], "")
            
            # 如果当前的规则是 "not so." 或类似的模糊描述
            if "not so" in q['rule_description'].lower() and positive_rule:
                # 拼接规则：例如 "not so (Vaguely self-similar...)"
                new_rule = f"Not so ({positive_rule})"
                q['rule_description'] = new_rule
                updated_count += 1

    # 4. 保存新 JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"✨ 处理完成！共更新了 {updated_count} 条 'not so' 规则。")
    print(f"📂 已保存至: {output_json}")

# --- 运行 ---
input_file = "bongard_v2_dual_tasks.json" # 你的原始文件名
output_file = "bongard_v2_refined_rules.json"

if __name__ == "__main__":
    update_bongard_rules(input_file, output_file)