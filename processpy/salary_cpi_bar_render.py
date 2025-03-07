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

# 自定义颜色列表（可以根据需要调整或选择更有辨识度的颜色）
city_colors = {
    "北京": "skyblue",  # 设置北京为浅蓝色
    "上海": "lightgreen",  # 设置上海为浅绿色
    "广州": "salmon",  # 设置广州为鲑鱼色
    "深圳": "lightcoral",  # 设置深圳为浅珊瑚色
    "天津": "gold"  # 设置天津为金色
}

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

    # 过滤掉超过均值 + 2*标准差的数据，并创建副本
    df_filtered = df[df["单位面积租金（元/月/㎡）"] <= (mean + 2 * std)].copy()

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
    # 计算每个城市的单位面积租金平均值
    mean_rent = unit_price_data.groupby("城市")["单位面积租金（元/月/㎡）"].mean().reset_index()

    # 映射平均工资
    mean_rent["平均工资（元）"] = mean_rent["城市"].map(salary_data)

    # 计算性价比（CPI）：平均工资 / 单位面积租金
    mean_rent["性价比 (CPI)"] = mean_rent["平均工资（元）"] / mean_rent["单位面积租金（元/月/㎡）"]

    # 按 CPI 排序
    mean_rent_sorted = mean_rent.sort_values(by="性价比 (CPI)", ascending=False)

    # 设置绘图风格
    sns.set_theme(style="whitegrid")
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 适用于macOS和Windows
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

    # 创建柱状图，指定 hue='城市' 并移除图例中的 CPI
    plt.figure(figsize=(14, 10))
    ax = sns.barplot(
        x="城市",
        y="性价比 (CPI)",
        data=mean_rent_sorted,
        hue="城市",  # 指定 hue
        palette=city_colors,  # 使用字典形式的 palette
        alpha=0.8,
        legend=False,  # 移除图例中的 CPI
    )

    # 设置标题和标签
    plt.xlabel("城市", fontsize=14)
    plt.ylabel("性价比 (CPI)", fontsize=14)
    plt.title("五个城市租房性价比 (CPI)", fontsize=16, fontweight="bold", pad=20)

    # 添加注释说明
    plt.text(
        0.95,
        0.95,
        "",
        horizontalalignment="right",
        verticalalignment="top",
        transform=plt.gca().transAxes,
        fontsize=12,
        bbox=dict(facecolor="white", alpha=0.5),
    )

    # 获取所有柱子的对象
    bars = ax.patches

    # 遍历每个柱子并添加标注
    for bar, row in zip(bars, mean_rent_sorted.itertuples()):
        # 获取柱子的中心x位置和顶部y位置
        x = bar.get_x() + bar.get_width() / 2
        y = bar.get_height()

        # 定义标注文本
        annotation = (
            f"CPI: {row._4:.2f}\n"  # row._4 是 '性价比 (CPI)'
            f"工资: {row._3:,}\n"  # row._3 是 '平均工资（元）'
            f"租金: {row._2:.1f}"  # row._2 是 '单位面积租金（元/月/㎡）'
        )

        # 添加标注
        ax.text(
            x,
            y + 0.03 * mean_rent_sorted["性价比 (CPI)"].max(),  # 根据最大CPI值动态调整y位置
            annotation,
            color="black",
            ha="center",
            va="bottom",
            fontsize=10,
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", boxstyle="round,pad=0.3"),
        )

    # 优化布局
    plt.tight_layout()

    # 保存图表
    salary_cpi_chart_filename = os.path.join(output_dir, "salary_cpi_bar_chart.png")
    plt.savefig(salary_cpi_chart_filename, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"租房性价比图表已成功保存到 {salary_cpi_chart_filename}")
