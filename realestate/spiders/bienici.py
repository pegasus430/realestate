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
    name = "bienici"
    # start_url = 'https://www.bienici.com/recherche/location/paris-75000'
    start_url = 'https://www.bienici.com/realEstateAds.json?filters=%7B%22size%22%3A24%2C%22from%22%3A0%2C%22filterType%22%3A%22rent%22%2C%22propertyType%22%3A%5B%22house%22%2C%22flat%22%5D%2C%22page%22%3A1%2C%22resultsPerPage%22%3A24%2C%22maxAuthorizedResults%22%3A2400%2C%22sortBy%22%3A%22relevance%22%2C%22sortOrder%22%3A%22desc%22%2C%22onTheMarket%22%3A%5Btrue%5D%2C%22showAllModels%22%3Afalse%2C%22zoneIdsByTypes%22%3A%7B%22zoneIds%22%3A%5B%22-7444%22%5D%7D%7D&extensionType=extendedIfNoResult&leadingCount=2'
    domain1 = 'https://www.bienici.com'

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
        json_data = json.loads(response.body)
        for data in json_data['realEstateAds']:
            try:
                item = RealestateItem()
                item['online'] = 1
                item['website'] = self.name
                item['website_logo'] = 'https://www.bienici.com/cacheForever/45ee97a38fe6a64ae66c7a2310cf2192ec35f538/logos/logo_bienici.svg'
                if 'roomsQuantity' in data.keys():
                    item['url'] = 'https://www.bienici.com/annonce/location/{}/appartement/{}pieces/{}?q=%2Frecherche%2Flocation%2Fparis-75000'\
                        .format(data['city'].strip().replace(' ', '-'), data['roomsQuantity'], data['id'])
                    item['pieces'] = data['roomsQuantity']
                    item['rooms'] = data['roomsQuantity']
                else:
                    item['url'] = 'https://www.bienici.com/annonce/location/{}/appartement/{}?q=%2Frecherche%2Flocation%2Fparis-75000'\
                        .format(data['city'].strip().replace(' ', '-'), data['roomsQuantity'], data['id'])
                item['description'] = data['description']
                item['title'] = data['title']

                if 'surfaceArea' in data.keys():
                    item['size'] = data['surfaceArea']

                if item['title'] == "":
                    item['title'] = "Appartement {} pièces {} m²".format(item['pieces'], item['size'])

                item['rent_buy'] = data['adType']
                item['city'] = data['city'].strip().split(' ')[0]
                item['district'] = data['postalCode']
                item['price'] = data['price']
                if 'floor' in data.keys():
                    item['floor'] = data['floor']
                if 'agencyRentalFee' in data.keys():
                    item['agency_fee'] = data['agencyRentalFee']
                if 'safetyDeposit' in data.keys():
                    item['deposit'] = data['safetyDeposit']
                if 'isFurnished' in data.keys():
                    item['furnished'] = 1
                if 'yearOfConstruction' in data.keys():
                    item['construction_year'] = data['yearOfConstruction']
                imgs = []
                for img in data['photos']:
                    imgs.append(img['url'])
                item['images'] = ','.join(imgs)
                # self.count += 1
                # print("Total Count: " + str(self.count))
                yield Request('https://www.bienici.com/realEstateAd.json?id={}&access_token=2lWi9yZU%2FR%2FuoEAybaCQI7Q0CMe3RD5aquaK7rLs63Y%3D%3A5b543410ac93c7009bfa3572'.format(data['id']), self.final_parse, meta={'item': item})
                # yield item
            except Exception as e:
                print("err: " + e.args[0] )
                self.count += 1
                print("Total Count: " + str(self.count))
                yield item

        total = int(json_data['total'])
        current = int(json_data['from'])
        if current < total:
            next = current+ 24
            page = int((current/24) + 1)
            next_page_url = 'https://www.bienici.com/realEstateAds.json?filters=%7B%22size%22%3A24%2C%22from%22%3A{}%2C%22filterType%22%3A%22rent%22%2C%22propertyType%22%3A%5B%22house%22%2C%22flat%22%5D%2C%22page%22%3A{}%2C%22resultsPerPage%22%3A24%2C%22maxAuthorizedResults%22%3A2400%2C%22sortBy%22%3A%22relevance%22%2C%22sortOrder%22%3A%22desc%22%2C%22onTheMarket%22%3A%5Btrue%5D%2C%22showAllModels%22%3Afalse%2C%22zoneIdsByTypes%22%3A%7B%22zoneIds%22%3A%5B%22-7444%22%5D%7D%7D&extensionType=extendedIfNoResult&leadingCount=2'.format(next, page)
            yield Request(next_page_url, self.parse)

        # if next_page_url:
        #     yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True)


    def final_parse(self, response):
        item = response.meta['item']
        try:
            json_data = json.loads(response.body)
            item['title'] = json_data['generatedTitle']
            item['type'] = json_data['generatedTitle'].strip().split(' ')[0]
            item['agency_name'] = json_data['contactRelativeData']['contactNameToDisplay']
            item['agency_address'] = json_data['contactRelativeData']['address']['street'] + ' - ' + json_data['contactRelativeData']['address']['city'] + ' ' + json_data['contactRelativeData']['address']['postalCode']
            item['agency_logo'] = 'https://file.bienici.com/photo/' + json_data['contactRelativeData']['imageName']
            self.count += 1
            print("Total Count: " + str(self.count))
            yield item
        except:
            self.count += 1
            print("Total Count: " + str(self.count))
            yield item