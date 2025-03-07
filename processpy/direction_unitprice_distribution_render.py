import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# 定义城市缩写到全称的映射
CITY_FULL_NAMES = {"bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"}

# 定义城市列表及对应的 CSV 文件名
CITIES = {
    "bj": "../processed_data/bj_direction_unit.csv",
    "sh": "../processed_data/sh_direction_unit.csv",
    "gz": "../processed_data/gz_direction_unit.csv",
    "sz": "../processed_data/sz_direction_unit.csv",
    "tj": "../processed_data/tj_direction_unit.csv",
}

# 创建输出目录（如果不存在）
OUTPUT_DIR = "../product"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 设置绘图风格
sns.set_theme(style="whitegrid")

# 定义有效的朝向和对应的颜色
VALID_DIRECTIONS = ["东", "南", "西", "北", "南北"]

# 新的颜色方案（使用较为鲜艳且对比度高的颜色）
direction_colors = {
    "东": "#FF6347",  # 番茄红
    "南": "#32CD32",  # 石灰绿
    "西": "#1E90FF",  # 遇见蓝
    "北": "#FFD700",  # 金色
    "南北": "#8A2BE2",  # 蓝紫色
}

# 计算阈值：平均值 + 3 * 标准差
def calculate_threshold(df, column, multiplier=3):
    """计算阈值：平均值 + multiplier * 标准差"""
    mean = df[column].mean()
    std = df[column].std()
    threshold = mean + multiplier * std
    return threshold

# 绘制单位面积租金分布的函数
def plot_rent_distribution(df, city_name, threshold):
    """绘制各朝向单位面积租金的分布图"""
    # 设置图形大小
    plt.figure(figsize=(14, 10))

    # 设置中文字体和解决负号显示问题
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
    plt.rcParams["axes.unicode_minus"] = False

    # 绘制每个朝向的概率密度曲线
    for direction in VALID_DIRECTIONS:
        direction_data = df[df["朝向"] == direction]["单位面积租金（元/月/㎡）"]
        if not direction_data.empty:
            sns.kdeplot(
                direction_data,
                label=direction,
                color=direction_colors.get(direction, "gray"),
                linewidth=4,
                linestyle="-",  # 使用实线
                alpha=0.7,  # 设置线条透明度
            )

    # 设置标题和标签
    plt.title(f"{city_name}各朝向单位面积租金分布", fontsize=20, fontweight="bold")
    plt.xlabel("单位面积租金（元/月/㎡）", fontsize=16)
    plt.ylabel("概率密度", fontsize=16)

    # 设置图例，放置在图表外部
    plt.legend(title="朝向", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=12, title_fontsize=14)

    # 添加注释说明被排除的数据
    plt.text(
        0.95,
        0.95,
        f"已排除单位面积租金超过平均值+3标准差的数据\n共排除 {excluded_records} 条记录，占比 {excluded_percentage:.2f}%",
        horizontalalignment="right",
        verticalalignment="bottom",
        transform=plt.gca().transAxes,
        fontsize=12,
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
    )

    # 调整布局以防止标签被截断
    plt.tight_layout(rect=[0, 0, 0.85, 1])

    # 保存图表
    output_filename = os.path.join(OUTPUT_DIR, f"{city_name}_direction_unit_distribution.png")
    plt.savefig(output_filename, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"{city_name} 城市的单位面积租金分布图已成功保存到 {output_filename}")

# 处理每个城市的文件
for city_code, csv_path in CITIES.items():
    city_name = CITY_FULL_NAMES.get(city_code, city_code)

    if not os.path.exists(csv_path):
        print(f"文件 {csv_path} 不存在，跳过 {city_name} 城市。")
        continue

    # 读取 CSV 文件
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except Exception as e:
        print(f"读取文件 {csv_path} 失败，错误：{e}")
        continue

    # 检查必要的列是否存在
    if "朝向" not in df.columns or "单位面积租金（元/月/㎡）" not in df.columns:
        print(f"文件 {csv_path} 缺少必要的列，跳过 {city_name} 城市。")
        continue

    # 删除缺失值
    df = df.dropna(subset=["朝向", "单位面积租金（元/月/㎡）"])

    if df.empty:
        print(f"{city_name} 城市没有有效的数据。")
        continue

    # 筛选有效朝向
    df_valid = df[df["朝向"].isin(VALID_DIRECTIONS)]

    if df_valid.empty:
        print(f"{city_name} 城市没有有效的朝向数据。")
        continue

    # 计算单位面积租金的阈值（平均值 + 3 * 标准差）
    threshold = calculate_threshold(df_valid, "单位面积租金（元/月/㎡）", multiplier=3)

    # 计算被排除的数据数量和比例
    total_records = len(df)
    excluded_records = len(df[df["单位面积租金（元/月/㎡）"] > threshold])
    excluded_percentage = (excluded_records / total_records) * 100

    # 仅保留不超过阈值的数据
    df_filtered = df_valid[df_valid["单位面积租金（元/月/㎡）"] <= threshold]

    if df_filtered.empty:
        print(f"{city_name} 城市没有低于阈值的数据，跳过绘图。")
        continue

    # 绘制并保存图表
    plot_rent_distribution(df_filtered, city_name, threshold)

print("所有城市的单位面积租金分布图已完成。")
