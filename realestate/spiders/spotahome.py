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
    name = "spotahome"
    start_url = 'https://www.spotahome.com/paris'
    domain1 = 'https://www.spotahome.com'

    use_selenium = False
    count = 0
    pageIndex = 1
    custom_settings = {
	    'CONCURRENT_REQUESTS': 1,
	    'DOWNLOAD_DELAY': 0.3,
	    'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
	    'CONCURRENT_REQUESTS_PER_IP': 1
	}

    sys.setdefaultencoding('utf-8')

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
        proxy = random.choice(self.list_proxy)
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
        n_list = []
        for i, t in enumerate(response.text.split('"rentableUnits":[{"id":')):
            if i == 0:
                continue
            n = t.split(',"adId":')[0]
            if n not in n_list:
                n_list.append(n)

        for n in n_list:
            url = 'https://www.spotahome.com/paris/for-rent:studios/{}'.format(n)
            time.sleep(0.3)
            yield Request(response.urljoin(url), callback=self.final_parse)

        urls = response.xpath('//div[@class="l-list__item"]/div/div/a/@href').extract()
        if len(urls) > 0:
            for url in urls:
                yield Request(response.urljoin(url), callback=self.final_parse)

            ##################_---------------- for test ----------------------##############
            # yield Request(response.urljoin(urls[0]), callback= self.final_parse, dont_filter=True)
            ###################################################################################

            next_count = response.meta['next_count'] + 1
            next_page_url = response.xpath('//a[@rel="next"]/@href').extract()
            if next_page_url:
                next_page_url = next_page_url[0]
                yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True, meta={"next_count": next_count})

    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['website_url'] = 'https://d26q4asbryw2nm.cloudfront.net/2390803/bundles/sahapp/favicon/largetile.png'
        item['url'] = response.url
        item['description'] = ''
        title = response.xpath('//div[@class="property-title-section"]/h1/text()').extract_first()
        if title:
            item['title'] = title

            price = response.xpath('//span[@class="rentable-unit-price"]/text()').re(r'[\d.,]+')
            if price:
                try:
                    price = ''.join(price)
                    item['price'] = price.replace(',', '.')
                except:
                    pass

            item['city'] = response.url.split('https://www.spotahome.com/')[-1].split('/')[0]

            district = response.xpath('//div[@class="property-title-section"]/h1/text()').re(r'[\d.,]+')
            if district:
                try:
                    item['district'] = int(district[-1].replace(',', ''))
                except:
                    pass
            addr = response.xpath('//section[@class="l-main-section l-property-main-section"]/div/div[@class="breadcrumb"]/span/text()').extract()
            if addr:
                item['address'] = addr[-1]

            avaiable_from = response.xpath('//div[@class="room--availability ga-detail-room-availability"]/text()').extract_first()
            if avaiable_from:
                avaiable_from = avaiable_from.split('Available: ')[-1]
                if avaiable_from:
                    avaiable_from = avaiable_from

            # addr = response.xpath('//div[@itemprop="address"]/p/text()').extract_first()
            # if addr:
            #     addr = addr.split(' ')
            #     item['city'] = addr[0]
            #
            #     district = response.xpath('//div[@itemprop="address"]/p/text()').re(r'[\d.,]+')
            #     if len(district) > 1:
            #         item['district'] = district[-1]

            images = response.xpath('//meta[@itemprop="image"]/@content').extract()
            if images:
                new_imgs = []
                for img in images:
                    img = img.strip()
                    if img:
                        new_imgs.append(img)
                if new_imgs:
                    item['images'] = ','.join(new_imgs)

            # area = response.xpath('//div[@class="left-panel"]//div[@class="btn btn-default btn-rounded btn-top-cover-default bold btn-shadow"]/text()').re(r'[\d.,]+')
            # if area:
            #     area = area[-1].replace(',', '.')
            #     item['size'] = area

            furnished = response.xpath('//div[@class="AvailableRoomFeatures"]/text()').extract_first()
            if furnished == 'Furnished':
                item['furnished'] = 1

            # temp = response.xpath('//div[@class="left-panel"]/p/text()').extract()
            # for t in temp:
            #     if 'Disponibilité' in t:
            #         avaiable_deposit = t.split(' ')[-1]

            descs = response.text.split('"description":"')
            if descs:
                new_desc = []
                for d in descs:
                    if d[:3] == '<p>':
                        d = d.split('"')[0]
                        d = d.strip().replace('</p>', '')
                        ds = d.split('<p>')
                        for dd in ds:
                            dd = dd.strip()
                            if dd:
                                new_desc.append(dd)
                        break
                if new_desc:
                    item['description'] = '\n'.join(new_desc)

            if 'Property type:' in response.text:
                type1 = response.text.split('Property type:')[-1].split('</li>')[0]
                if type1:
                    item['type'] = type1.strip()

            if 'Floor area:' in response.text:
                area = response.text.split('Floor area:')[-1].split('</li>')[0]
                if area:
                    area = re.findall('[\d.,]+', area)
                    if area:
                        area = area[0].replace(',', '.')
                        item['size'] = area
            if 'Floor:' in response.text:
                floor = response.text.split('Floor:')[-1].split('</li>')[0]
                if floor:
                    floor = re.findall('[\d.,]+', floor)
                    if floor:
                        floor = floor[0]
                        item['floor'] = floor
            if 'Number of bathrooms:' in response.text:
                bathrooms = response.text.split('Number of bathrooms:')[-1].split('</li>')[0]
                if bathrooms:
                    bathrooms = bathrooms.strip()

            self.count += 1
            print("Total Count: " + str(self.count))
            item['rent_buy'] = 'rent'
            yield item