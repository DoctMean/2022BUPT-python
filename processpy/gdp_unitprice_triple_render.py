import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import gaussian_kde
from matplotlib.gridspec import GridSpec

# 定义城市缩写与全称的映射
city_full_names = {"bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"}

# 定义城市列表及对应的 CSV 文件路径
cities = {
    "bj": "../processed_data/bj_unit_price.csv",
    "sh": "../processed_data/sh_unit_price.csv",
    "gz": "../processed_data/gz_unit_price.csv",
    "sz": "../processed_data/sz_unit_price.csv",
    "tj": "../processed_data/tj_unit_price.csv",
}

# 定义人均 GDP 数据
gdp_data = {
    "北京": 200341, "上海": 190713, "广州": 162034, "深圳": 195939, "天津": 122797
}

# 为每个城市分配颜色
colors = sns.color_palette("Set2", n_colors=len(cities))
city_colors = {city_full_names[code]: colors[idx] for idx, code in enumerate(cities.keys())}

# 创建输出目录（如果不存在）
output_dir = "../product"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def load_and_filter_data(city_code, filename):
    """读取并过滤每个城市的数据"""
    try:
        df = pd.read_csv(filename, encoding="utf-8-sig")
        if df.empty:
            print(f"{city_full_names[city_code]} 数据为空，跳过。")
            return None
        # 计算均值和标准差，过滤掉超过均值 + 2 * 标准差的数据
        mean = df["单位面积租金（元/月/㎡）"].mean()
        std = df["单位面积租金（元/月/㎡）"].std()
        df_filtered = df[df["单位面积租金（元/月/㎡）"] <= (mean + 3 * std)].copy()
        if df_filtered.empty:
            print(f"{city_full_names[city_code]} 过滤后无有效数据，跳过。")
            return None
        # 添加城市列
        df_filtered["城市"] = city_full_names[city_code]
        return df_filtered[["城市", "单位面积租金（元/月/㎡）"]]
    except Exception as e:
        print(f"读取 {filename} 时发生错误：{e}")
        return None

# 加载所有城市的数据
unit_price_data = pd.concat(
    [load_and_filter_data(city_code, filename) for city_code, filename in cities.items() if load_and_filter_data(city_code, filename) is not None],
    ignore_index=True
)

# 检查数据是否为空
if unit_price_data.empty:
    print("所有城市的数据在过滤后均无有效记录，无法绘图。")
else:
    # 设置绘图风格
    sns.set_theme(style="whitegrid")
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 适用于 macOS 和 Windows
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

    # 使用 GridSpec 更灵活地创建子图
    fig = plt.figure(figsize=(14, 16))
    gs = GridSpec(3, 1, height_ratios=[1, 2, 3], hspace=0.4)

    # --------------- 子图1: GDP 柱状图 ---------------
    ax1 = fig.add_subplot(gs[0])

    # 准备GDP数据
    cities_order = list(gdp_data.keys())
    gdp_values = [gdp_data[city] for city in cities_order]

    # 绘制 GDP 柱状图（水平条形图）
    ax1.barh(cities_order, gdp_values, color=[city_colors[city] for city in cities_order], alpha=0.8)
    
    # 添加数据标注
    for i, (city, value) in enumerate(zip(cities_order, gdp_values)):
        ax1.text(value + 5000, i, f"{value}", va='center', fontsize=12, color='black')

    ax1.set_xlabel("人均 GDP（元）", fontsize=14)
    ax1.set_ylabel("城市", fontsize=14)
    ax1.set_title("五个城市人均 GDP", fontsize=16, fontweight="bold")

    # --------------- 子图2: 单位面积租金的箱形图 ---------------
    ax2 = fig.add_subplot(gs[1])

    # 绘制单位面积租金的箱形图
    rent_data = [unit_price_data[unit_price_data["城市"] == city]["单位面积租金（元/月/㎡）"] for city in cities_order]
    ax2.boxplot(rent_data, vert=False, patch_artist=True, 
                boxprops=dict(facecolor='lightblue', color='black'), 
                whiskerprops=dict(color='black', linewidth=1.5), 
                capprops=dict(color='black', linewidth=1.5))

    ax2.set_yticklabels(cities_order, fontsize=12)
    ax2.set_xlabel("单位面积租金（元/月/㎡）", fontsize=14)
    ax2.set_title("五个城市单位面积租金分布", fontsize=16, fontweight="bold")

    # --------------- 子图3: 单位面积租金分布曲线 ---------------
    ax3 = fig.add_subplot(gs[2])

    # 绘制单位面积租金的概率密度曲线
    for city in cities_order:
        data = unit_price_data[unit_price_data["城市"] == city]["单位面积租金（元/月/㎡）"]
        if data.empty:
            continue
        kde = gaussian_kde(data)
        x_min, x_max = data.min(), data.max()
        x_grid = np.linspace(x_min, x_max, 1000)
        density = kde(x_grid)
        ax3.plot(x_grid, density, label=city, color=city_colors[city], linewidth=3, alpha=0.8)

    ax3.set_xlabel("单位面积租金（元/月/㎡）", fontsize=14)
    ax3.set_ylabel("概率密度", fontsize=14)
    ax3.set_title("单位面积租金的概率密度分布", fontsize=16, fontweight="bold")
    ax3.legend(title="城市", fontsize=10, title_fontsize=12)

    # 保存图表
    bar_chart_filename = os.path.join(output_dir, "gdp_unit_price_chart.png")
    plt.savefig(bar_chart_filename, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"图表已成功保存到 {bar_chart_filename}")
