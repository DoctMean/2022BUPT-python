import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# 定义城市缩写到全称的映射
city_full_names = {
    "bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"
}

# 定义城市列表及对应的 CSV 文件名
cities = {
    "bj": "../processed_data/bj_block_price.csv",
    "sh": "../processed_data/sh_block_price.csv",
    "gz": "../processed_data/gz_block_price.csv",
    "sz": "../processed_data/sz_block_price.csv",
    "tj": "../processed_data/tj_block_price.csv",
}

# 创建输出目录（如果不存在）
output_dir = "../product"
os.makedirs(output_dir, exist_ok=True)

# 设置绘图风格
sns.set_theme(style="darkgrid", palette="coolwarm")

def load_and_clean_data(csv_path):
    """加载CSV文件并进行数据清理"""
    if not os.path.exists(csv_path):
        print(f"文件 {csv_path} 不存在，跳过。")
        return None

    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except Exception as e:
        print(f"读取文件 {csv_path} 失败，错误：{e}")
        return None

    # 检查必要的列
    if "板块" not in df.columns or "平均价格（元/月）" not in df.columns:
        print(f"文件 {csv_path} 缺少必要的列。")
        return None

    # 删除缺失值
    df = df.dropna(subset=["板块", "平均价格（元/月）"])
    return df

def plot_bar_chart(df, city_name, city_code):
    """绘制条形图并保存"""
    # 按平均价格从低到高排序
    df_sorted = df.sort_values(by="平均价格（元/月）", ascending=True)

    # 设置图形大小
    plt.figure(figsize=(12, 8))
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 设置中文字体
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

    # 绘制条形图
    bar_plot = sns.barplot(data=df_sorted, x="板块", y="平均价格（元/月）", hue="板块", palette="coolwarm", legend=False)

    # 设置标题和标签
    plt.title(f"{city_name}各板块平均租金对比", fontsize=18, fontweight="bold")
    plt.xlabel("板块", fontsize=14)
    plt.ylabel("平均租金（元/月）", fontsize=14)

    # 旋转 x 轴标签以避免重叠
    plt.xticks(rotation=45, ha="right", fontsize=10)
    plt.yticks(fontsize=12)

    # 调整布局以防止标签被截断
    plt.tight_layout()

    # 保存图表
    output_filename = os.path.join(output_dir, f"{city_name}_block_price_bar_chart.png")
    plt.savefig(output_filename, dpi=1200, bbox_inches="tight")
    plt.close()
    print(f"{city_name} 城市的条形图已成功保存到 {output_filename}")

def process_and_plot_city_data(city_code, csv_path):
    """处理和绘制城市数据"""
    city_name = city_full_names.get(city_code, city_code)

    df = load_and_clean_data(csv_path)
    if df is None:
        return

    plot_bar_chart(df, city_name, city_code)

def main():
    """主函数，遍历所有城市并绘制条形图"""
    for city_code, csv_path in cities.items():
        process_and_plot_city_data(city_code, csv_path)

if __name__ == "__main__":
    main()
