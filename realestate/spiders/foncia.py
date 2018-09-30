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
    name = "foncia"
    start_url = 'https://fr.foncia.com/location/paris-75/appartement--maison--chambre'
    domain1 = 'https://fr.foncia.com'

    use_selenium = False
    count = 0
    pageIndex = 1
    totalpage= None
    custom_settings = {
	    'CRAWLERA_ENABLED' : False,
        # 'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        "DOWNLOADER_MIDDLEWARES":{
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 400,
            # 'scrapy_crawlera.CrawleraMiddleware': 610,
            'random_useragent.RandomUserAgentMiddleware': None
        }
	}

    def start_requests(self):
        yield Request(self.start_url, callback= self.parse, meta={"next_count": 1})

    def parse(self, response):
        urls = response.xpath('//article[@class="TeaserOffer "]/a/@href').extract()
        for url in urls:
            yield Request(response.urljoin(url), callback=self.final_parse)

        next_page_url = response.xpath('//*[@class="Pagination Pagination--more"]/a[contains(text(), "Suivante")]/@href').extract_first()

        if next_page_url:
            yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True)


    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['website_logo'] = 'https://fr.foncia.com/bundles/fonciainternet/images/logos/foncia-square-50@1x.png'
        item['url'] = response.url
        item['description'] = response.xpath('//div[@class="OfferDetails-content"]/p/text()').extract_first()
        item['title'] = response.xpath('//title/text()').extract_first().replace('- Foncia', '').strip()

        price = response.xpath('//p[@class="OfferTop-price"]/text()').re(r'[\d.,]+')
        if price:
            try:
                price = ''.join(price)
                item['price'] = price.replace(',', '.')
            except:
                pass

        type1 = response.xpath('//p[@class="Breadcrumbs-inner"]/span/text()').extract()
        # type1 = response.url.split('/')[-3]
        item['type'] = type1[1]
        item['city'] = 'Paris'
        item['district'] = response.xpath('//p[@class="OfferTop-loc"]/@data-gtm-zipcode').extract_first()

        images = response.xpath('//ul[@class="OfferSlider-main-slides"]//img/@src').extract()
        image_urls = ','.join(images)
        item['images'] = image_urls

        other_tags = response.xpath('//*[@class="List List--data"]/li')
        for li in other_tags:
            key = ''.join(li.xpath('./span//text()').extract())
            if 'Honoraires charge' in key:
                item['agency_fee'] = ''.join(li.xpath('./strong/text()').re(r'[\d.,]+'))
            elif 'Dépôt de garantie' in key:
                item['deposit'] = ''.join(li.xpath('./strong/text()').re(r'[\d.,]+'))
            elif 'Année de construction' in key:
                item['construction_year'] = li.xpath('./strong/text()').extract_first()

        attrs = response.xpath('//div[@class="MiniData-row MiniData-row--bg"]/p/text()').extract()
        for txt_attr in attrs:
            if txt_attr[-1] == 'm':
                item['size'] =re.findall(r'[\d.,]+', txt_attr)[0]
            elif 'pièce' in txt_attr:
                item['pieces'] =re.findall(r'[\d]+', txt_attr)[0]
            elif 'chambre' in txt_attr:
                item['rooms'] =re.findall(r'[\d]+', txt_attr)[0]

        agency_name = response.xpath('//p[@class="OfferContact-address OfferContact-address--center rwd--noMobile rwd--noTablet"]/a/strong/text()').extract_first()
        if agency_name:
            item['agency_name'] = agency_name.strip().replace('\n', ' ')

        agency_address = ''.join(response.xpath('//p[@class="OfferContact-address OfferContact-address--center rwd--noMobile rwd--noTablet"]/a/text()')
                                 .extract()).replace(' ', '').strip().replace('\n', ' ')
        if agency_address:
            item['agency_address'] = agency_address.strip()

        address =  response.xpath('//p[@data-behat="adresseBien"]/text()').extract_first()
        if address:
            item['address'] = address.strip().replace('  ', '').replace('\n', ' ')

        if 'location' in response.url:
            item['rent_buy'] = 'rent'
        else:
            item['rent_buy'] = 'buy'

        self.count += 1
        print("Total Count: " + str(self.count))

        yield item