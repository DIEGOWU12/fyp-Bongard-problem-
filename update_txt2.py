import os
import re

def modify_bongard_prompts(folder_path):
    if not os.path.exists(folder_path):
        print(f"找不到路径: {folder_path}")
        return

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                # 提取原逻辑描述：从 "features a " 开始，截取到 " logic" 之前的内容
                # 这样可以兼容带引号或不带引号的情况
                match = re.search(r"features a (.*?) logic", content, re.IGNORECASE)
                
                if match:
                    extracted_logic = match.group(1).strip().strip("'").strip('"')
                else:
                    # 默认保底逻辑
                    extracted_logic = "filled in solid"

                # 构建最终要求的简洁模板
                new_prompt = (
                    f"Bongard style, one large composite image consisting of six individual images arranged in a 3x2 layout. "
                    f"Each of the six images features a '{extracted_logic}' logic."
                )

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_prompt)
                
                print(f"Updated: {filename} -> logic: {extracted_logic}")
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")

# 执行修改
target_path = r'C:\Users\Lenovo\OneDrive\文档\GitHub\fyp-Bongard-problem-\kohya_train_data\10_BongardStyle'
modify_bongard_prompts(target_path)