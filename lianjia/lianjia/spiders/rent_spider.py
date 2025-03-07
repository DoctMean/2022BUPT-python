import re
import scrapy
from lianjia.items import RentHouseItem


class RentHouseSpider(scrapy.Spider):
    name = "rent_spider"
    allowed_domains = ["lianjia.com"]
    city = "tj"  # 更改为所需城市 ("sh", "bj", "gz", "sz", "tj")
    max_price_pages = 8 if city == "sh" else 7  # 根据价格范围调整最大页数
    base_url = f"https://{city}.lianjia.com"

    custom_settings = {
        "FEEDS": {
            f"{city}_rent.json": {
                "format": "json",
                "encoding": "utf8",
                "overwrite": True,
            },
        },
    }

    def start_requests(self):
        """从城市租赁主页开始抓取。"""
        start_url = f"{self.base_url}/zufang/"
        yield scrapy.Request(url=start_url, callback=self.parse_level, meta={'level': 'city'})

    def parse_level(self, response):
        """
        处理当前子区域层级。
        判断是否需要进一步细分或处理分页。
        """
        current_level = response.meta.get('level')
        self.logger.info(f"解析 {current_level} 页: {response.url}")
        total_pages, total_houses = self.get_page_info(response)

        # 定义子区域层级结构
        subdivision_hierarchy = {
            'city': {
                'should_subdivide': self.should_subdivide(total_pages, total_houses),  # 是否要再分级进行下一步parse
                'next_level': 'area',   # 下一步parse分级
                'extract_urls': self.extract_area_urls   # 下一步parse使用的url
            },
            'area': {
                'should_subdivide': self.should_subdivide(total_pages, total_houses),
                'next_level': 'price',
                'url_modifier': self.get_price_url,
                'max_pages': self.max_price_pages
            },
            'price': {
                'should_subdivide': self.should_subdivide(total_pages, total_houses),
                'next_level': 'room',
                'url_modifier': self.get_room_url,
                'patterns': self.get_price_regex(),
                'list': self.get_room_type_list()
            },
            'room': {
                'should_subdivide': self.should_subdivide(total_pages, total_houses),
                'next_level': 'direction',
                'url_modifier': self.get_direction_url,
                'patterns': self.get_room_regex(),
                'list': self.get_direction_list()
            },
            'direction': {
                'should_subdivide': self.should_subdivide(total_pages, total_houses),
                'next_level': 'floor',
                'url_modifier': self.get_floor_url,
                'patterns': self.get_direction_regex(),
                'list': self.get_floor_list()
            },
            'floor': {
                'should_subdivide': False  # 无需进一步细分
            }
        }

        current_subdivision = subdivision_hierarchy.get(current_level, {})
        if current_subdivision.get('should_subdivide'):
            next_level = current_subdivision['next_level']
            if 'extract_urls' in current_subdivision:
                # 基于提取的 URL 进行细分（例如区域）
                next_urls = current_subdivision['extract_urls'](response)
                for url in next_urls:
                    yield scrapy.Request(url=f"{self.base_url}{url}", callback=self.parse_level, meta={'level': next_level}, dont_filter=True)
            elif 'url_modifier' in current_subdivision:
                # 基于 URL 模式进行细分（例如价格、房型、朝向）
                if current_level == 'price':
                    for i in range(1, current_subdivision['max_pages'] + 1):
                        modified_url = current_subdivision['url_modifier'](response.url, i)
                        yield scrapy.Request(url=modified_url, callback=self.parse_level, meta={'level': next_level}, dont_filter=True)
                else:
                    for item in current_subdivision['list']:
                        modified_url = current_subdivision['url_modifier'](response.url, item)
                        yield scrapy.Request(url=modified_url, callback=self.parse_level, meta={'level': next_level}, dont_filter=True)
        else:
            # 如果不需要进一步细分，则处理分页
            yield from self.handle_pagination(response.url, total_pages)

    def should_subdivide(self, total_pages, total_houses):
        """判断当前页面是否需要进一步细分。"""
        return total_pages == 100 or total_houses > 3000

    def handle_pagination(self, base_url, total_pages):
        """处理分页，通过生成每一页的请求。"""
        if total_pages:
            for page_number in range(1, total_pages + 1):
                paginated_url = f"{base_url}pg{page_number}/"
                yield scrapy.Request(url=paginated_url, callback=self.parse_data, dont_filter=True)
        else:
            self.logger.warning(f"{base_url} 没有找到分页数据")

    def parse_data(self, response):
        """从页面中提取房源信息。"""
        self.logger.info(f"从页面提取数据: {response.url}")

        for house in response.xpath(
            '//div[@class="content__article"]/div[@class="content__list"][1]//div[@class="content__list--item"]'
        ):
            item = RentHouseItem()
            item["title"] = self.extract_text(
                house,
                './div[@class="content__list--item--main"]/p[@class="content__list--item--title"]/a[@class="twoline"]/text()',
                "N/A"
            )
            item["info"] = self.extract_descriptions(house)
            item["bottom"] = self.extract_bottom_info(house)
            item["source"] = self.extract_text(
                house,
                './div[@class="content__list--item--main"]/p[@class="content__list--item--brand oneline"]/span[@class="brand"]/text()',
                "N/A"
            )
            item["price"] = self.extract_text(
                house,
                './div[@class="content__list--item--main"]/span[@class="content__list--item-price"]//text()',
                "N/A"
            )

            yield item

    def extract_text(self, house, xpath_expr, default_value):
        """辅助函数，用于提取单个文本或返回默认值。"""
        text = house.xpath(xpath_expr).get()
        return text.strip() if text else default_value

    def extract_descriptions(self, house):
        """提取并清理房源描述信息。"""
        descriptions = house.xpath(
            './div[@class="content__list--item--main"]/p[@class="content__list--item--des"]//text()'
        ).getall()
        return ["".join(text.split()) for text in descriptions if text.strip() and text.strip() not in ["-", "/"]]
        # 提取并清理每个文本元素：去除多余的空格，排除无用的字符（"-"和"/"）

    def extract_bottom_info(self, house):
        """提取底部信息（例如 '电梯'、'停车' 等标签）。"""
        bottom_info = house.xpath(
            './div[@class="content__list--item--main"]/p[@class="content__list--item--bottom oneline"]//i/text()'
        ).getall()
        return [text.strip() for text in bottom_info if text.strip()] or []
        # 将文本元素内的值逐个提取出来

    def get_page_info(self, response):
        """从页面中获取总页数和房源总数。"""
        total_pages = self.extract_total_pages(response)
        total_houses = self.extract_total_houses(response)
        return total_pages, total_houses

    def extract_total_pages(self, response):
        """从响应中提取总页数。"""
        total_pages_str = response.xpath('//div[@class="content__pg"]/@data-totalpage').get()
        return self.parse_integer(total_pages_str)

    def extract_total_houses(self, response):
        """从响应中提取房源总数。"""
        total_houses_str = response.xpath('//span[@class="content__title--hl"]/text()').get()
        return self.parse_integer(total_houses_str)

    def parse_integer(self, value):
        """从字符串中解析整数，如果无效则返回 0。"""
        try:
            return int(value)
        except (ValueError, TypeError):
            self.logger.warning(f"无效的整数值: {value}")
            return 0

    def extract_area_urls(self, response):
        """从城市页面中提取区域的 URL。"""
        return response.xpath(
            '//div[@class="filter"]/div[@class="filter__wrapper w1150"]/ul[@data-target="area"]//li/a/@href'
        ).getall()

    def get_price_regex(self):
        """根据城市返回适当的正则表达式模式。"""
        return re.compile(r"(rp[1-8])") if self.city == "sh" else re.compile(r"(rp[1-7])")

    def get_room_regex(self):
        """返回房型的正则表达式模式。"""
        return re.compile(r"(l[0-3])")

    def get_direction_regex(self):
        """返回朝向的正则表达式模式。"""
        return re.compile(r"(f10050000000[15379])")

    def get_floor_regex(self):
        """返回楼层的正则表达式模式。"""
        return re.compile(r"(lc20050000000[123])")

    def get_room_type_list(self):
        """返回房型列表。"""
        return [f"l{i}" for i in range(0, 4)]

    def get_direction_list(self):
        """返回朝向列表。"""
        return ["f100500000001", "f100500000005", "f100500000003", "f100500000007", "f100500000009"]

    def get_floor_list(self):
        """返回楼层列表。"""
        return ["lc200500000003", "lc200500000002", "lc200500000001"]

    def get_price_url(self, base_url, page_number):
        """生成特定价格范围页面的 URL。"""
        return f"{base_url}rp{page_number}/"

    def get_room_url(self, base_url, room_type):
        """生成特定房型的 URL。"""
        room_regex = self.get_room_regex()
        match = room_regex.search(base_url)
        if match:
            room_identifier = match.group(1)
            return f"{base_url.split(room_identifier, 1)[0]}{room_type}{room_identifier}/"
        else:
            self.logger.warning(f"在 URL 中未找到房型模式: {base_url}")
            return base_url

    def get_direction_url(self, base_url, direction):
        """生成特定朝向的 URL。"""
        direction_regex = self.get_direction_regex()
        match = direction_regex.search(base_url)
        if match:
            direction_identifier = match.group(1)
            return f"{base_url.split(direction_identifier, 1)[0]}{direction}{direction_identifier}/"
        else:
            self.logger.warning(f"在 URL 中未找到朝向标识符: {base_url}")
            return base_url

    def get_floor_url(self, base_url, floor):
        """生成特定楼层的 URL。"""
        floor_regex = self.get_floor_regex()
        match = floor_regex.search(base_url)
        if match:
            floor_identifier = match.group(1)
            return f"{base_url.split(floor_identifier, 1)[0]}{floor}{floor_identifier}/"
        else:
            self.logger.warning(f"在 URL 中未找到楼层模式: {base_url}")
            return base_url
