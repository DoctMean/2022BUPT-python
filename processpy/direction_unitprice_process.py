import os
import json
import pandas as pd


# 定义城市缩写到全称的映射
CITY_FULL_NAMES = {"bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"}

# 定义城市列表及对应的 JSON 文件名
CITIES = {
    "bj": "../data/bj_rent.json",
    "sh": "../data/sh_rent.json",
    "gz": "../data/gz_rent.json",
    "sz": "../data/sz_rent.json",
    "tj": "../data/tj_rent.json",
}

# 创建输出目录（如果不存在）
OUTPUT_DIR = "../processed_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 定义有效的朝向
VALID_DIRECTIONS = {"东", "南", "西", "北", "南北"}

# 加载 JSON 数据
def load_json(filename):
    """读取并解析 JSON 文件"""
    try:
        with open(filename, encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"无法读取文件 {filename}：{e}")
        return None

# 提取并计算单位面积租金
def extract_data_from_listing(listing):
    """从单个房源条目提取朝向、面积和租金信息"""
    info = listing.get("info", [])
    
    # 提取朝向
    direction = next((item for item in info if item in VALID_DIRECTIONS), "")
    if not direction:
        return None  # 如果没有有效的朝向，跳过此条数据

    # 提取面积
    area_str = next((item.replace("㎡", "").replace(",", "").strip() for item in info if "㎡" in item), "")
    if not area_str:
        return None  # 如果没有有效面积，跳过此条数据
    
    try:
        area = float(area_str)
        if area <= 0:
            return None
    except ValueError:
        return None  # 如果面积无效，跳过此条数据

    # 提取租金
    price_str = listing.get("price", "0元/月").replace("元/月", "").replace(",", "").strip()
    try:
        price = float(price_str)
        if price <= 0:
            return None
    except ValueError:
        return None  # 如果租金无效，跳过此条数据

    # 计算单位面积租金（元/月/㎡）
    unit_rent = price / area
    return {"朝向": direction, "单位面积租金（元/月/㎡）": unit_rent}

# 处理单个城市的数据
def process_city_data(city_code, filename):
    """处理指定城市的 JSON 文件并计算单位面积租金"""
    city_name = CITY_FULL_NAMES.get(city_code, city_code)

    # 加载 JSON 数据
    data = load_json(filename)
    if not data:
        print(f"{city_name} 城市数据加载失败，跳过该城市。")
        return

    # 提取有效记录
    records = [extract_data_from_listing(listing) for listing in data]
    records = [record for record in records if record]  # 过滤掉无效数据

    if not records:
        print(f"{city_name} 城市没有有效的数据。")
        return

    # 创建 DataFrame
    df_city = pd.DataFrame(records)

    # 保存数据到 CSV 文件
    output_filename = os.path.join(OUTPUT_DIR, f"{city_code}_direction_unit.csv")
    df_city.to_csv(output_filename, index=False, encoding="utf-8-sig")
    print(f"{city_name} 城市的朝向单位面积租金已成功保存到 {output_filename}")

# 主函数，遍历所有城市并处理数据
def main():
    for city_code, filename in CITIES.items():
        process_city_data(city_code, filename)

if __name__ == "__main__":
    main()
