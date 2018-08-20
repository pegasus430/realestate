# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class RealestateItem(scrapy.Item):

    title = scrapy.Field()
    type = scrapy.Field()
    url = scrapy.Field()
    rent_buy = scrapy.Field()
    price = scrapy.Field()
    other_charges = scrapy.Field()
    other_charges1 = scrapy.Field()
    agency_fee = scrapy.Field()
    other_agency_fee = scrapy.Field()
    deposit = scrapy.Field()
    caf_avaliable = scrapy.Field()
    rooms = scrapy.Field()
    pieces = scrapy.Field()
    size = scrapy.Field()
    furnished = scrapy.Field()
    address = scrapy.Field()
    district = scrapy.Field()
    parisian_district = scrapy.Field()
    city = scrapy.Field()
    email = scrapy.Field()
    phone = scrapy.Field()
    description = scrapy.Field()
    agency_name = scrapy.Field()
    agency_address = scrapy.Field()
    agency_phone = scrapy.Field()
    agency_city = scrapy.Field()
    agency_postal_code = scrapy.Field()
    online = scrapy.Field()
    images = scrapy.Field()
    website = scrapy.Field()
    construction_year = scrapy.Field()
    floor = scrapy.Field()
    website_logo = scrapy.Field()
    agency_logo = scrapy.Field()