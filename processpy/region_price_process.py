import json
import os
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

def load_json_data(file_path):
    """加载并解析 JSON 数据"""
    try:
        with open(file_path, encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"加载文件 {file_path} 失败: {e}")
        return None

def extract_rent_data(data):
    """从 JSON 数据中提取区域和价格信息"""
    records = []
    for listing in data:
        info = listing.get("info", [])
        if len(info) < 1:
            continue
        
        district = info[0].strip()
        
        # 过滤掉包含数字的区域名称
        if any(char.isdigit() for char in district):
            continue

        price_str = listing.get("price", "0元/月").replace("元/月", "").replace(",", "").strip()
        try:
            price = float(price_str)
        except ValueError:
            price = None
        
        if price and price > 0:
            records.append({"区域": district, "价格（元/月）": price})
    return records

def process_city_data(city_code, data):
    """处理城市的租金数据"""
    records = extract_rent_data(data)
    if not records:
        print(f"{city_code} 城市没有有效的数据。")
        return None
    
    df_city = pd.DataFrame(records)
    
    # 计算每个区域的平均价格
    df_avg = df_city.groupby("区域")["价格（元/月）"].mean().reset_index()
    df_avg.rename(columns={"价格（元/月）": "平均价格（元/月）"}, inplace=True)
    
    return df_avg

def save_city_data(city_code, df_avg):
    """保存处理后的城市数据到 CSV"""
    if df_avg is not None:
        output_filename = os.path.join(output_dir, f"{city_code}_region_price.csv")
        df_avg.to_csv(output_filename, index=False, encoding="utf-8-sig")
        print(f"{city_code} 城市的区域平均租金已成功保存到 {output_filename}")

def main():
    """主函数，遍历每个城市处理数据并保存"""
    for city_code, filename in cities.items():
        print(f"正在处理 {city_full_names.get(city_code, city_code)} 城市的数据...")
        
        data = load_json_data(filename)
        if data is None:
            continue
        
        df_avg = process_city_data(city_code, data)
        save_city_data(city_code, df_avg)

if __name__ == "__main__":
    main()
