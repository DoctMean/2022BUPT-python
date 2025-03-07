import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# 定义城市缩写与全称的映射
city_mapping = {"bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"}

# 定义每个城市对应的 CSV 文件路径
cities = {
    "bj": "../processed_data/bj_direction_unit.csv",
    "sh": "../processed_data/sh_direction_unit.csv",
    "gz": "../processed_data/gz_direction_unit.csv",
    "sz": "../processed_data/sz_direction_unit.csv",
    "tj": "../processed_data/tj_direction_unit.csv",
}

# 定义有效的朝向
valid_directions = ["东", "南", "西", "北", "南北"]

# 创建输出目录（如果不存在）
output_dir = "../product"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 初始化一个空的 DataFrame 来存储所有城市的有效数据
all_data = pd.DataFrame(columns=["城市", "朝向", "单位面积租金（元/月/㎡）"])

# 遍历每个城市的 CSV 文件，收集有效的朝向数据
for city_code, csv_path in cities.items():
    city_name = city_mapping.get(city_code, city_code)

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
    required_columns = ["朝向", "单位面积租金（元/月/㎡）"]
    if not all(col in df.columns for col in required_columns):
        print(f"文件 {csv_path} 缺少必要的列 {required_columns}，跳过 {city_name} 城市。")
        continue

    # 删除缺失值
    df = df.dropna(subset=required_columns)

    if df.empty:
        print(f"{city_name} 城市的数据为空，跳过。")
        continue

    # 筛选有效朝向
    df_valid = df[df["朝向"].isin(valid_directions)]

    if df_valid.empty:
        print(f"{city_name} 城市没有有效的朝向数据，跳过。")
        continue

    # 添加城市名称列
    df_valid["城市"] = city_name

    # 去除极大值：单位面积租金 > 平均值 + 2 * 标准差
    # 这里我们按朝向分组进行处理
    def remove_outliers(group):
        mean = group["单位面积租金（元/月/㎡）"].mean()
        std = group["单位面积租金（元/月/㎡）"].std()
        threshold = mean + 2 * std
        filtered_group = group[group["单位面积租金（元/月/㎡）"] <= threshold]
        removed = group[group["单位面积租金（元/月/㎡）"] > threshold]
        if not removed.empty:
            print(f"朝向 {group.name} 中移除了 {len(removed)} 个极大值。")
        return filtered_group

    # 应用去除极大值的函数
    df_filtered = df_valid.groupby("朝向").apply(remove_outliers).reset_index(drop=True)

    if df_filtered.empty:
        print(f"在城市 {city_name} 中，所有数据被移除后无有效数据。")
        continue

    # 将过滤后的有效数据追加到 all_data DataFrame
    all_data = pd.concat([all_data, df_filtered], ignore_index=True)

# 检查是否有数据可绘图
if all_data.empty:
    print("所有城市的数据在去除极大值后均为空，无法绘制箱线图。")
else:
    # 设置绘图风格
    sns.set_theme(style="whitegrid")

    # 设置图形大小
    plt.figure(figsize=(12, 8))
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 适用于macOS和Windows
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

    direction_colors = {
        "东": "#FF6347",  # 番茄红
        "南": "#32CD32",  # 石灰绿
        "西": "#1E90FF",  # 遇见蓝
        "北": "#FFD700",  # 金色
        "南北": "#8A2BE2"  # 蓝紫色
    }

    # 绘制箱线图
    box_plot = sns.boxplot(data=all_data, x="城市", y="单位面积租金（元/月/㎡）", hue="朝向", palette=direction_colors)

    # 设置标题和标签
    plt.title("五个城市各朝向单位面积租金价格分布", fontsize=16, fontweight="bold", pad=20)
    plt.xlabel("城市", fontsize=14)
    plt.ylabel("单位面积租金（元/月/㎡）", fontsize=14)

    # 设置刻度标签字体大小
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    # 调整图例位置到图像内部
    plt.legend(title="朝向", title_fontsize=12, fontsize=10, loc="upper right", bbox_to_anchor=(0.95, 0.95))

    # 获取 x 和 hue 的分类信息
    x_categories = all_data["城市"].unique()
    hue_categories = all_data["朝向"].unique()

    # 在箱线图上标注每个朝向的平均值
    for i, city in enumerate(x_categories):
        for j, direction in enumerate(hue_categories):
            group_data = all_data[(all_data["城市"] == city) & (all_data["朝向"] == direction)]
            if group_data.empty:
                continue

            mean_value = group_data["单位面积租金（元/月/㎡）"].mean()
            x_position = i + (j - len(hue_categories) / 2) * 0.15

            plt.text(x_position, mean_value, f"{mean_value:.2f}", ha="center", va="bottom", fontsize=8)

    # 调整布局以防止标签被截断
    plt.tight_layout()

    # 保存图表
    output_filename = os.path.join(output_dir, "direction_unit_box_chart.png")
    plt.savefig(output_filename, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"箱线图（已去除极大值）已成功保存到 {output_filename}")
