# -*- coding: utf-8 -*-
from scrapy import Spider, Request, FormRequest
import sys
import re, os, requests, urllib
from scrapy.utils.response import open_in_browser
import time, datetime
from shutil import copyfile
import json, re, random
from realestate.items import RealestateItem
from scrapy.conf import settings
from collections import OrderedDict

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

class selogerSpider(Spider):
    name = "meilleursagents"
    start_url = 'https://www.meilleursagents.com/immobilier/recherche/?redirect_url=&view_mode=&sort_mode=&transaction_type=369681778&buyer_search_id=&user_email=&place_ids%5B%5D=138724240&place_title=&item_types%5B%5D=369681781&item_types%5B%5D=369681782&item_area_min=&item_area_max=&budget_min=&budget_max='
    domain1 = 'https://www.meilleursagents.com'

    use_selenium = False
    count = 0
    pageIndex = 1
    totalpage= None

    custom_settings = {
	    # 'CRAWLERA_ENABLED' : False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        "DOWNLOADER_MIDDLEWARES":{
            # 'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 400,
            'scrapy_crawlera.CrawleraMiddleware': 610,
            'random_useragent.RandomUserAgentMiddleware': None
        }
	}

    def start_requests(self):
        yield Request(self.start_url, callback= self.parse, meta={"next_count": 1})

    def parse(self, response):
        urls = response.xpath('//div[@class="block relative no_decoration"]/a/@href').extract()
        for url in urls:
            yield Request(response.urljoin(url), callback=self.final_parse)

        next_page_url = response.xpath('//div[@class="pagination pagination-centered"]/ul/li/a[@rel="next"]/@href').extract_first()

        if next_page_url:
            yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True)


    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['website_logo'] = 'https://static.meilleursagents.com/3.4.0/img/www/logo-meilleursagents-std.png'
        item['url'] = response.url
        item['description'] = response.xpath('//p[@class="tjustify chapo-small"]/text()').extract_first()
        item['title'] = response.xpath('//h1[@class="margin-none"]/text()').extract_first().strip()

        price = response.xpath('//div[@class="h2"]/strong/text()').re(r'[\d.,]+')
        if price:
            try:
                price = ''.join(price)
                item['price'] = price.replace(',', '.')
            except:
                pass
        item['type'] = response.xpath('//table[@class="table table-striped chapo-small pull-left"]//tr/td/text()').extract_first().split(' ')[0]
        item['city'] = response.xpath('//div[@class="muted"]/text()').extract_first().strip().split(' ')[0]
        item['district'] = response.xpath('//div[@class="muted"]/text()').re(r'[\d]+')[0]

        images = response.xpath('//div[@id="realtor_listing_carousel_pictures"]/a/@href').extract()
        imgs = []
        for img in images:
            img = 'https:' + img
            imgs.append(img)
        image_urls = ','.join(imgs)
        item['images'] = image_urls

        agency_name = response.xpath('//h4[@class="tcenter margin-bottom"]/a/text()').extract_first()
        if agency_name:
            item['agency_name'] = agency_name.strip()

        other_tags = response.xpath('//div[not(@id)]/table/tr')
        for li in other_tags:
            key = ''.join(li.xpath('./td//text()').extract())
            if 'pièces' in key:
                item['pieces'] = li.xpath('./td//text()').re(r'[\d]+')[0]
            elif 'Surface de' in key:
                item['size'] = li.xpath('./td//text()').re(r'[\d.,]+')[0]
            elif 'chambre' in key:
                item['rooms'] = li.xpath('./td//text()').re(r'[\d]+')[0]
            elif 'Etage' in key:
                item['floor'] = li.xpath('./td//text()').re(r'[\d]+')[0]
            elif 'Construit en' in key:
                item['construction_year'] = li.xpath('./td//text()').re(r'[\d]+')[0]

        if "Studio" == item['type']:
            item['pieces'] = 1

        other_tags = response.xpath('//div[not(@id)]/table/tr')
        for li in other_tags:
            key = ''.join(li.xpath('./td//text()').extract())
            if 'pièces' in key:
                item['pieces'] = li.xpath('./td//text()').re(r'[\d]+')[0]
            elif 'Surface de' in key:
                item['size'] = li.xpath('./td//text()').re(r'[\d.,]+')[0]
            elif 'chambre' in key:
                item['rooms'] = li.xpath('./td//text()').re(r'[\d]+')[0]
            elif 'Etage' in key:
                item['floor'] = li.xpath('./td//text()').re(r'[\d]+')[0]
            elif 'Construit en' in key:
                item['construction_year'] = li.xpath('./td//text()').re(r'[\d]+')[0]


        other_tags = response.xpath('//div[@id="details"]/table//tr')
        for li in other_tags:
            key = ''.join(li.xpath('./td[1]//text()').extract())
            if 'Charges locatives' in key:
                other_charges = li.xpath('./td[2]//text()').re(r'[\d]+')
                if other_charges:
                    item['other_charges'] = other_charges[0]
            elif 'Dépôt de garantie' in key:
                deposit= li.xpath('./td[2]//text()').re(r'[\d.,]+')
                if deposit:
                    item['deposit'] = deposit[0]
            elif 'Honoraires charge' in key:
                fee= li.xpath('./td[2]//text()').re(r'[\d]+')
                if fee:
                    item['agency_fee'] = fee[0]


        if 'location' in response.url:
            item['rent_buy'] = 'rent'
        else:
            item['rent_buy'] = 'buy'
        item['rent_buy'] = 'rent'
        self.count += 1
        print("Total Count: " + str(self.count))

        yield item