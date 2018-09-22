# -*- coding: utf-8 -*-
from scrapy import Spider, Request, FormRequest
import sys
import re, os, requests, urllib
from scrapy.utils.response import open_in_browser
import time, datetime
from shutil import copyfile
import json, re, random
from realestate.items import RealestateItem

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

class selogerSpider(Spider):
    name = "pap"
    start_url = 'https://www.pap.fr/annonce/location-appartement-maison-paris-75-g439'
    domain1 = 'https://www.pap.fr'

    use_selenium = False
    count = 0
    pageIndex = 1

    # sys.setdefaultencoding('utf-8')

   # //////// angel headers and cookies////////////
    # --------------- Get list of proxy-----------------------#
    proxy_text = requests.get('https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt').text
    list_proxy_temp = proxy_text.split('\n')
    list_proxy = []
    for line in list_proxy_temp:
        if line.strip() !='' and (line.strip()[-1] == '+' or line.strip()[-1] == '-'):
            ip = line.strip().split(':')[0].replace(' ', '')
            port = line.split(':')[-1].split(' ')[0]
            list_proxy.append('http://'+ip+':'+port)

    def start_requests(self):
        # proxy = random.choice(self.list_proxy)
        yield Request(self.start_url, callback= self.parse, meta={"next_count": 1})

    # def errCall(self, response):
    #     ban_proxy = response.request.meta['proxy']
    #     self.list_proxy.remove(ban_proxy)
    #     proxy = random.choice(self.list_proxy)
    #     # response.request.meta['proxy'] = proxy
    #     print ('err proxy: ' + proxy)
    #     yield Request(response.request.url,
    #                   callback=self.parse,
    #                   meta={'proxy': proxy},
    #                   dont_filter=True,
    #                   errback=self.errCall)

    def parse(self, response):
        urls = response.xpath('//div[@class="search-list-item"]/div/a/@href').extract()
        if len(urls) > 0:
            for url in urls:
                yield Request(response.urljoin(url), callback=self.final_parse)

            ##################_---------------- for test ----------------------##############
            # yield Request(response.urljoin(urls[0]), callback= self.final_parse, dont_filter=True)
            ###################################################################################

            # next_count = response.meta['next_count'] + 1
            next_page_url = response.xpath('//li[@class="next"]/a/@href').extract_first()
            if next_page_url:
                yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True)

    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['website_logo'] = 'https://www.pap.fr/images/logos/logo-pap.png'
        item['url'] = response.url
        item['description'] = ''
        title = response.xpath('//h1[@class="item-title"]/span[@class="h1"]/text()').extract_first()
        if title:
            item['title'] = title

        price = response.xpath('//h1[@class="item-title"]/span[@class="item-price"]/text()').re(r'[\d.,]+')
        if price:
            try:
                price = ''.join(price)
                item['price'] = price.replace('.', '')
            except:
                pass
        temp = response.xpath('//a[@itemprop="item"]/span[@itemprop="name"]/text()').extract_first()
        t = temp.split(' ')[0]
        if t == 'Location':
            item['rent_buy'] = 'rent'
        type1 = temp.split(' ')[-1]
        if type1:
            type1 = type1.strip()
            if type1:
                item['type'] = type1

        characteristics_tds = response.xpath('//ul[@class="item-tags"]/li/strong')
        for td in characteristics_tds:
            spans_strs = td.xpath('./text()').extract_first()
            if spans_strs:
                if 'pièce' in spans_strs:
                    pieces = td.xpath('./text()').re(r'[\d.,]+')
                    if pieces:
                        pieces = pieces[0]
                        item['pieces'] = pieces
                elif 'm²' in spans_strs:
                    area = td.xpath('./text()').re(r'[\d.,]+')
                    if area:
                        area = area[0].replace(',', '.')
                        item['size'] = area
                elif 'chambre' in spans_strs:
                    rooms = td.xpath('./text()').re(r'[\d.,]+')
                    if rooms:
                        rooms = rooms[0]
                        item['rooms'] = rooms

        addr = response.xpath('//div[@class="item-description margin-bottom-30"]/h2/text()').extract_first()
        if addr:
            addr = addr.strip().split(' ')
            item['city'] = addr[0]

            district = response.xpath('//div[@class="item-description margin-bottom-30"]/h2/text()').re(r'[\d.,]+')
            if len(district) > 0:
                try:
                    item['district'] = int(district[-1])
                except:
                    pass

        images = response.xpath('//div[@class="owl-thumbs"]/a/img/@src').extract()
        if images:
            image_urls = ','.join(images)
            item['images'] = image_urls

        desc = response.xpath('//div[@class="margin-bottom-30"]/p/text()').extract()
        if desc:
            new_desc = []
            for d in desc:
                d = d.strip()
                if d:
                    new_desc.append(d)
            if new_desc:
                item['description'] = '\n'.join(new_desc)

        self.count += 1
        print("Total Count: " + str(self.count))

        yield item