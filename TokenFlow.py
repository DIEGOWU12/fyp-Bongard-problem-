import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
import os

def solve_bongard(image_path, model_path):
    # 1. 检测硬件：14B 模型建议使用 bf16 以节省显存
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"正在使用设备: {device}")

    # 2. 加载 Tokenizer 和 Model
    # trust_remote_code=True 是必须的，因为 TokenFlow 包含自定义层
    print("正在加载模型，请稍候（这可能需要几分钟）...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, 
        torch_dtype=torch.bfloat16, 
        device_map="auto", 
        trust_remote_code=True
    ).eval()

    # 3. 准备 Bongard 图片
    if not os.path.exists(image_path):
        print(f"错误：找不到图片 {image_path}")
        return

    raw_image = Image.open(image_path).convert("RGB")
    
    # 4. 构造专门针对 Bongard Problem 的提示词
    # 我们要求模型先观察左侧(Index 1-6)再观察右侧(Index 7-12)
    prompt = (
        "This image contains 12 sub-figures. Figures 1-6 (left) follow a specific geometric rule, "
        "while Figures 7-12 (right) do not follow that rule. "
        "Please: 1. Describe the visual elements in the left group. "
        "2. Compare them with the right group. "
        "3. Identify the hidden rule (Bongard Problem). "
        "Answer in Chinese."
    )

    # 5. 构建输入格式 (符合 TokenFlow/LLaVA 的对话模板)
    # 注意：这里的 query 格式可能随版本微调，这是标准写法
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": raw_image},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    
    # 使用模型自带的处理器处理文本和图像
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    # 针对 TokenFlow 的特殊编码（参考官方 Demo）
    inputs = tokenizer(text, return_tensors="pt").to(device)
    # 注意：实际运行中需根据官方示例确认 image_tensor 的传入方式
    
    print("AI 正在思考中...")
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=1024,
            do_sample=False, # 解决逻辑问题建议关闭随机抽样
            temperature=0.0
        )
    
    # 6. 解码并输出结果
    response = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    print("\n=== AI 推理结果 ===")
    print(response)

if __name__ == "__main__":
    # 修改这里！
    MY_MODEL_DIR = "./models/Tokenflow-14B" 
    MY_IMAGE_PATH = "my_puzzle.jpg" 
    
    solve_bongard(MY_IMAGE_PATH, MY_MODEL_DIR)