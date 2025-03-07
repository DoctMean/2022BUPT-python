import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 定义城市缩写到全称的映射
city_full_names = {
    "bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"
}

# 定义城市列表及对应的文件名
cities = {
    "bj": "../processed_data/bj_room_price.csv",
    "sh": "../processed_data/sh_room_price.csv",
    "gz": "../processed_data/gz_room_price.csv",
    "sz": "../processed_data/sz_room_price.csv",
    "tj": "../processed_data/tj_room_price.csv",
}

# 定义统计指标
metrics = [
    "均值", "标准差", "中位数", "25%分位数", "75%分位数"
]

# 设置输出目录
output_dir = "../product"
os.makedirs(output_dir, exist_ok=True)

# 设置绘图风格
sns.set_theme(style="whitegrid")

# 检查并加载数据
def load_city_data(filename, city_full_name):
    """加载每个城市的CSV数据并返回一个处理后的DataFrame"""
    try:
        df = pd.read_csv(filename, encoding="utf-8-sig")
        required_columns = ["房屋类型", "均值", "标准差", "中位数", "25%分位数", "75%分位数"]

        if not all(col in df.columns for col in required_columns):
            print(f"文件 {filename} 缺少必要列，跳过 {city_full_name} 城市。")
            return None

        df["城市"] = city_full_name
        return df[required_columns + ["城市"]]

    except Exception as e:
        print(f"读取文件 {filename} 失败，错误：{e}")
        return None

# 合并所有城市的数据
def merge_city_data(cities, city_full_names):
    """合并所有城市的数据并返回一个DataFrame"""
    all_data = []
    for city_code, filename in cities.items():
        city_name = city_full_names.get(city_code, city_code)
        if not os.path.exists(filename):
            print(f"文件 {filename} 不存在，跳过 {city_name} 城市。")
            continue
        
        df_city = load_city_data(filename, city_name)
        if df_city is not None:
            all_data.append(df_city)
    
    if not all_data:
        print("没有有效的租金数据可供处理。")
        exit(1)

    return pd.concat(all_data, ignore_index=True)

# 绘制租金统计折线图
def plot_rent_statistics(df, city_full_name, output_dir, palette="Set2"):
    """为每个城市绘制租金统计信息的折线图，支持自定义颜色调色板"""
    df_melt = df.melt(id_vars=["房屋类型"], value_vars=metrics, var_name="统计指标", value_name="数值")

    plt.figure(figsize=(16, 10))
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 设置中文字体
    plt.rcParams["axes.unicode_minus"] = False

    # 使用自定义调色板或默认调色板
    sns.lineplot(data=df_melt, x="房屋类型", y="数值", hue="统计指标", marker="o", palette=palette)

    # 添加数据标签
    for line in plt.gca().lines:
        for x, y in zip(line.get_xdata(), line.get_ydata()):
            if pd.isna(y):
                continue
            label = f"{y:.2f}" if isinstance(y, float) and y < 1000 else f"{int(y)}"
            plt.text(x, y, label, ha="center", va="bottom" if y >= 0 else "top", fontsize=8, color="black")

    plt.title(f"{city_full_name}房屋类型租金统计信息对比", fontsize=18, fontweight="bold", pad=20)
    plt.xlabel("房屋类型", fontsize=14)
    plt.ylabel("金额（元/月）", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(title="统计指标", fontsize=10, title_fontsize=12, loc="upper right", bbox_to_anchor=(1, 1))

    output_filename = os.path.join(output_dir, f"{city_full_name}_room_price_line_chart.png")
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300, bbox_inches="tight")
    print(f"{city_full_name} 的租金统计图已成功保存到 {output_filename}")

# 主函数
def main():
    # 合并所有城市的数据
    df_all = merge_city_data(cities, city_full_names)

    # 自定义颜色调色板示例（使用调色板“muted”）
    custom_palette = sns.color_palette(["#FF6347", "#4682B4", "#32CD32", "#FFD700", "#8A2BE2"])


    # 绘制每个城市的租金统计折线图，使用自定义调色板
    for city_full_name in city_full_names.values():
        df_city = df_all[df_all["城市"] == city_full_name]
        if not df_city.empty:
            plot_rent_statistics(df_city, city_full_name, output_dir, palette=custom_palette)
        else:
            print(f"城市 {city_full_name} 没有数据，跳过。")

if __name__ == "__main__":
    main()
