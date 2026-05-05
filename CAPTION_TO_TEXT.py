import os

# 你的图片路径
data_path = r"/kohya_train_data/5_BongardStyle"

def rename_captions():
    files = os.listdir(data_path)
    count = 0
    for f in files:
        if f.endswith(".caption"):
            old_file = os.path.join(data_path, f)
            new_file = os.path.join(data_path, f.replace(".caption", ".txt"))
            # 如果 .txt 已存在则先删除，确保更新
            if os.path.exists(new_file):
                os.remove(new_file)
            os.rename(old_file, new_file)
            count += 1
    print(f"完成！成功转换了 {count} 个标签文件。")

if __name__ == "__main__":
    rename_captions()