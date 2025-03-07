import os
import json
import pandas as pd

# 定义城市缩写到全称的映射
city_full_names = {
    "bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "tj": "天津"
}

# 定义城市列表及对应的 JSON 文件名
cities = {
    "bj": "../data/bj_rent.json",
    "sh": "../data/sh_rent.json",
    "gz": "../data/gz_rent.json",
    "sz": "../data/sz_rent.json",
    "tj": "../data/tj_rent.json",
}

# 创建输出目录（如果不存在）
output_dir = "../processed_data"
os.makedirs(output_dir, exist_ok=True)

def load_json_data(filename):
    """加载JSON文件并返回数据，如果文件无效则返回None"""
    if not os.path.exists(filename):
        print(f"文件 {filename} 不存在。")
        return None
    
    try:
        with open(filename, encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        print(f"文件 {filename} 解析失败。")
        return None

def process_city_data(city_code, data):
    """处理城市数据，提取有效的板块和租金信息"""
    records = []
    for listing in data:
        info = listing.get("info", [])
        if len(info) < 2:
            continue
        
        district = info[1].strip()   # info对应第二元素即为板块信息

        # 过滤：板块名称含有数字，跳过该记录
        if any(char.isdigit() for char in district):
            continue
        
        price_str = listing.get("price", "0元/月").replace("元/月", "").replace(",", "").strip()
        try:
            price = float(price_str)
        except ValueError:
            price = None

        if price and price > 0:
            records.append({"板块": district, "价格（元/月）": price})
    
    return records

def save_to_csv(df, city_code):
    """保存DataFrame到CSV文件"""
    output_filename = os.path.join(output_dir, f"{city_code}_block_price.csv")
    df.to_csv(output_filename, index=False, encoding="utf-8-sig")
    print(f"{city_code} 城市的板块平均租金已成功保存到 {output_filename}")

def compute_average_price(df_city):
    """计算每个板块的平均价格并返回DataFrame"""
    df_avg = df_city.groupby("板块")["价格（元/月）"].mean().reset_index()
    df_avg.rename(columns={"价格（元/月）": "平均价格（元/月）"}, inplace=True)
    return df_avg

def process_and_save_city(city_code, filename):
    """处理城市的JSON文件并保存结果"""
    data = load_json_data(filename)
    if not data:
        return

    # 提取有效的板块和价格数据
    records = process_city_data(city_code, data)
    if not records:
        print(f"{city_code} 城市没有有效的数据。")
        return

    # 创建DataFrame并计算平均价格
    df_city = pd.DataFrame(records)
    df_avg = compute_average_price(df_city)

    # 保存结果到CSV
    save_to_csv(df_avg, city_code)

def main():
    """主函数，遍历所有城市并处理"""
    for city_code, filename in cities.items():
        process_and_save_city(city_code, filename)

if __name__ == "__main__":
    main()
