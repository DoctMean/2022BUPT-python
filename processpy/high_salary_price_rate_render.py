import os
import matplotlib.pyplot as plt
import pandas as pd

# 定义城市缩写与全称的映射
city_full_names = {"bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"}

# 定义平均工资（单位：元）
salary_data = {"北京": 18193, "上海": 19111, "广州": 12873, "深圳": 14321, "天津": 13108}

# 创建输出目录（如果不存在）
output_dir = "../product"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 读取租金数据
price_data_file = "../processed_data/price_data.csv"

if not os.path.exists(price_data_file):
    print(f"文件 {price_data_file} 不存在，请确保文件路径正确。")
else:
    try:
        df = pd.read_csv(price_data_file, encoding="utf-8-sig")
    except Exception as e:
        print(f"读取文件 {price_data_file} 失败，错误：{e}")
        df = pd.DataFrame()

    if df.empty:
        print("租金数据为空，无法绘图。")
    else:
        # 过滤必要的列并映射城市名称
        df = df[["城市", "均值"]].copy()
        df["城市"] = df["城市"].map(city_full_names)

        # 添加平均工资数据
        df["平均工资（元）"] = df["城市"].map(salary_data)

        # 计算性价比指数（CPI）：租金 / 平均工资
        df["占比"] = df["均值"] / df["平均工资（元）"]

        # ------------------- 绘制条形图 -------------------
        # 计算 CPI 排序
        df_sorted = df.sort_values(by="占比", ascending=False)

        # 创建条形图
        fig, ax = plt.subplots(figsize=(10, 6))

        # 使用 Set2 调色板设置条形颜色
        colors = plt.cm.Set2.colors
        bar_colors = [colors[i % len(colors)] for i in range(df_sorted.shape[0])]

        # 绘制条形图
        bars = ax.barh(df_sorted["城市"], df_sorted["占比"], color=bar_colors, alpha=0.8)

        # 添加数据标注
        for bar, cpi in zip(bars, df_sorted["占比"]):
            width = bar.get_width()
            ax.annotate(
                f"{cpi:.2f}",
                xy=(width, bar.get_y() + bar.get_height() / 2),
                xytext=(5, 0),  # 向右偏移5点
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=10,
                color="black",
            )

        # 设置条形图的标题和标签
        ax.set_xlabel("占比", fontsize=12)
        ax.set_ylabel("城市", fontsize=12)
        ax.set_title("五个城市租金占平均工资比例", fontsize=14, fontweight="bold")

        # 添加注释说明
        fig.text(0.5, 0.02, "占比 = 租金 / 平均工资", ha="center", fontsize=12, bbox=dict(facecolor="white", alpha=0.5))

        # 保存图表
        pie_bar_chart_filename = os.path.join(output_dir, "high_salary_price_bar_chart.png")
        plt.tight_layout()
        plt.savefig(pie_bar_chart_filename, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"租金占工资比例的 CPI 条形图已成功保存到 {pie_bar_chart_filename}")
