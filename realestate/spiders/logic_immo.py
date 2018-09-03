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
    name = "logic_immo"
    start_url = 'http://www.logic-immo.com/location-immobilier-paris-75,100_1' \
                '/options/groupprptypesids=1,2,6,7,12/order=update_date_desc'
    domain1 = 'http://www.logic-immo.com'

    use_selenium = False
    count = 0
    pageIndex = 1
    totalpage= None
    custom_settings = {
	    # 'CRAWLERA_ENABLED' : False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                      ' (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        "DOWNLOADER_MIDDLEWARES":{
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 400,
            'scrapy_crawlera.CrawleraMiddleware': 610,
            'random_useragent.RandomUserAgentMiddleware': None
        }
	}

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

    def errCall(self, response):
        ban_proxy = response.request.meta['proxy']
        self.list_proxy.remove(ban_proxy)
        proxy = random.choice(self.list_proxy)
        # response.request.meta['proxy'] = proxy
        print ('err proxy: ' + proxy)
        yield Request(response.request.url,
                      callback=self.parse,
                      meta={'proxy': proxy},
                      dont_filter=True,
                      errback=self.errCall)

    def parse(self, response):
        urls = response.xpath('//p[@class="offer-type"]/a/@href').extract()
        # if len(urls) > 0:
        for url in urls:
            if 'www.logic-immo.com' in url:
                yield Request(url, callback=self.final_parse)
                # yield Request('http://www.logic-immo.com/detail-location-b0673f77-1638-71da-8ae1-03cce29d8cdc.htm', self.final_parse)
                # break
            ##################_---------------- for test ----------------------##############
            # yield Request(response.urljoin(urls[0]), callback= self.final_parse, dont_filter=True)
            ###################################################################################

        next_count = response.meta['next_count']
        if not self.totalpage:
            next_page_url = response.xpath('//*[@class="btn btn-lightgrey jammer"]/@title').extract()
            self.totalpage = next_page_url[-1]

        if next_count < int(self.totalpage):
            next_count = next_count + 1
            if next_count == 2:
                url = self.start_url + '/page=2'
            else:
                url = response.url.split('/page=')[0] + '/page={}'.format(next_count)
            yield Request(url, callback=self.parse, dont_filter=True, meta={"next_count": next_count})


    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['url'] = response.url
        item['description'] = ''
        title = response.xpath('//table[@class="licom-breadcrumb"]//td/h1/text()').extract_first()
        if title:
            item['title'] = title

        price = response.xpath('//div[@itemprop="price"]/h2/text()').re(r'[\d.,]+')
        if price:
            try:
                price = ''.join(price)
                item['price'] = price.replace(',', '.')
            except:
                pass

        type1 = response.xpath('//div[@class="col-xs-3 offer-type"]/p/text()').extract_first()
        if type1:
            type1 = type1.strip()
            if type1:
                item['type'] = type1

        addr = response.xpath('//div[@itemprop="address"]/p/text()').extract_first()
        if addr:
            addr = addr.split(' ')
            item['city'] = addr[0]

            district = response.xpath('//div[@itemprop="address"]/p/text()').re(r'[\d]+')
            if len(district) > 1:
                try:
                    item['district'] = int(district[-1])
                except:
                    pass

        images = response.xpath('//div[@class="carousel-content noSlider"]//img/@src').extract()
        if images:
            image_urls = ','.join(images)
            item['images'] = image_urls

        agency_fee = response.xpath('//span[@class="lbl-agencyfees"]/text()').re(r'[\d.,]+')
        if agency_fee:
            agency_fee = ''.join(agency_fee)
            item['agency_fee'] = agency_fee.replace(',', '.')

        desc = response.xpath('//div[@class="offer-description-text"]/meta/@content').extract_first()
        if desc:
            item['description'] = desc

        area = response.xpath('//span[@class="offer-area-number"]/text()').re(r'[\d.,]+')
        if area:
            area = area[0].replace(',', '.')
            item['size'] = area

        pieces = response.xpath('//span[@class="offer-rooms-number"]/text()').re(r'[\d.,]+')
        if pieces:
            pieces = pieces[0]
            item['pieces'] = pieces

        other_charges = response.xpath('//span[@id="valueChargeRentProperty"]/text()').re(r'[\d.,]+')
        if other_charges:
            other_charges = ''.join(other_charges)
            item['other_charges'] = other_charges.replace(',', '.')

        deposit = response.xpath('//span[@id="valueDepotRentGarantee"]/text()').re(r'[\d.,]+')
        if deposit:
            deposit = ''.join(deposit)
            item['deposit'] = deposit.replace(',', '.')

        agency_fee = response.xpath('//span[@id="valueFeesRentAgency"]/text()').re(r'[\d.,]+')
        if agency_fee:
            agency_fee = ''.join(agency_fee)
            item['agency_fee'] = agency_fee.replace(',', '.')

        agency_name = response.xpath('//span[@itemprop="seller"]/text()').extract_first()
        if agency_name:
            item['agency_name'] = agency_name

        agency_address = response.xpath('//p[@class="agency-infos size_12 nomargin"]//span/text()').extract()
        if agency_address:
            item['agency_address'] = '\n'.join(agency_address)

        characteristics_tds = response.xpath('//ul[@itemprop="description"]/li')
        for td in characteristics_tds:
            spans_strs = td.xpath('./div[1]/text()').extract_first()
            if spans_strs:
                if 'Nombre d\'étages de l\'immeuble' in spans_strs:
                    total_floors = td.xpath('./div[2]/text()').extract_first()
                    if total_floors:
                        total_floors = total_floors
                        # item['toilettes'] = total_floors
                elif 'Nombre de salle de bain' in spans_strs:
                    bath_rooms = td.xpath('./div[2]/text()').extract_first()
                    if bath_rooms:
                        bath_rooms = bath_rooms
                        # item['bath_rooms'] = bath_rooms
                elif 'Etage du bien' in spans_strs:
                    floors = td.xpath('./div[2]/text()').extract_first()
                    if floors:
                        item['floor'] = floors.replace('e', '')
                elif 'Meublé' in spans_strs:
                    furnished = td.xpath('./div[2]/text()').extract_first()
                    if furnished == 'Oui':
                        item['furnished'] = 1

        t = response.xpath('//li[@class="columns current"]/a/span/text()').extract_first()
        if t == 'Location':
            item['rent_buy'] = 'rent'

        self.count += 1
        print("Total Count: " + str(self.count))

        yield item