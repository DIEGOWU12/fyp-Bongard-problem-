import re

# 读取原始报告
with open("patterns_report.txt", "r", encoding="utf-8") as f:
    raw_data = f.read()

def sort_patterns(text):
    # 1. 提取 ID 和 数量
    pattern = r"ID:\s*(BP\d+)\s*\|\s*Total Images:\s*(\d+)"
    matches = re.findall(pattern, text)
    
    # 2. 核心修改：去掉 reverse=True，实现从小到大排序
    # key=lambda x: int(x[1]) 确保是按数字大小排，而不是按字符排
    sorted_list = sorted(matches, key=lambda x: int(x[1]))
    
    # 3. 格式化输出并保存
    with open("patterns_report.txt", "w", encoding="utf-8") as f:
        f.write("--- Sorted Bongard Problems by Image Count (Ascending) ---\n")
        for bp_id, count in sorted_list:
            line = f"ID: {bp_id} | Total Images: {count}\n"
            f.write(line)
            print(line.strip())

if __name__ == "__main__":
    if raw_data.strip():
        sort_patterns(raw_data)
        print(f"\n✅ 排序完成！现在是按照图片数量“从小到大”排列了。")
    else:
        print("⚠ 文件是空的，没东西可以排序哦宝宝。")