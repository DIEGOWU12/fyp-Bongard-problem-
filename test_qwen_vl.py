import json
import os
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

# 1. 初始化模型和处理器 (确保路径指向你下载好的本地模型)
model_path = "Qwen/Qwen2-VL-7B-Instruct" # 或者你的本地绝对路径
model = Qwen2VLForConditionalGeneration.from_pretrained(
    model_path, torch_dtype="auto", device_map="auto"
)
processor = AutoProcessor.from_pretrained(model_path)

def run_inference(json_path, dataset_root):
    # 2. 读取之前生成的 JSON 数据库
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = data['questions']
    results = []

    for q in questions:
        bp_folder = q['bp']
        
        # 构建图片路径列表 (Context 5张 + Options 4张)
        context_paths = [os.path.join(dataset_root, bp_folder, img) for img in q['context']]
        option_paths = [os.path.join(dataset_root, bp_folder, img) for img in q['options']]
        
        # 3. 构造 Prompt
        # 告诉模型：前5张是例子，后4张是选项，选一个符合例子的
        prompt_text = "These 5 images follow a specific pattern. Which of the 4 options (A, B, C, D) follows the same pattern?"
        
        # 构造多图消息结构
        content = [{"type": "text", "text": "Context images:"}]
        for p in context_paths:
            content.append({"type": "image", "image": f"file://{p}"})
        
        content.append({"type": "text", "text": "\nOptions (A, B, C, D):"})
        for i, p in enumerate(option_paths):
            letter = chr(65 + i)
            content.append({"type": "text", "text": f" {letter}:"})
            content.append({"type": "image", "image": f"file://{p}"})
            
        content.append({"type": "text", "text": "\nOutput the letter of the correct answer only."})

        messages = [{"role": "user", "content": content}]

        # 4. 模型推理
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt")
        inputs = inputs.to("cuda")

        generated_ids = model.generate(**inputs, max_new_tokens=10)
        generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
        output_text = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

        # 5. 记录结果
        is_correct = output_text.strip().upper() == q['correct']
        print(f"Task: {q['question_id']} | Model: {output_text} | GT: {q['correct']} | {'✅' if is_correct else '❌'}")
        
        results.append({
            "id": q['question_id'],
            "model_output": output_text,
            "ground_truth": q['correct'],
            "is_correct": is_correct
        })

    # 6. 计算最终准确率
    accuracy = sum([1 for r in results if r['is_correct']]) / len(results)
    print(f"\nFinal Accuracy: {accuracy * 100:.2f}%")

# --- 运行配置 ---
DATASET_ROOT = r"C:\Users\fypuser\Documents\fyp-Bongard-problem-\Bongard_Dataset_v2"
JSON_PATH = "bongard_v2_dual_tasks.json"

run_inference(JSON_PATH, DATASET_ROOT)