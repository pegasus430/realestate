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
    name = "leboncoin"
    start_url = ['https://www.leboncoin.fr/recherche/?category=10&region=12&departement=75&real_estate_type=1,2',
                 'https://www.leboncoin.fr/colocations/offres/ile_de_france/paris/']
    domain1 = 'https://www.leboncoin.fr'

    use_selenium = False
    count = 0
    pageIndex = 1

    # sys.setdefaultencoding('utf-8')

   # //////// angel headers and cookies////////////
   #  headers = {
   #              'Cache-Control': 'max-age=0',
   #              'upgrade-insecure-requests': '1',
   #              'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
   #              'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
   #              'accept-encoding': 'gzip, deflate, br',
   #              'accept-language': 'en-US,en;q=0.9',
   #              'upgrade-insecure-requests': '1',
   #              'referer': 'https://www.tradecarview.com/my/favoritelist.aspx?list=1&sort=0&ps=25&&pn=0'
   #          }

    # --------------- Get list of proxy-----------------------#
    # proxy_text = requests.get('https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt').text
    # list_proxy_temp = proxy_text.split('\n')
    # list_proxy = []
    # for line in list_proxy_temp:
    #     if line.strip() !='' and (line.strip()[-1] == '+' or line.strip()[-1] == '-'):
    #         ip = line.strip().split(':')[0].replace(' ', '')
    #         port = line.split(':')[-1].split(' ')[0]
    #         list_proxy.append('http://'+ip+':'+port)

    def start_requests(self):
        # proxy = random.choice(self.list_proxy)
        for url in self.start_url:
            yield Request(url, callback= self.parse, meta={"main_url": url, "next_count": 1})

        ##################_---------------- for test ----------------------##############
        # yield Request(self.start_url[0], callback= self.parse, meta={"main_url": self.start_url[0], "next_count": 1})
        ###################################################################################

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
        urls = response.xpath('//ul/li[@class="_3DFQ-"]/a/@href').extract()
        if len(urls) > 0:
            # proxy = response.meta['proxy']
            for url in urls:
                yield Request(response.urljoin(url), callback=self.final_parse)

            main_url = response.meta["main_url"]
            next_count = response.meta["next_count"] + 1
            next_page_url = main_url + "p-{}/".format(next_count)
            # next_page_url = response.xpath('//li[@class="_2zwVR"]/a/@href').extract()[-1]
            yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True, meta={"main_url": main_url, "next_count": next_count})

    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['description'] = ''

        title = response.xpath('//h1[@class="_1KQme"]/text()').extract_first()
        if title:
            title = title.strip()
            item['title'] = title

        images = response.xpath('//div[@data-qa-id="adview_gallery_container"]//img/@src').extract_first()
        if images:
            item['images'] = images

        if 'colocations' in response.url:
            item['type'] = 'Appartement'
        else:
            item['type'] = response.xpath('//div[@data-qa-id="adview_price"]/span/text()').extract_first()
        item['url'] = response.url

        price = response.xpath('//div[@data-qa-id="adview_price"]/div/span/text()').extract_first()
        if price:
            try:
                price = float(price.replace(' ', ''))
                item['price'] = price
            except:
                pass

        date_added_str_list = response.xpath('//div[@data-qa-id="adview_date"]/text()').re('\d+')
        if len(date_added_str_list) > 3:
            year = int(date_added_str_list[2])
            month = int(date_added_str_list[1])
            day = int(date_added_str_list[0])
            hour = int(date_added_str_list[3])
            minute = int(date_added_str_list[4])

            item["date_added"] = datetime.datetime(year, month, day, hour, minute)
        elif len(date_added_str_list) > 0:
            year = int(date_added_str_list[2])
            month = int(date_added_str_list[1])
            day = int(date_added_str_list[0])

            item["date_added"] = datetime.datetime(year, month, day)

        type1 = response.xpath('//div[@data-qa-id="criteria_item_real_estate_type"]/div/div[@class="_3Jxf3"]/text()').extract_first()
        if type1:
            item['type'] = type1

        area = response.xpath('//div[@data-qa-id="criteria_item_square"]/div/div[@class="_3Jxf3"]/text()').re(r'[\d.,]+')
        if area:
            area = area[0]
            item['size'] = area

        rooms_count = response.xpath('//div[@data-qa-id="criteria_item_rooms"]/div/div[@class="_3Jxf3"]/text()').re(r'[\d.,]+')
        if rooms_count:
            rooms_count = rooms_count[0]
            item['pieces'] = rooms_count

        furnished = response.xpath('//div[@data-qa-id="criteria_item_furnished"]/div/div[@class="_3Jxf3"]/text()').extract_first()
        if furnished:
            if 'Non' in furnished:
                furnished = 0
            else:
                furnished = 1
            item['furnished'] = furnished

        descs = response.xpath('//div[@data-qa-id="adview_description_container"]/div/span[@class="_2wB1z"]/text()').extract()
        if descs:
            descs = '\n'.join(descs)
            item['description'] = descs

        locations = response.xpath('//div[@data-qa-id="adview_location_informations"]/span/text()').extract()
        if len(locations) > 1:
            city = locations[0]
            district = locations[-1]
            item['city'] = city
            try:
                item['district'] = int(district)
            except:
                pass

        if len(locations) > 0:
            city = locations[0]
            item['city'] = city
        rent = "buy"
        if 'location' in str(response.url):
            rent = "rent"
        item['rent_buy'] = rent

        self.count += 1
        print("Total Count: " + str(self.count))

        yield item