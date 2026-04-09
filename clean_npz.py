import os

# 定义你的数据集路径（请确保路径正确）
target_dir = r'D:\user\Documents\GitHub\fyp-bongard-problem-\kohya_train_data'

print(f"开始清理路径下的 .npz 文件: {target_dir}")

count = 0
for root, dirs, files in os.walk(target_dir):
    for file in files:
        if file.endswith('.npz'):
            file_path = os.path.join(root, file)
            try:
                os.remove(file_path)
                print(f"已删除: {file}")
                count += 1
            except Exception as e:
                print(f"无法删除 {file}: {e}")

print(f"--- 清理完成！共删除了 {count} 个缓存文件 ---")