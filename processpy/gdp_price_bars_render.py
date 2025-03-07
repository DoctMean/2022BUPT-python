import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.preprocessing import StandardScaler

# 定义城市缩写与全称的映射
city_full_names = {"bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"}

# 定义人均 GDP（单位：元）
gdp_data = {"北京": 200278, "上海": 190321, "广州": 161634, "深圳": 195231, "天津": 84342}

# 读取价格数据
price_data_file = "../processed_data/price_data.csv"
if not os.path.exists(price_data_file):
    print(f"文件 {price_data_file} 不存在。")
    exit()

try:
    price_df = pd.read_csv(price_data_file, encoding="utf-8-sig")
except Exception as e:
    print(f"读取文件 {price_data_file} 失败，错误：{e}")
    exit()

if price_df.empty:
    print("价格数据文件为空，无法绘图。")
    exit()

# 映射城市缩写到全称
price_df["城市全称"] = price_df["城市"].map(city_full_names)

# 检查是否有未映射的城市
if price_df["城市全称"].isnull().any():
    missing_cities = price_df[price_df["城市全称"].isnull()]["城市"].unique()
    print(f"未找到以下城市的全称映射: {missing_cities}")
    exit()

# 提取必要的列并重命名
price_df = price_df[["城市全称", "均值"]].rename(columns={"城市全称": "城市"})

# 计算 CPI
price_df["人均 GDP（元）"] = price_df["城市"].map(gdp_data)

# 检查是否有 NaN 的人均 GDP
if price_df["人均 GDP（元）"].isnull().any():
    missing_gdp_cities = price_df[price_df["人均 GDP（元）"].isnull()]["城市"].unique()
    print(f"未找到以下城市的人均 GDP 数据: {missing_gdp_cities}")
    exit()

price_df["CPI"] = price_df["人均 GDP（元）"] / price_df["均值"]

# 检查 CPI 是否有无穷大或 NaN
if price_df["CPI"].replace([float("inf"), -float("inf")], pd.NA).dropna().shape[0] != price_df.shape[0]:
    print("CPI 计算结果包含无穷大或 NaN，请检查数据。")
    exit()

# 排序 CPI 从大到小
price_df_sorted = price_df.sort_values(by="CPI", ascending=False).reset_index(drop=True)

# 标准化数据（对每个指标进行标准化，使得数值尺度相同）
scaler = StandardScaler()
price_df_sorted[["均值", "人均 GDP（元）", "CPI"]] = scaler.fit_transform(
    price_df_sorted[["均值", "人均 GDP（元）", "CPI"]]
)

# 定义颜色列表（选择美观的调色板）
colors = sns.color_palette("Set2", n_colors=3)

# 创建输出目录（如果不存在）
output_dir = "../product"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 设置绘图风格
sns.set_theme(style="whitegrid")
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 适用于macOS和Windows
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# --------------------- 分组条形图 ---------------------
plt.figure(figsize=(14, 10))

# 绘制均值、人均GDP、CPI的并排条形图
bar_width = 0.25  # 控制条形的宽度
x = range(len(price_df_sorted))

# 绘制均值柱状图
plt.bar(
    x,
    price_df_sorted["均值"],
    width=bar_width,
    label="均值",
    color=colors[0],
    edgecolor="black",
    alpha=0.7,
)

# 绘制人均GDP柱状图
plt.bar(
    [i + bar_width for i in x],
    price_df_sorted["人均 GDP（元）"],
    width=bar_width,
    label="人均 GDP（元）",
    color=colors[1],
    edgecolor="black",
    alpha=0.7,
)

# 绘制CPI柱状图
plt.bar(
    [i + 2 * bar_width for i in x],
    price_df_sorted["CPI"],
    width=bar_width,
    label="性价比 (CPI)",
    color=colors[2],
    edgecolor="black",
    alpha=0.7,
)

# 添加图例和标签
plt.xticks([i + bar_width for i in x], price_df_sorted["城市"], rotation=45, fontsize=12)
plt.xlabel("城市", fontsize=14)
plt.ylabel("标准化后的值", fontsize=14)
plt.title("五个城市均值、人均GDP与租房性价比 (CPI) 的对比", fontsize=16, fontweight="bold", pad=20)
plt.legend(title="指标", fontsize=12)

# 优化布局
plt.tight_layout()

# 保存图表
grouped_bar_chart_filename = os.path.join(output_dir, "gdp_price_grouped_bar_chart.png")
plt.savefig(grouped_bar_chart_filename, dpi=300, bbox_inches="tight")
plt.close()

print(f"标准化分组条形图已成功保存到 {grouped_bar_chart_filename}")
