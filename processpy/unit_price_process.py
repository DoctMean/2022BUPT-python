import json
import os
import pandas as pd
import logging
from typing import List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定义城市缩写到全称的映射
CITY_FULL_NAMES = {
    "bj": "北京",
    "sh": "上海",
    "gz": "广州",
    "sz": "深圳",
    "tj": "天津"
}

# 定义城市列表及对应的 JSON 文件名
CITIES = {
    "bj": "../data/bj_rent.json",
    "sh": "../data/sh_rent.json",
    "gz": "../data/gz_rent.json",
    "sz": "../data/sz_rent.json",
    "tj": "../data/tj_rent.json",
}

OUTPUT_DIR = "../processed_data"


class RentDataProcessor:
    """
    处理单个城市的租房数据，包括从文件中提取数据、计算单位面积租金。
    """

    def __init__(self, city_code: str, filename: str):
        self.city_code = city_code
        self.filename = filename
        self.city_name = CITY_FULL_NAMES.get(city_code, city_code)

    def _load_json(self) -> Optional[List[dict]]:
        """
        加载 JSON 文件并返回数据列表，失败时返回 None。
        """
        if not os.path.exists(self.filename):
            logger.warning(f"文件 {self.filename} 不存在，跳过 {self.city_name} 城市。")
            return None
        
        try:
            with open(self.filename, encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            logger.error(f"文件 {self.filename} 解析失败，跳过 {self.city_name} 城市。错误信息: {e}")
            return None

    def _extract_unit_rent(self, listings: List[dict]) -> List[dict]:
        """
        从房源数据中提取单位面积租金。
        """
        unit_rents = []

        for listing in listings:
            area_str = next((item.replace("㎡", "").replace(",", "").strip() for item in listing.get("info", []) if "㎡" in item), None)
            price_str = listing.get("price", "0元/月").replace("元/月", "").replace(",", "").strip()

            # 提取面积
            if not area_str or not self._is_valid_area(area_str):
                continue

            # 提取租金
            if not self._is_valid_price(price_str):
                continue

            # 计算单位面积租金
            unit_rent = float(price_str) / float(area_str)
            unit_rents.append({"单位面积租金（元/月/㎡）": unit_rent})

        return unit_rents

    @staticmethod
    def _is_valid_area(area_str: str) -> bool:
        """
        检查面积是否合法
        """
        try:
            area = float(area_str)
            return area > 0
        except ValueError:
            return False

    @staticmethod
    def _is_valid_price(price_str: str) -> bool:
        """
        检查租金是否合法
        """
        try:
            price = float(price_str.replace("元/月", ""))
            return price > 0
        except ValueError:
            return False

    def process(self) -> Optional[pd.DataFrame]:
        """
        处理数据并返回计算出的单位面积租金 DataFrame。
        """
        listings = self._load_json()
        if not listings:
            return None

        unit_rents = self._extract_unit_rent(listings)
        if not unit_rents:
            logger.warning(f"{self.city_name} 城市没有有效的数据。")
            return None

        # 返回处理后的 DataFrame
        return pd.DataFrame(unit_rents)


class DataExporter:
    """
    将处理后的数据导出为 CSV 文件。
    """
    @staticmethod
    def save_to_csv(city_code: str, df: pd.DataFrame):
        """
        将 DataFrame 保存为 CSV 文件。
        """
        output_filename = os.path.join(OUTPUT_DIR, f"{city_code}_unit_price.csv")
        df.to_csv(output_filename, index=False, encoding="utf-8-sig")
        logger.info(f"{CITY_FULL_NAMES.get(city_code, city_code)} 城市的单位面积租金已成功保存到 {output_filename}")


class CityRentDataProcessor:
    """
    处理多个城市的数据，组织整个数据处理和导出过程。
    """

    @staticmethod
    def process_and_export_data():
        """
        处理所有城市数据并导出为 CSV。
        """
        # 创建输出目录
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        for city_code, filename in CITIES.items():
            logger.info(f"开始处理 {CITY_FULL_NAMES.get(city_code, city_code)} 城市的数据...")
            processor = RentDataProcessor(city_code, filename)
            df_city = processor.process()

            if df_city is not None:
                DataExporter.save_to_csv(city_code, df_city)
            else:
                logger.warning(f"{CITY_FULL_NAMES.get(city_code, city_code)} 城市没有有效的数据，跳过导出。")


# 主逻辑：处理和导出所有城市的租金数据
if __name__ == "__main__":
    CityRentDataProcessor.process_and_export_data()
