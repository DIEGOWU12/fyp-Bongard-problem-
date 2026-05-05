import torch
from diffusers import StableDiffusionXLPipeline

# 1. 设置模型路径
# base_model_path 是你截图里用的 stabilityai/stable-diffusion-xl-base-1.0
base_model_path = "stabilityai/stable-diffusion-xl-base-1.0"
# weight_path 是你训练出来的那个几 GB 的文件路径
weight_path = r"D:\kohya_ss\outputs\sdxl_trained_3.safetensors"

# 2. 加载基础模型
print("正在加载基础模型...")
pipe = StableDiffusionXLPipeline.from_pretrained(
    base_model_path, 
    torch_dtype=torch.float16, 
    variant="fp16", 
    use_safetensors=True
).to("cuda")

# 3. 加载你训练的权重
# 如果你训练的是全量微调（Dreambooth），用下面的方式加载：
print("正在加载训练权重...")
pipe.load_lora_weights(weight_path) # 如果你训练的是 LoRA 请用这行
# 如果你训练的是全模型（Checkpoint），则直接在第一步将 base_model_path 替换为你的文件路径即可

# 4. 设置 Prompt
# 使用我们之前润色好的那个结构
prompt = (
    "Bongard style, one large composite image consisting of six individual images arranged in a 3x2 layout. "
    "Each of the six images features a 'filled in solid' logic."
)
negative_prompt = "lowres, bad anatomy, text, error, extra digit, fewer digits, cropped, worst quality, low quality"

# 5. 生成图片
print("正在生成图片...")
image = pipe(
    prompt=prompt,
    negative_prompt=negative_prompt,
    num_inference_steps=30,
    guidance_scale=7.5,
    width=1024,
    height=1024
).images[0]

# 6. 保存
image.save("bongard_output.png")
print("生成成功！图片已保存为 bongard_output.png")