import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
from scipy.stats import zscore

# 定义城市缩写与全称的映射
city_mapping = {"bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"}

# 定义输入文件路径
price_stats_filepath = "../processed_data/price_data.csv"
unit_price_stats_filepath = "../processed_data/unit_price_data.csv"

# 检查文件是否存在
def check_file_exists(filepath):
    if not os.path.exists(filepath):
        print(f"文件 {filepath} 不存在，请检查路径是否正确。")
        exit(1)

check_file_exists(price_stats_filepath)
check_file_exists(unit_price_stats_filepath)

# 读取 CSV 文件
price_df = pd.read_csv(price_stats_filepath)
unit_price_df = pd.read_csv(unit_price_stats_filepath)

# 将城市缩写替换为全称
price_df["城市"] = price_df["城市"].map(city_mapping)
unit_price_df["城市"] = unit_price_df["城市"].map(city_mapping)

# 设置 '城市' 为索引
price_df.set_index("城市", inplace=True)
unit_price_df.set_index("城市", inplace=True)

# 定义需要可视化的统计指标
price_metrics = [
    "均值", "中位数", "25%分位数", "75%分位数", "标准差", "最高值", "最低值",
]

unit_price_metrics = [
    "均值", "中位数", "25%分位数", "75%分位数", "标准差", "最高值", "最低值",
]

# 将数据转为长格式以适应seaborn绘图需求
def prepare_long_format(df, metrics, value_name):
    return (
        df[metrics]
        .reset_index()
        .melt(id_vars="城市", value_vars=metrics, var_name="统计指标", value_name=value_name)
    )

price_long = prepare_long_format(price_df, price_metrics, "金额（元/月）")
unit_price_long = prepare_long_format(unit_price_df, unit_price_metrics, "金额（元/㎡）")

# 设置绘图风格
sns.set_theme(style="whitegrid")
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 设置中文字体
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 定义更美观的调色板
common_palette = sns.color_palette("coolwarm", n_colors=max(len(price_metrics), len(unit_price_metrics)))

# 创建输出目录（如果不存在）
output_dir = "../product"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 绘制柱状图的公共函数
def plot_bar_chart(data, x, y, hue, title, ylabel, filename, palette):
    plt.figure(figsize=(22, 14))  # 增加图表尺寸，增强可读性
    barplot = sns.barplot(data=data, x=x, y=y, hue=hue, palette=palette, dodge=True)
    
    # 添加数据标签，去除小数，仅显示整数，并防止重叠
    for p in barplot.patches:
        height = p.get_height()
        label = f"{int(height)}" if height > 0 else f"{height:.2f}"
        barplot.annotate(
            label,
            (p.get_x() + p.get_width() / 2.0, height),
            ha="center",
            va="bottom",
            fontsize=12,
            color="black",
            xytext=(0, 3),  # 稍微上移
            textcoords="offset points",
        )

    # 设置标题和标签，字体加粗，调整字体大小
    plt.title(title, fontsize=24, fontweight="bold", pad=20)
    plt.xlabel("城市", fontsize=16)
    plt.ylabel(ylabel, fontsize=16)
    plt.xticks(fontsize=14, rotation=45)  # 旋转X轴标签，避免重叠
    plt.yticks(fontsize=14)

    # 设置图例位置和样式
    handles, labels = barplot.get_legend_handles_labels()
    plt.legend(handles=handles, labels=labels, title="统计指标", fontsize=14, title_fontsize=16, loc="upper right", bbox_to_anchor=(1, 1))

    # 添加网格线
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)

    # 保存图表
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    print(f"{title} 已成功保存到 {filename}")


# 绘制租金统计柱状图
price_output_filename = os.path.join(output_dir, "priceall_bar_chart.png")
plot_bar_chart(
    data=price_long,
    x="城市",
    y="金额（元/月）",
    hue="统计指标",
    title="五个城市租金统计信息对比（单位：元/月）",
    ylabel="金额（元/月）",
    filename=price_output_filename,
    palette=common_palette,
)

# 绘制单位面积租金统计柱状图
unit_price_output_filename = os.path.join(output_dir, "unit_price_bar_chart.png")
plot_bar_chart(
    data=unit_price_long,
    x="城市",
    y="金额（元/㎡）",
    hue="统计指标",
    title="五个城市单位面积租金统计信息对比（单位：元/㎡）",
    ylabel="金额（元/㎡）",
    filename=unit_price_output_filename,
    palette=common_palette,
)


# 定义雷达图绘制函数
def plot_radar_chart(df, metrics, title, filename, colors):
    """
    绘制雷达图并保存，包含具体数据标签。

    参数：
    - df: DataFrame，包含城市为索引和需要绘制的指标列。
    - metrics: List[str]，需要绘制的指标名称。
    - title: str，图表标题。
    - filename: str，保存的文件路径。
    - colors: List[str]，城市对应的颜色列表。
    """
    # 数据标准化（Z-score）
    normalized_data = df[metrics].apply(zscore)

    # 获取指标名称
    categories = list(metrics)
    N = len(categories)

    # 计算角度
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # 完成环形

    # 初始化图形
    plt.figure(figsize=(10, 10))
    ax = plt.subplot(111, polar=True)

    # 设置起始角度和方向
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # 设置类别标签
    plt.xticks(angles[:-1], categories, color="grey", size=12)

    # 设置 y 轴刻度
    ax.set_rlabel_position(0)
    plt.yticks([-2, -1, 0, 1, 2], ["-2", "-1", "0", "1", "2"], color="grey", size=10)
    plt.ylim(-2, 2)

    # 绘制每个城市的数据
    for idx, (city, row) in enumerate(normalized_data.iterrows()):
        values = row.tolist()
        values += values[:1]  # 完成环形
        ax.plot(angles, values, linewidth=2, linestyle="solid", label=city, color=colors[idx % len(colors)])
        ax.fill(angles, values, alpha=0.25, color=colors[idx % len(colors)])

    # 添加图例
    plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=12)

    # 添加标题
    plt.title(title, size=20, y=1.1, fontweight="bold")

    # 保存图表
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"雷达图已成功保存到 {filename}")


# 定义颜色列表（为每个城市分配不同颜色）
colors = ["b", "g", "r", "c", "m"]  # 可以根据需要扩展

# 绘制租金统计雷达图
plot_radar_chart(
    df=price_df,
    metrics=price_metrics,
    title="五个城市租金统计信息雷达图对比",
    filename=os.path.join(output_dir, "priceall_radar_chart.png"),
    colors=colors,
)

# 绘制单位面积租金统计雷达图
plot_radar_chart(
    df=unit_price_df,
    metrics=unit_price_metrics,
    title="五个城市单位面积租金统计信息雷达图对比",
    filename=os.path.join(output_dir, "unit_price_radar_chart.png"),
    colors=colors,
)
