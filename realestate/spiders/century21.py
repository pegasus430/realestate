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
    name = "century21"
    start_url = 'https://www.century21.fr/annonces/location-maison-appartement/v-paris/s-0-/st-0-/b-0-/page-1/'
    domain1 = 'https://www.century21.fr/'

    use_selenium = False
    count = 0
    pageIndex = 1

    sys.setdefaultencoding('utf-8')

    proxy_text = requests.get('https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt').text
    list_proxy_temp = proxy_text.split('\n')
    list_proxy = []
    for line in list_proxy_temp:
        if line.strip() !='' and (line.strip()[-1] == '+' or line.strip()[-1] == '-'):
            ip = line.strip().split(':')[0].replace(' ', '')
            port = line.split(':')[-1].split(' ')[0]
            list_proxy.append('http://'+ip+':'+port)

    def start_requests(self):
        proxy = random.choice(self.list_proxy)
        yield Request(self.start_url, callback= self.parse, meta={"next_count": 1})

    def errCall(self, response):
        ban_proxy = response.request.meta['proxy']
        self.list_proxy.remove(ban_proxy)
        proxy = random.choice(self.list_proxy)
        response.request.meta['proxy'] = proxy
        print ('err proxy: ' + proxy)
        yield Request(response.request.url,
                      callback=self.parse,
                      meta={'proxy': proxy},
                      dont_filter=True,
                      errback=self.errCall)

    def parse(self, response):
        urls = response.xpath('//ul[@class="annoncesListeBien"]/li//div[@class="zone-photo-exclu"]/a/@href').extract()
        if urls:
            for url in urls:
                yield Request(response.urljoin(url), callback=self.final_parse)

            ##################_---------------- for test ----------------------##############
            yield Request(response.urljoin(urls[0]), callback= self.final_parse, dont_filter=True)
            ###################################################################################

            next_page_url = response.xpath('//li[@class="btnSUIV_PREC suivant"]/a/@href').extract_first()
            if next_page_url:
                yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True)


    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['website_logo'] = 'https://www.century21.fr/theme/generic/css/images/logo_century21-header.png'
        item['url'] = response.url
        item['description'] = ''
        title = response.xpath('//h1[@class="h1_page"]//text()').extract_first()
        if title:
            item['title'] = title

        price = response.xpath('//div[@id="focusAnnonceV2"]/section/span[@class="yellow"]/b/text()').re(r'[\d.,]+')
        if price:
            try:
                price = ''.join(price)
                item['price'] = price.replace(',', '.')
            except:
                pass

        images = response.xpath('//div[@class="zone-galerie"]/div/a//img/@src').extract()
        new_images = []
        if images:
            for img in images:
                new_images.append(response.urljoin(img))
            image_urls = ','.join(new_images)
            item['images'] = image_urls

        desc = response.xpath('//div[@class="desc-fr"]/p/text()').extract_first()
        if desc:
            item['description'] = desc.strip()

        address = title.split(' - ')
        if address:
            item['city'] = address[len(address) - 3]
            try:
                item['district'] = int(address[len(address) - 2])
            except:
                pass

        characteristics_tds = response.xpath('//div[@class="col-gauche-slide"]/div/ul/li')
        item['furnished'] = 0
        for td in characteristics_tds:
            spans_strs = ''.join(td.xpath('./span/text()').extract())
            if spans_strs:
                if 'Location meublée' in spans_strs:
                    item['furnished'] = 1
                elif 'Nombre de pièces' in spans_strs:
                    pieces = td.xpath('./text()').extract_first()
                    if pieces:
                        pieces = pieces.strip()
                        item['pieces'] = pieces
                elif 'Type d\'appartement' in spans_strs:
                    pieces = td.xpath('./text()').extract_first()
                    if pieces:
                        pieces = pieces.strip()
                        item['pieces'] = pieces
                elif 'Surface totale' in spans_strs:
                    area = td.xpath('./text()').re(r'[\d.,]+')
                    if area:
                        area = area[0].replace(',', '.')
                        item['size'] = area
                elif 'Année construction' in spans_strs:
                    construction_year = td.xpath('./text()').re(r'[\d.,]+')
                    if construction_year:
                        construction_year =  construction_year[0]
                        item['construction_year'] = construction_year
                elif 'Honoraires charge locataire' in spans_strs:
                    agency_fee = td.xpath('./text()').re(r'[\d.,]+')
                    if agency_fee:
                        agency_fee = agency_fee[0].replace(',', '.')
                        item['agency_fee'] = agency_fee
                elif 'Dépôt de garantie' in spans_strs:
                    deposit = td.xpath('./text()').re(r'[\d.,]+')
                    if deposit:
                        deposit = deposit[0].replace(',', '.')
                        item['deposit'] = deposit
                elif 'Détail du loyer' in spans_strs:
                    other_charges = td.xpath('./ul/li/text()').re(r'[\d.,]+')
                    if other_charges:
                        other_charges = other_charges[0].replace(',', '.')
                        item['other_charges'] = other_charges

        rent = "buy"
        tt = response.xpath('//div[@id="filAriane"]//span[@itemprop="title"]/text()').extract()
        if 'Location Appartement' in tt:
            item['type'] = 'Appartement'
        if 'Location' in tt:
            rent = 'rent'
        item['rent_buy'] = rent

        self.count += 1
        print("Total Count: " + str(self.count))

        yield item