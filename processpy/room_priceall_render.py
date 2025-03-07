import os
import pandas as pd
import numpy as np
from pyecharts.charts import Bar3D
from pyecharts import options as opts
from pyecharts.globals import ThemeType

# 定义城市缩写与全称的映射（如果需要）
city_mapping = {"bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"}

# 定义输入文件路径
renting_filepath = "../processed_data/renting.csv"  # 请确保此路径正确

# 检查文件是否存在
if not os.path.exists(renting_filepath):
    print(f"文件 {renting_filepath} 不存在，请检查路径是否正确。")
    exit(1)

# 读取 renting.csv 文件
renting_df = pd.read_csv(renting_filepath)

# 确认 '城市' 列存在
if "城市" not in renting_df.columns:
    print("renting.csv 文件中缺少 '城市' 列。")
    exit(1)

# 定义需要分析的统计函数，使用 'mean' 代替 'average'
func = ['min', 'median', 'mean', 'max']

# 分析每个城市和房型的租金统计信息
def analyze_room(city):
    df = renting_df[renting_df['城市'] == city]
    stats = {}
    for room_type in ['一居', '二居', '三居', '四居及以上']:
        df_room = df[df['房屋类型'] == room_type]
        if df_room.empty:
            stats[room_type] = {'min': 0, 'median': 0, 'average': 0, 'max': 0}
            continue
        agg_stats = df_room['价格（元/月）'].agg(func).to_dict()
        stats[room_type] = {
            'min': int(agg_stats.get('min', 0)),
            'median': int(agg_stats.get('median', 0)),
            'average': int(agg_stats.get('mean', 0)),
            'max': int(agg_stats.get('max', 0))
        }
    return stats

# 获取所有城市
cities = renting_df['城市'].unique()

# 分析所有城市的数据
origin = {}
for city in cities:
    origin[city] = analyze_room(city)

# 准备绘图数据
data = []
for i, city in enumerate(cities):
    for room_type in ['一居', '二居', '三居', '四居及以上']:
        stats = origin[city].get(room_type, {'min':0, 'median':0, 'average':0, 'max':0})
        # 计算 x 轴位置
        if room_type == '四居及以上':
            x_pos = (4 - 1) * 5 + i  # (4居及以上 -1)*5 + city_index = 15 + i
        else:
            room_num = {'一居':1, '二居':2, '三居':3}.get(room_type, 1)
            x_pos = (room_num - 1) * 5 + i
        # 添加数据点
        data.append([x_pos, 0, stats['min']])
        data.append([x_pos, 1, stats['median']])
        data.append([x_pos, 2, stats['average']])
        data.append([x_pos, 3, int(stats['max']/10) if stats['max'] > 0 else 0])

# 准备标签
label = []
for room_type in ['一居', '二居', '三居', '四居及以上']:
    for city in cities:
        label.append(f"{city}\n{room_type}")

# 定义 y 轴数据类型
y_labels = ['最小值(元)', '中位数(元)', '平均值(元)', '最大值(十元)']

# 定义颜色调色板
color_palette = [
    "#313695","#4575B4","#74ADD1","#ABD9E9","#E0F3F8",
    "#FFFFbF","#FEE090","#FDAE61","#F46D43","#D73027",
]

# 绘制3D柱状图
def plot_room_citys(data, label, y_labels, title, filename, colors):
    b = Bar3D(init_opts=opts.InitOpts(
        width='2500px',
        height='1250px',
        theme=ThemeType.CHALK,
        bg_color='white'  # 设置背景颜色为白色
    ))
    b.add(
        series_name='月租金',
        data=data,
        xaxis3d_opts=opts.Axis3DOpts(
            name='城市及户型',
            type_='category',
            data=label,
            textstyle_opts=opts.TextStyleOpts(font_weight='bold', font_size=12)
        ),
        yaxis3d_opts=opts.Axis3DOpts(
            name='数据类型',
            type_='category',
            data=y_labels,
            textstyle_opts=opts.TextStyleOpts(font_weight='bold', font_size=13)
        ),
        zaxis3d_opts=opts.Axis3DOpts(
            name='月租金',
            type_='value',
            textstyle_opts=opts.TextStyleOpts(font_weight='bold', font_size=13)
        )
    )
    b.set_global_opts(
        visualmap_opts=opts.VisualMapOpts(
            max_=50000,
            range_color=colors,
            is_piecewise=True,
            dimension=2
        ),
        title_opts=opts.TitleOpts(
            title=title,
            pos_left="center",
            pos_top="5%",
            title_textstyle_opts=opts.TextStyleOpts(font_size=24, font_weight="bold")
        ),
        legend_opts=opts.LegendOpts(
            is_show=True,
            pos_left="left",
            pos_top="10%",
            orient="vertical"
        )
    )
    b.render(filename)
    print(f"3D柱状图已成功保存到 {filename}")

# 绘制3D柱状图
plot_room_citys(
    data=data,
    label=label,
    y_labels=y_labels,
    title='各城市不同户型月租金数据分布',
    filename='../product/room.html',
    colors=color_palette
)
