import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# 定义城市缩写与全称的映射
city_full_names = {"bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"}

# 定义城市列表及对应的 CSV 文件名
cities = {
    "bj": "../processed_data/bj_unit_price.csv",
    "sh": "../processed_data/sh_unit_price.csv",
    "gz": "../processed_data/gz_unit_price.csv",
    "sz": "../processed_data/sz_unit_price.csv",
    "tj": "../processed_data/tj_unit_price.csv",
}

# 定义平均工资（单位：元）
salary_data = {"北京": 11982, "上海": 12183, "广州": 8206, "深圳": 9129, "天津": 8356}

# 定义颜色列表（选择美观的调色板）
colors = sns.color_palette("Set2", n_colors=len(cities))  # 为每个城市分配不同颜色
city_colors = {city_full_names[code]: colors[idx] for idx, code in enumerate(cities.keys())}

# 创建输出目录（如果不存在）
output_dir = "../product"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 初始化 unit_price_data 为 None
unit_price_data = None

# 遍历每个城市的 CSV 文件并读取数据
for city_code, filename in cities.items():
    city_name = city_full_names.get(city_code, city_code)

    if not os.path.exists(filename):
        print(f"文件 {filename} 不存在，跳过 {city_name} 城市。")
        continue

    try:
        df = pd.read_csv(filename, encoding="utf-8-sig")
    except Exception as e:
        print(f"读取文件 {filename} 失败，错误：{e}")
        continue

    if df.empty:
        print(f"{city_name} 城市的数据为空，跳过。")
        continue

    # 计算均值和标准差
    mean = df["单位面积租金（元/月/㎡）"].mean()
    std = df["单位面积租金（元/月/㎡）"].std()

    # 过滤掉超过均值 + 3*标准差的数据，并创建副本
    df_filtered = df[df["单位面积租金（元/月/㎡）"] <= (mean + 3 * std)].copy()

    if df_filtered.empty:
        print(f"{city_name} 城市在过滤后没有有效的数据。")
        continue

    # 添加城市名称，使用 .loc 避免 SettingWithCopyWarning
    df_filtered.loc[:, "城市"] = city_name

    # 确保 DataFrame 只有 ['城市', '单位面积租金（元/月/㎡）'] 两列
    df_filtered = df_filtered[["城市", "单位面积租金（元/月/㎡）"]]

    # 合并数据
    if unit_price_data is None:
        unit_price_data = df_filtered
    else:
        unit_price_data = pd.concat([unit_price_data, df_filtered], ignore_index=True)

# 检查是否有数据可绘图
if unit_price_data is None or unit_price_data.empty:
    print("所有城市的数据在过滤后均无有效记录，无法绘图。")
else:
    # 设置绘图风格
    sns.set_theme(style="whitegrid")
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 适用于macOS和Windows
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

    # 创建子图：绘制平均工资条形图
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # 准备平均工资数据
    cities_order = list(salary_data.keys())
    salary_values = [salary_data[city] for city in cities_order]

    # 绘制条形图
    bars = ax1.barh(
        cities_order,
        salary_values,
        color=[city_colors[city] for city in cities_order],
        alpha=0.8,
        label="平均工资（元）",
    )

    # 添加数据标注
    for bar in bars:
        width = bar.get_width()
        ax1.annotate(
            f"{width}",
            xy=(width + 200, bar.get_y() + bar.get_height() / 2),
            xytext=(0, 0),  # 不需要偏移
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=12,
            color="black",
        )

    ax1.set_xlabel("平均工资（元）", fontsize=14)
    ax1.set_ylabel("城市", fontsize=14)
    ax1.set_title("五个城市平均工资", fontsize=16, fontweight="bold", pad=20)

    # 调整布局
    plt.tight_layout()

    # 保存图表
    bar_chart_filename = os.path.join(output_dir, "salary_unit_price_chart.png")
    plt.savefig(bar_chart_filename, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"图表已成功保存到 {bar_chart_filename}")
