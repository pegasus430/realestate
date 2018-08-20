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
    name = "lacartedescolocs"
    start_url = 'https://www.lacartedescolocs.fr/colocations/ile-de-france/paris'
    # start_json_url = 'https://www.lacartedescolocs.fr/listings/update_map_results?country=fr&filters%5Blocation%5D=Paris&filters%5Brent_max%5D=2000&filters%5BsortBy%5D=edited_at+DESC&viewport%5BneLat%5D=48.91453&viewport%5BneLon%5D=2.50104&viewport%5BswLat%5D=48.80317&viewport%5BswLon%5D=2.19308&viewport%5Bzoom%5D=12'
    start_json_url = 'https://www.lacartedescolocs.fr/listings/update_map_results?country=fr&filters%5Bdate_min%5D=-60&filters%5Blocation%5D=Paris&filters%5Brent_max%5D=2000&filters%5BsortBy%5D=edited_at+DESC&viewport%5BneLat%5D=48.93020&viewport%5BneLon%5D=2.51821&viewport%5BswLat%5D=48.78745&viewport%5BswLon%5D=2.17591&viewport%5Bzoom%5D=12'
    domain1 = 'https://www.lacartedescolocs.fr'

    use_selenium = False
    count = 0
    pageIndex = 1

    # sys.setdefaultencoding('utf-8')

   # //////// angel headers and cookies////////////
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
        yield Request(self.start_json_url, callback= self.parse, meta={"next_count": 1})

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
        json_data = json.loads(response.body)
        markers = json_data['markers']
        main_url = 'https://www.lacartedescolocs.fr/listings/show_listing?locale=fr&url_token={}'
        uts = []
        for m in markers:
            uts.append(m['ut'])
            yield Request(main_url.format(m['ut']), callback=self.final_parse, dont_filter=True)

    def final_parse(self, response):
        json_data = json.loads(response.body)
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['website_logo'] = 'https://dc0r5opm7495b.cloudfront.net/assets/logos/logo_white.fr-d5e56db342eda1a81e02b633d1a339a708e5ed1d823ffa8bdd16db6eab5cc405.png'
        item['url'] = json_data['full_url']
        desc = json_data['description']
        if desc:
            desc = desc.replace('<br/>', '\n')
        item['description'] = desc
        item['title'] = json_data['listing_title_string']
        item['price'] = json_data['cost_total_rent']
        item['size'] = json_data['lodging_surface']
        item['type'] = json_data['lodging_type_string']
        item['deposit'] = json_data['cost_caution']
        item['other_charges'] = json_data['cost_charges']
        item['city'] = json_data['address_city']
        address_list = [json_data['address_city']]
        if json_data['address_street']:
            address_list.append(json_data['address_street'])
        item['address'] = ' '.join(address_list)

        available_from = json_data['lodging_availability_string']

        pieces = re.findall('[\d.,]+', json_data['lodging_size_string'])
        if pieces:
            pieces = pieces[0]
            item['pieces'] = pieces

        imgs = json_data['pictures']
        images = []
        for img in imgs:
            if 'image_large' in img.keys():
                images.append(img['image_large'])
            elif 'image_medium' in img.keys():
                images.append(img['image_medium'])
        if images:
            image_urls = ','.join(images)
            item['images'] = image_urls

        item['rent_buy'] = 'rent'

        self.count += 1
        print("Total Count: " + str(self.count))

        yield item