import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.preprocessing import StandardScaler

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
    # 计算每个城市的单位面积租金平均值
    mean_rent = unit_price_data.groupby("城市")["单位面积租金（元/月/㎡）"].mean().reset_index()

    # 映射平均工资
    mean_rent["平均工资（元）"] = mean_rent["城市"].map(salary_data)

    # 计算性价比（CPI）：平均工资 / 单位面积租金
    mean_rent["性价比 (CPI)"] = mean_rent["平均工资（元）"] / mean_rent["单位面积租金（元/月/㎡）"]

    # 使用 StandardScaler 进行标准化
    scaler = StandardScaler()

    # 标准化单位面积租金、平均工资和CPI
    mean_rent[["单位面积租金（元/月/㎡）", "平均工资（元）", "性价比 (CPI)"]] = scaler.fit_transform(
        mean_rent[["单位面积租金（元/月/㎡）", "平均工资（元）", "性价比 (CPI)"]]
    )

    # 排序（可选）
    mean_rent_sorted = mean_rent.sort_values(by="性价比 (CPI)", ascending=False)

    # 设置绘图风格
    sns.set_theme(style="whitegrid")
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 适用于macOS和Windows
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

    # --------------------- 分组条形图 ---------------------
    plt.figure(figsize=(14, 10))

    # 控制条形的宽度
    bar_width = 0.25  
    x = range(len(mean_rent_sorted))

    # 绘制单位面积租金柱状图
    plt.bar(
        x,
        mean_rent_sorted["单位面积租金（元/月/㎡）"],
        width=bar_width,
        label="单位面积租金",
        color="skyblue",
        edgecolor="black",
        alpha=0.7,
    )

    # 绘制平均工资柱状图
    plt.bar(
        [i + bar_width for i in x],
        mean_rent_sorted["平均工资（元）"],
        width=bar_width,
        label="平均工资",
        color="lightgreen",
        edgecolor="black",
        alpha=0.7,
    )

    # 绘制CPI柱状图
    plt.bar(
        [i + 2 * bar_width for i in x],
        mean_rent_sorted["性价比 (CPI)"],
        width=bar_width,
        label="性价比 (CPI)",
        color="salmon",
        edgecolor="black",
        alpha=0.7,
    )

    # 添加图例和标签
    plt.xticks([i + bar_width for i in x], mean_rent_sorted["城市"], rotation=45, fontsize=12)
    plt.xlabel("城市", fontsize=14)
    plt.ylabel("标准化后的值", fontsize=14)
    plt.title("五个城市单位面积租金、平均工资与租房性价比 (CPI) 的对比", fontsize=16, fontweight="bold", pad=20)
    plt.legend(title="指标", fontsize=12)

    # 优化布局
    plt.tight_layout()

    # 保存分组条形图
    grouped_bar_chart_filename = os.path.join(output_dir, "salary_unit_price_bar_chart.png")
    plt.savefig(grouped_bar_chart_filename, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"标准化分组条形图已成功保存到 {grouped_bar_chart_filename}")
