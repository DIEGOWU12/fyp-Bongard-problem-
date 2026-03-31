import json
import os
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

# 1. 设定本地模型路径
# 注意：Windows 路径建议使用 r"" 原始字符串
MODEL_PATH = r"D:\qwenVL\Qwen3-VL-8B-Instruct" 
DATASET_ROOT = r"C:\Users\fypuser\Documents\fyp-Bongard-problem-\Bongard_Dataset_v2"
JSON_PATH = "bongard_v2_dual_tasks.json"

# 2. 初始化模型
print(f"正在从本地加载模型: {MODEL_PATH}...")
model = Qwen2VLForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16, # 显存小，用 float16
    device_map="auto",
    load_in_4bit=True,         # 开启 4-bit 量化
)
processor = AutoProcessor.from_pretrained(
    MODEL_PATH, 
    min_pixels=128 * 28 * 28,  # 约 313,600 像素
    max_pixels=448 * 28 * 28,  # 约 351,232 像素 (比 512*28*28 更稳妥)
)

def run_evaluation():
    # 读取 JSON 数据库
    if not os.path.exists(JSON_PATH):
        print(f"❌ 找不到 JSON 文件: {JSON_PATH}")
        return
        
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = data['questions']
    results = []
    
    print(f"开始测试，总计题目数: {len(questions)}")

    # 为了安全起见，你可以先只测试前 5 道题：questions[:5]
    for q in questions:
        bp_folder = q['bp']
        
        # 拼接图片绝对路径 (Context 5张 + Options 4张)
        context_paths = [os.path.join(DATASET_ROOT, bp_folder, img) for img in q['context']]
        option_paths = [os.path.join(DATASET_ROOT, bp_folder, img) for img in q['options']]
        
        # 3. 构造消息结构
        # 提示词：告诉模型这是一个寻找规律的任务
        content = [{"type": "text", "text": "Observe the following 5 images (Context) that follow a specific geometric or logical rule."}]
        
        # 添加 Context 图片
        for p in context_paths:
            content.append({"type": "image", "image": f"file://{p}"})
        
        content.append({"type": "text", "text": "\nNow look at these 4 options (A, B, C, D). Which one follows the SAME rule as the Context images?"})
        
        # 添加 Options 图片
        for i, p in enumerate(option_paths):
            letter = chr(65 + i)
            content.append({"type": "text", "text": f"\nOption {letter}:"})
            content.append({"type": "image", "image": f"file://{p}"})
            
        content.append({"type": "text", "text": "\nAnswer with the letter (A, B, C, D) only."})

        messages = [{"role": "user", "content": content}]

        # 4. 推理预处理
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        ).to("cuda")

        # 5. 生成答案
        with torch.no_grad():
            generated_ids = model.generate(**inputs, max_new_tokens=10)
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = processor.batch_decode(
                generated_ids_trimmed, 
                skip_special_tokens=True, 
                clean_up_tokenization_spaces=False
            )[0].strip()

        # 6. 验证与记录
        # 简单清洗输出，只取第一个字母
        prediction = ""
        for char in output_text.upper():
            if char in ['A', 'B', 'C', 'D']:
                prediction = char
                break
                
        is_correct = (prediction == q['correct'])
        
        print(f"[{q['question_id']}] 推测: {prediction} | 正确: {q['correct']} | {'✅' if is_correct else '❌'}")
        
        results.append({
            "id": q['question_id'],
            "target_side": q['target_side'],
            "prediction": prediction,
            "ground_truth": q['correct'],
            "is_correct": is_correct
        })

    # 7. 保存结果并输出准确率
    with open("inference_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    accuracy = sum([1 for r in results if r['is_correct']]) / len(results) if results else 0
    print(f"\n" + "="*30)
    print(f"测试完成！最终准确率: {accuracy * 100:.2f}%")
    print(f"详细日志已保存至: inference_results.json")
    print("="*30)

if __name__ == "__main__":
    run_evaluation()