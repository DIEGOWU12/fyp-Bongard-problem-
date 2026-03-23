import re
import os

# 1. 获取当前脚本所在的绝对路径，确保读写的是同一个文件
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "patterns_report.txt")

print(f"正在操作的文件路径: {file_path}")

# 读取原始报告
if not os.path.exists(file_path):
    print("❌ 错误：找不到 patterns_report.txt 文件！")
else:
    with open(file_path, "r", encoding="utf-8") as f:
        raw_data = f.read()

    def sort_patterns(text):
        # 提取 ID 和 数量
        pattern = r"ID:\s*(BP\d+)\s*\|\s*Total Images:\s*(\d+)"
        matches = re.findall(pattern, text)
        
        print(f"🔍 扫描完毕，抓取到 {len(matches)} 条数据")

        if len(matches) == 0:
            print("⚠ 警告：没有匹配到任何数据，请检查文件格式！")
            return

        # --- 从小到大排序 (去掉 reverse=True) ---
        sorted_list = sorted(matches, key=lambda x: int(x[1]))
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("--- Sorted Bongard Problems by Image Count (Ascending) ---\n")
            for bp_id, count in sorted_list:
                line = f"ID: {bp_id} | Total Images: {count}\n"
                f.write(line)
            # 强制刷新缓存到磁盘
            f.flush()
            os.fsync(f.fileno())

    if __name__ == "__main__":
        sort_patterns(raw_data)
        print(f"\n✅ 任务结束！请重新打开 {file_path} 查看。")