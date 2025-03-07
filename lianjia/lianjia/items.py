import scrapy

class RentHouseItem(scrapy.Item):
    # 租房字段
    title = scrapy.Field()  # 标题
    info = scrapy.Field()  # 描述信息
    source = scrapy.Field()  # 来源
    price = scrapy.Field()  # 价格
    bottom = scrapy.Field()  # 底部信息
