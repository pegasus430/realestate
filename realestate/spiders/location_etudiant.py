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
    name = "location_etudiant"
    start_url = 'https://en.location-etudiant.fr/residences-etudiantes-paris.html'
    domain1 = 'https://en.location-etudiant.fr'

    use_selenium = False
    count = 0
    pageIndex = 1
    totalpage= None
    # custom_settings = {
	#     # 'CRAWLERA_ENABLED' : False,
     #    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
     #    "DOWNLOADER_MIDDLEWARES":{
     #        # 'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 400,
     #        'scrapy_crawlera.CrawleraMiddleware': 610,
     #        'random_useragent.RandomUserAgentMiddleware': None
     #    }
	# }

    def start_requests(self):
        yield Request(self.start_url, callback= self.parse, meta={"next_count": 1})

    def parse(self, response):
        urls = response.xpath('//div[@class="list"]/article[not(@class="une")]/div[@class="content"]/h4/a/@href').extract()
        for url in urls:
            yield Request(response.urljoin(url), callback=self.final_parse)

        urls1 = response.xpath('//div[@class="list"]/article[not(@class="une")]/a/@href').extract()
        for url in urls1:
            yield Request(response.urljoin(url), callback=self.final_parse)


        # next_page_url = response.xpath('//*[@class="Pagination Pagination--more"]/a[contains(text(), "Suivante")]/@href').extract_first()
        #
        # if next_page_url:
        #     yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True)


    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['website_logo'] = 'https://en.location-etudiant.fr/images/logo.png'
        item['url'] = response.url
        item['description'] = response.xpath('//p[@itemprop="description"]/text()').extract_first()
        item['title'] = response.xpath('//h1[@itemprop="name"]/text()').extract_first()

        price = response.xpath('//div[@class="aPartirDe"]/span/text()').re(r'[\d.,]+')
        if price:
            try:
                price = ''.join(price)
                item['price'] = price.replace(',', '.')
            except:
                pass


        item['district'] = str(response.body).split('"postalCode":')[-1].split(',')[0].replace('"', '')
        item['city'] = str(response.body).split('"addressLocality":')[-1].split(',')[0].replace('"', '').strip().split(' ')[0]
        item['address'] = response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first()

        images = response.xpath('//div[@class="photoVignette"]/img/@src').extract()
        image_urls = []
        for img in images:
            img = 'https://www.location-etudiant.fr' + img.replace('h=81&w=81', 'h=410&w=525')
            image_urls.append(img)
        item['images'] = ','.join(image_urls)

        if 'location' in response.url:
            item['rent_buy'] = 'rent'
        else:
            item['rent_buy'] = 'buy'

        self.count += 1
        print("Total Count: " + str(self.count))

        yield item