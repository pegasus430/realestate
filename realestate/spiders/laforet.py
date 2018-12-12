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

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

class selogerSpider(Spider):
    name = "laforet"
    start_url = 'http://www.laforet.com/louer/rechercher?localisation=Paris%20%2875%29&maison=on&appartement=on'
    domain1 = 'http://www.laforet.com'

    use_selenium = False
    count = 0
    pageIndex = 1
    totalpage= None
    custom_settings = {
	    'CRAWLERA_ENABLED' : False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        "DOWNLOADER_MIDDLEWARES":{
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 400,
            'scrapy_crawlera.CrawleraMiddleware': 610,
            'random_useragent.RandomUserAgentMiddleware': None
        }
	}

    def start_requests(self):
        yield Request(self.start_url, callback= self.parse, meta={"next_count": 1})

    def parse(self, response):
        url_tags = response.xpath('//ul[@class="results-compact"]/li')
        for tag in url_tags:
            data_json = tag.xpath('./@data-json').extract_first()
            data_json = json.loads(data_json)
            url = tag.xpath('./a/@href').extract_first()

            item = RealestateItem()
            item['title'] = data_json['title'] +' ' + data_json['title_city']
            item['online'] = 1
            item['website'] = self.name
            item['website_logo'] = 'http://www.laforet.com/sites/default/themes/laforet/logo.png'

            try:
                item['description'] = data_json['description']
            except:
                pass

            try:
                item['price'] = data_json['price'].replace(' ', '')
            except:
                pass

            try:
                item['type'] = data_json['title'].split(' ')[0].lower()
            except:
                pass

            try:
                item['city'] = data_json['title_city'].split(' ')[0]
            except:
                pass

            try:
                item['district'] = data_json['postalCode']
            except:
                try:
                    item['district'] = re.findall(r'[\d]+', data_json['title_city'])[-1]
                except:
                    pass

            try:
                item['city'] = data_json['title_city'].split(' ')[0]
            except:
                pass

            imgurl1 = data_json['imageUrl']
            imgurl = imgurl1 +',' + imgurl1.split('.jpg')[0][0:-1] + 'b.jpg'
            imgurl = imgurl +',' + imgurl1.split('.jpg')[0][0:-1] + 'c.jpg'
            imgurl = imgurl +',' + imgurl1.split('.jpg')[0][0:-1] + 'd.jpg'
            item['images'] = imgurl

            try:
                item['size'] = data_json['surface']
            except:
                pass

            try:
                item['pieces'] = data_json['roomsQuantity']
            except:
                pass

            try:
                item['deposit'] = data_json['deposit']
            except:
                pass

            try:
                item['agency_fee'] = data_json['fees']
            except:
                pass

            item['rent_buy'] = 'rent'
            item['url'] = response.urljoin(data_json['url'])

            yield Request(item['url'], callback=self.final_parse, meta={'item': item}, )

        next_page_url = response.xpath('//*[@aria-label="Next"]/a[@aria-label="Next"]/@href').extract_first()

        if next_page_url:
            yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True)


    def final_parse(self, response):
        item = response.meta['item']

        other_charges = response.xpath('//div[@class="mentions-location"]/span/text()').re(r'[\d.,]+')
        if other_charges:
            item['other_charges'] = other_charges[0]
        agency_name = response.xpath('//div[@class="legal-informations"]/p[1]/text()').extract_first()
        if 'AGENCE' in agency_name:
            item['agency_name'] = agency_name
        item['agency_address'] = ' '.join(response.xpath('//div[@class="agency-detail"]/div/p/text()').extract())

        li_attrs = response.xpath('//div[@class="caracteristiques-detail"]/ul/li')
        for li in li_attrs:
            key = li.xpath('./h3/text()').extract_first()
            if 'Meublé' in key:
                val = li.xpath('./span/text()').extract_first()
                if 'Oui' in val:
                    item['furnished'] = 1

        self.count += 1
        print("Total Count: " + str(self.count))

        yield item