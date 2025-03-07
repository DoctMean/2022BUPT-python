import json
import os
import re

import pandas as pd

# 定义城市列表及对应的文件名
cities = {
    "bj": "../data/bj_rent.json",
    "sh": "../data/sh_rent.json",
    "gz": "../data/gz_rent.json",
    "sz": "../data/sz_rent.json",
    "tj": "../data/tj_rent.json",
}

# 定义城市缩写到全称的映射
city_full_names = {"bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"}

# 初始化一个列表用于存储所有有效的数据
all_rent_data = []

# 遍历每个城市的 JSON 文件
for city, filename in cities.items():
    if not os.path.exists(filename):
        print(f"文件 {filename} 不存在，跳过 {city_full_names.get(city, city)} 城市。")
        continue

    with open(filename, encoding="utf-8") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            print(f"文件 {filename} 解析失败，跳过 {city_full_names.get(city, city)} 城市。")
            continue

    for listing in data:
        # 提取租金
        price_str = listing.get("price", "0元/月")
        try:
            price = float(price_str.replace("元/月", "").replace(",", "").strip())
        except ValueError:
            price = 0.0

        if price <= 0:  # 跳过价格为 0 或负值的数据
            continue

        # 提取房屋类型
        info = listing.get("info", [])

        room_type = ""
        for item in info:
            match = re.match(r"(\d+)室", item)
            if match:
                num = int(match.group(1))
                # 根据房间数量分类
                if num == 1:
                    room_type = "一居"
                elif num == 2:
                    room_type = "二居"
                elif num == 3:
                    room_type = "三居"
                else:
                    room_type = "四居及以上"
                break  # 找到后停止

        if not room_type:
            room_type = "未知"  # 无法识别的房屋类型

        # 记录有效的数据
        all_rent_data.append(
            {
                "城市": city_full_names.get(city, city),
                "房屋类型": room_type,
                "价格（元/月）": price,
            }
        )

# 如果没有有效的数据，退出程序
if not all_rent_data:
    print("没有有效的租金数据可供处理。")
    exit(1)

# 创建 DataFrame
renting_df = pd.DataFrame(all_rent_data)

# 导出为 renting.csv
output_dir = "../processed_data"  # 确保此目录存在或创建
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

renting_csv_path = os.path.join(output_dir, "renting.csv")
renting_df.to_csv(renting_csv_path, index=False, encoding="utf-8-sig")
print(f"renting.csv 已成功保存到 {renting_csv_path}")
