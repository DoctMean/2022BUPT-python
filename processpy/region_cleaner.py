import pandas as pd
import os

def clean_data(df, city_name):
    """
    清理数据：
    - 根据城市名称删除指定的区域
    - 对区域名称进行适当的修改
    - 在区域名称后添加 '区'
    """
    # 根据不同城市的需求，删除特定的区域
    if city_name == "bj":
        df = df[df["区域"] != "亦庄开发区"]
        df = df[df["区域"] != "北京经济技术开发区"]
        df = df[df["区域"] != "精选"]
        df["区域"] = df["区域"] + "区"
    elif city_name == "gz":
        df = df[df["区域"] != "精选"]
        df = df[df["区域"] != "南海"]
        df["区域"] = df["区域"] + "区"
    elif city_name == "sh":
        df = df[df["区域"] != "精选"]
        df["区域"] = df["区域"].replace("浦东", "浦东新")
        df["区域"] = df["区域"] + "区"
    elif city_name == "sz":
        df = df[df["区域"] != "精选"]
        df = df[df["区域"] != "大鹏新区"]
        
    elif city_name == "tj":
        df = df[df["区域"] != "精选"]
        df["区域"] = df["区域"] + "区"
    # 添加 '区' 到所有区域名称
    
    return df

def process_city_data(file_path, city_name, output_dir):
    """
    处理单个城市的数据并保存清理后的数据
    """
    try:
        # 读取 CSV 文件
        df = pd.read_csv(file_path)

        # 清理数据
        df_clean = clean_data(df.copy(), city_name)

        # 显示清理后的前五行
        print(f"{city_name} 清理后的数据：")
        print(df_clean.head())

        # 创建输出目录（如果不存在）
        os.makedirs(output_dir, exist_ok=True)

        # 保存清理后的数据为新的 CSV 文件
        output_file = os.path.join(output_dir, f"{city_name}_region_price_cleaned.csv")
        df_clean.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"{city_name} 的清理数据已保存到 {output_file}")

        # 返回清理后的数据
        return df_clean
    except Exception as e:
        print(f"处理 {city_name} 时发生错误: {e}")
        return None

def main():
    # 定义城市及其数据文件路径
    cities = {
        "bj": "../processed_data/bj_region_price.csv",
        "gz": "../processed_data/gz_region_price.csv",
        "sh": "../processed_data/sh_region_price.csv",
        "sz": "../processed_data/sz_region_price.csv",
        "tj": "../processed_data/tj_region_price.csv"
    }

    # 输出目录
    output_dir = "../processed_data"

    # 处理每个城市的数据
    for city_name, file_path in cities.items():
        process_city_data(file_path, city_name, output_dir)

if __name__ == "__main__":
    main()
