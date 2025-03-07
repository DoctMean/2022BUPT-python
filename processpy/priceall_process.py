import json
import os
import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Optional,Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定义城市列表及对应的文件路径
CITIES = {
    "bj": "../data/bj_rent.json",
    "sh": "../data/sh_rent.json",
    "gz": "../data/gz_rent.json",
    "sz": "../data/sz_rent.json",
    "tj": "../data/tj_rent.json",
}

OUTPUT_DIR = "../processed_data"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


class RentDataProcessor:
    """
    处理租房数据，提取价格和单位面积租金，计算统计信息
    """

    def __init__(self, city: str, filename: str):
        self.city = city
        self.filename = filename

    def _load_json_data(self) -> Optional[List[Dict]]:
        """
        加载 JSON 数据文件
        """
        if not os.path.exists(self.filename):
            logger.warning(f"文件 {self.filename} 不存在，跳过 {self.city} 城市。")
            return None

        try:
            with open(self.filename, encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            logger.error(f"文件 {self.filename} 解析失败，跳过 {self.city} 城市。错误信息: {e}")
            return None

    def _extract_data(self, listings: List[Dict]) -> Tuple[List[float], List[float]]:
        """
        从房源数据中提取租金和单位面积租金
        """
        rent_prices = []
        rent_per_sqm = []

        for listing in listings:
            price = self._extract_price(listing)
            if price <= 0:
                continue  # 如果价格无效，跳过此条记录

            area = self._extract_area(listing)
            if area <= 0:
                continue  # 如果面积无效，跳过此条记录

            price_sqm = price / area  # 计算单位面积租金

            rent_prices.append(price)
            rent_per_sqm.append(price_sqm)

        return rent_prices, rent_per_sqm

    def _extract_price(self, listing: Dict) -> float:
        """
        提取租金价格
        """
        price_str = listing.get("price", "0元/月").replace("元/月", "").replace(",", "").strip()
        try:
            return float(price_str)
        except ValueError:
            return 0.0

    def _extract_area(self, listing: Dict) -> float:
        """
        提取面积
        """
        info = listing.get("info", [])
        area_str = next((item.replace("㎡", "").replace(",", "").strip() for item in info if "㎡" in item), None)
        try:
            return float(area_str) if area_str else 0.0
        except ValueError:
            return 0.0

    def calculate_statistics(self, data: List[float]) -> Dict[str, float]:
        """
        计算给定数据的统计信息
        """
        if len(data) == 0:
            return {}
        data_np = np.array(data)
        stats = {
            "均值": np.round(np.mean(data_np), 2),
            "标准差": np.round(np.std(data_np, ddof=1), 2),
            "最高值": np.round(np.max(data_np), 2),
            "最低值": np.round(np.min(data_np), 2),
            "中位数": np.round(np.median(data_np), 2),
            "25%分位数": np.round(np.percentile(data_np, 25), 2),
            "75%分位数": np.round(np.percentile(data_np, 75), 2),
        }
        return stats

    def process(self) -> Optional[Dict[str, pd.DataFrame]]:
        """
        处理数据，返回租金和单位面积租金的统计信息
        """
        listings = self._load_json_data()
        if not listings:
            return None

        # 提取数据
        rent_prices, rent_per_sqm = self._extract_data(listings)

        # 计算租金统计
        rent_stats = self.calculate_statistics(rent_prices)
        rent_stats["城市"] = self.city
        rent_stats["数据量"] = len(rent_prices)

        # 计算单位面积租金统计
        unit_price_stats = self.calculate_statistics(rent_per_sqm)
        unit_price_stats["城市"] = self.city
        unit_price_stats["数据量"] = len(rent_per_sqm)

        # 将统计信息转换为 DataFrame
        rent_df = pd.DataFrame([rent_stats])
        unit_price_df = pd.DataFrame([unit_price_stats])

        return {"rent": rent_df, "unit_price": unit_price_df}


class DataExporter:
    """
    将处理后的数据导出为 CSV 文件
    """

    @staticmethod
    def save_to_csv(df: pd.DataFrame, filename: str):
        """
        保存 DataFrame 为 CSV 文件
        """
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        logger.info(f"数据已成功保存到 {filename}")


class CityRentDataProcessor:
    """
    处理多个城市的数据，组织数据处理和导出
    """

    def __init__(self, cities: Dict[str, str]):
        self.cities = cities

    def process_and_export_data(self):
        """
        处理所有城市的数据并导出
        """
        all_rent_data = []
        all_unit_price_data = []

        for city, filename in self.cities.items():
            logger.info(f"开始处理 {city} 城市的数据...")
            processor = RentDataProcessor(city, filename)
            result = processor.process()

            if result:
                all_rent_data.append(result["rent"])
                all_unit_price_data.append(result["unit_price"])

        # 合并所有城市的数据
        if all_rent_data:
            rent_df = pd.concat(all_rent_data, ignore_index=True)
            unit_price_df = pd.concat(all_unit_price_data, ignore_index=True)

            # 导出数据
            rent_output_filename = os.path.join(OUTPUT_DIR, "price_data.csv")
            unit_price_output_filename = os.path.join(OUTPUT_DIR, "unit_price_data.csv")

            DataExporter.save_to_csv(rent_df, rent_output_filename)
            DataExporter.save_to_csv(unit_price_df, unit_price_output_filename)
        else:
            logger.warning("没有有效的租金数据，未生成任何文件。")


# 主逻辑：处理和导出所有城市的租金数据
if __name__ == "__main__":
    city_processor = CityRentDataProcessor(CITIES)
    city_processor.process_and_export_data()
