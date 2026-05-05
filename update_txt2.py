import os
import re


def modify_bongard_prompts(folder_path):
    # 确保文件夹路径存在
    if not os.path.exists(folder_path):
        print(f"文件夹 {folder_path} 不存在。")
        return

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            # 修正后的正则：匹配 "features a" 之后到 "logic, showing" 之前的内容
            # 例如从 "features a 'filled in solid' logic, showing" 中提取出 "'filled in solid'"
            match = re.search(r"features a\s*(.*?)\s*logic,\s*showing", content, re.IGNORECASE)

            if match:
                extracted_logic = match.group(1).strip()
            else:
                # 如果没匹配到，默认给个占位符
                extracted_logic = "'filled in solid'"

            # 构建简化后的新 Prompt 模板（已去掉 minimalist aesthetic 等后缀）
            new_prompt = (
                f"Bongard style, one large composite image consisting of six individual images arranged in a 3x2 layout. "
                f"Each of the six images features a {extracted_logic} logic."
            )

            # 将修改后的内容写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_prompt)

            print(f"已更新: {filename}")

# 使用方法：将 'your_folder_path' 替换为你存放 txt 的文件夹路径
# modify_bongard_prompts('C:/Users/YourName/Desktop/Bongard_Prompts')