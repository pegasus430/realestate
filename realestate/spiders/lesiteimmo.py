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
    name = "lesiteimmo"
    start_url = 'https://www.lesiteimmo.com/louer/maison,appartement/paris-75000'
    domain1 = 'https://www.lesiteimmo.com'

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
        urls = response.xpath('//div[@itemprop="itemListElement"]//a[@itemprop="url"]/@href').extract()
        for url in urls:
            yield Request(url, callback=self.final_parse)

        next_page_url = response.xpath('//a[@title="Page suivante"]/@href').extract_first()

        if next_page_url:
            yield Request(next_page_url, callback=self.parse, dont_filter=True)


    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['website_logo'] = 'https://www.lesiteimmo.com/images/logo.svg?id=409b2bdfb76416b8f554'
        item['url'] = response.url
        item['description'] = response.xpath('//div[@itemprop="description"]/text()').extract_first().strip()
        item['title'] = response.xpath('//title/text()').extract_first()

        price = response.xpath('//span[@class="text-xl font-medium"]/span[@class="value"]/text()').re(r'[\d.,]+')
        if price:
            try:
                price = ''.join(price)
                item['price'] = price.replace(',', '.')
            except:
                pass

        type1 = response.xpath('//h1[@itemprop="name"]/text()').extract_first()
        item['type'] = type1.strip().split(' ')[0]

        item['city'] = 'Paris'
        item['district'] = response.url.split('/')[-2].split('-')[-1]

        images = response.xpath('//div[contains(@class,"bg-cover h-64 lg:h-128 w-full")]/@style').extract()
        image_urls = []
        for img in images:
            img_url = img.split("url('")[-1].split("')")[0]
            image_urls.append(img_url)
        item['images'] = ','.join(image_urls)

        agency_name = response.xpath('//div[@class="font-medium text-grey-darkest"]/text()').extract_first()
        if agency_name:
            item['agency_name'] = agency_name.strip().replace('\n', ' ')

        agency_address = response.xpath('//div[@class="text-grey"]/text()').extract_first()
        if agency_address:
            item['agency_address'] = agency_address.strip()

        agency_logo = response.xpath('//div[@class="mb-2"]/img/@src').extract_first()
        if agency_logo:
            item['agency_logo'] = agency_logo

        # attr_tags = response.xpath('//div[@class="p-4 flex flex-wrap justify-start items-start"]//div[@class="flex w-full p-2 bg-grey-lightest"]')
        # for div in attr_tags:
        #     key = div.xpath('./div[@class="w-2/3 text-grey-darker mr-2"]/text()').extract_first()
        #     val = div.xpath('./div[@class="w-1/3 text-grey text-right"]/text()').extract_first()
        #     if 'Étage' in key:
        #         item['floor'] = re.findall(r'[\d]+', str(val))[0]
        #     elif 'Nbre. de chambres' in key:
        #         item['rooms'] = val.strip()
        #     elif 'Adresse' == key:
        #         item['address'] = val.strip()
        #     elif 'Nb. de pièces' in key:
        #         item['pieces'] = val.strip()
        #     elif 'Charges' == key:
        #         item['other_charges'] = re.findall(r'[\d.,\s]+', str(val))[0].replace(' ', '')
        #     elif 'Dépôt de garantie' in key:
        #         item['deposit'] = re.findall(r'[\d.,\s]+', str(val))[0].replace(' ', '')
        #     elif 'Honoraires' == key:
        #         item['agency_fee'] = re.findall(r'[\d.,\s]+', str(val))[0].replace(' ', '')
        #     elif 'Année de construction' in key:
        #         item['construction_year'] = val.strip()
        #     elif 'Surface habitable' in key:
        #         item['size'] = re.findall(r'[\d.,\s]+', str(val))[0].replace(' ', '')


        if 'location' in response.url:
            item['rent_buy'] = 'rent'
        else:
            item['rent_buy'] = 'buy'
        item['rent_buy'] = 'rent'
        self.count += 1
        print("Total Count: " + str(self.count))

        yield item