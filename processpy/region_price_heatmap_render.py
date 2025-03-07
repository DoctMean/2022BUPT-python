import os
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import colors as mcolors

# 设置Matplotlib参数以支持中文显示
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 适用于macOS和Windows
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 定义城市列表及对应的文件名
cities = {
    "bj": {
        "csv": "../processed_data/bj_region_price_cleaned.csv",
        "geojson": "../data/bj.geojson",
        "name": "北京",
    },
    "sh": {
        "csv": "../processed_data/sh_region_price_cleaned.csv",
        "geojson": "../data/sh.geojson",
        "name": "上海",
    },
    "gz": {
        "csv": "../processed_data/gz_region_price_cleaned.csv",
        "geojson": "../data/gz.geojson",
        "name": "广州",
    },
    "sz": {
        "csv": "../processed_data/sz_region_price_cleaned.csv",
        "geojson": "../data/sz.geojson",
        "name": "深圳",
    },
    "tj": {
        "csv": "../processed_data/tj_region_price_cleaned.csv",
        "geojson": "../data/tj.geojson",
        "name": "天津",
    },
}

# 定义输出地图的目录
map_data_dir = "../product"
os.makedirs(map_data_dir, exist_ok=True)

# 新的亮度计算方式（使用一种简单的对比度判断）
def get_text_color_from_brightness(rgba_color):
    r, g, b, _ = rgba_color
    # 使用亮度对比度判断公式
    brightness = (0.299 * r + 0.587 * g + 0.114 * b)
    return "black" if brightness > 0.5 else "white"

# 颜色映射可以选择其他更合适的，例如 'viridis', 'plasma', 'coolwarm'
cmap = "coolwarm"

for city_key, city_info in cities.items():
    csv_file = city_info["csv"]
    geojson_file = city_info["geojson"]
    city_name = city_info["name"]

    # 检查文件是否存在
    if not os.path.exists(csv_file):
        print(f"CSV 文件 {csv_file} 不存在，跳过 {city_name}。")
        continue
    if not os.path.exists(geojson_file):
        print(f"GeoJSON 文件 {geojson_file} 不存在，跳过 {city_name}。")
        continue

    # 读取租金数据
    df = pd.read_csv(csv_file)

    # 读取 GeoJSON 数据
    gdf = gpd.read_file(geojson_file)

    # 确保区域名称匹配
    if "name" in gdf.columns:
        gdf = gdf.rename(columns={"name": "区域"})
    elif "NAME_1" in gdf.columns:
        gdf = gdf.rename(columns={"NAME_1": "区域"})

    # 预处理区域名称：去除空格并统一大小写（根据需要）
    df["区域"] = df["区域"].str.strip()
    gdf["区域"] = gdf["区域"].str.strip()

    # 合并数据
    merged = gdf.merge(df, on="区域")

    # 检查合并后的数据
    if merged.empty:
        print(f"{city_name} 的 GeoJSON 和 CSV 数据合并后为空，请检查区域名称是否匹配。")
        continue

    # 重新投影为投影坐标系（EPSG:3857）
    merged = merged.to_crs(epsg=3857)

    # 计算区域的中心点，用于标签定位
    merged["centroid"] = merged.geometry.centroid

    # 设置绘图风格
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))  # 增大图像尺寸

    # 定义颜色映射和规范化
    norm = mcolors.Normalize(vmin=merged["平均价格（元/月）"].min(), vmax=merged["平均价格（元/月）"].max())
    colormap = plt.get_cmap(cmap)

    # 绘制地图，按照 '平均价格（元/月）' 着色
    merged.plot(
        column="平均价格（元/月）",
        cmap=cmap,
        linewidth=0.8,
        ax=ax,
        edgecolor="0.8",
        legend=True,
        norm=norm,
        legend_kwds={
            "label": "平均价格（元/月）",
            "orientation": "horizontal",
            "shrink": 0.5,  # 缩小图例大小
            "pad": 0.05,  # 图例与图像的距离
        },
    )

    # 获取当前颜色图例（colorbar）并调整字体大小
    if ax.get_legend() is not None:
        colorbar = ax.get_legend()
        for text in colorbar.texts:
            text.set_fontsize(10)  # 设置图例字体大小

    # 添加区域名称和租金价格标签
    for _, row in merged.iterrows():
        centroid = row["centroid"]
        if pd.notnull(centroid):
            # 获取对应租金的颜色
            rent = row["平均价格（元/月）"]
            rgba_color = colormap(norm(rent))  # 获取对应的 RGBA 颜色
            text_color = get_text_color_from_brightness(rgba_color)  # 根据亮度计算文本颜色

            # 添加文本标签
            plt.text(
                centroid.x,
                centroid.y,
                f"{row['区域']}\n{row['平均价格（元/月）']:.0f}",
                horizontalalignment="center",
                fontsize=8,
                color=text_color,
                weight="bold",
            )

    # 添加城市名称标题
    ax.set_title(f"{city_name}各区域平均租金分布", fontsize=20)

    # 去除坐标轴
    ax.set_axis_off()

    # 优化布局
    plt.tight_layout()

    # 保存地图
    map_file = os.path.join(map_data_dir, f"{city_name}_region_heat_map.png")
    plt.savefig(map_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"{city_name} 的租金热力图已保存到 {map_file}")
