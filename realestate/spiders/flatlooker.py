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
    name = "flatlooker"
    start_url = 'https://www.flatlooker.com/appartements?utf8=%E2%9C%93&min_latitude=48.815573&min_longitude=2.2241989999999987&max_latitude=48.9021449&max_longitude=2.4699207999999544&zoom=12&move_search=true&lieu=Paris%2C+France&surface_min=&prix_max='
    domain1 = 'https://www.flatlooker.com'

    use_selenium = False
    count = 0
    pageIndex = 1

    sys.setdefaultencoding('utf-8')

    # proxy_text = requests.get('https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt').text
    # list_proxy_temp = proxy_text.split('\n')
    # list_proxy = []
    # for line in list_proxy_temp:
    #     if line.strip() != '' and (line.strip()[-1] == '+' or line.strip()[-1] == '-'):
    #         ip = line.strip().split(':')[0].replace(' ', '')
    #         port = line.split(':')[-1].split(' ')[0]
    #         list_proxy.append('http://'+ip+':'+port)

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
        urls = response.xpath('//div[@class="col-sm-6 col-md-6 col-lg-4"]//div[@class="photo_container"]/a/@href').extract()
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
        item['url'] = response.url
        item['description'] = ''
        title = response.xpath('//div[@class="col-md-8 hidden-xs hidden-sm"]/h3/text()').extract_first()
        if title:
            item['title'] = title

            temp = response.xpath('head/title/text()').extract_first()
            if temp:
                try:
                    temp = temp.split(' - ')
                    price = temp[-1]
                    price = re.findall('[\d.,]+', price)
                    price = ''.join(price)
                    item['price'] = price.replace(',', '.')
                    item['city'] = temp[len(temp) - 2]
                    item['district'] = int(temp[len(temp) - 3])
                except:
                    pass

            type1 = response.url.replace('https://www.flatlooker.com/', '').split('/')[0]
            if type1:
                if 'appartement' in type1:
                    item['type'] = 'appartement'
                else:
                    item['type'] = type1

            # addr = response.xpath('//div[@itemprop="address"]/p/text()').extract_first()
            # if addr:
            #     addr = addr.split(' ')
            #     item['city'] = addr[0]
            #
            #     district = response.xpath('//div[@itemprop="address"]/p/text()').re(r'[\d.,]+')
            #     if len(district) > 1:
            #         item['district'] = district[-1]

            images = response.xpath('body/div[@class="container-fluid"]/img/@src').extract()
            if images:
                image_urls = ','.join(images)
                item['images'] = image_urls

            addr = response.xpath('//div[@class="left-panel"]/h4[@class="orange bold"]/text()').extract_first()
            if addr:
                item['address'] = addr.strip()

            area = response.xpath('//div[@class="left-panel"]//div[@class="btn btn-default btn-rounded btn-top-cover-default bold btn-shadow"]/text()').re(r'[\d.,]+')
            if area:
                pe = area[0]
                item['pieces'] = pe
                area = area[-1].replace(',', '.')
                item['size'] = area

            furnished = response.xpath('//div[@class="left-panel"]/div[@class="flex-vcenter"]/p/text()').extract_first()
            if 'Non' in furnished:
                item['furnished'] = 0
            else:
                item['furnished'] = 1

            temp = response.xpath('//div[@class="left-panel"]/p/text()').extract()
            for t in temp:
                if 'Disponibilité' in t:
                    avaiable_deposit = t.split(' ')[-1]

            descs = response.xpath('//div[@id="annonce"]/div[2]//div[@class="block-with-text"]//text()').extract()
            if descs:
                new_desc = []
                for d in descs:
                    d = d.strip()
                    if d:
                        new_desc.append(d)
                if new_desc:
                    item['description'] = '\n'.join(new_desc)



            # other_charges = response.xpath('//span[@id="valueChargeRentProperty"]/text()').re(r'[\d.,]+')
            # if other_charges:
            #     other_charges = ''.join(other_charges)
            #     item['other_charges'] = other_charges.replace(',', '.')

            temp = response.xpath('//table[@id="table-essentials"]//tr')
            for t in temp:
                strs = t.xpath('./td/text()').extract()
                if '\nDépôt de garantie\n' in strs:
                    deposit = strs[1]
                    if deposit and deposit.strip():
                        deposit = deposit.strip()
                        deposit = re.findall('[\d.,]+', deposit)
                        deposit = ''.join(deposit)
                        item['deposit'] = deposit
                elif '\nHonoraires de location\n' in strs:
                    agency_fee = strs[1]
                    if agency_fee and agency_fee.strip():
                        agency_fee = agency_fee.strip()
                        agency_fee = re.findall('[\d.,]+', agency_fee)
                        agency_fee = ''.join(agency_fee)
                        item['agency_fee'] = agency_fee

            temp = response.xpath('//table[@id="table-mesure"]/tbody//td/text()').extract()
            for i, t in enumerate(temp):
                strs = t
                if 'Étage' in strs:
                    floor = temp[i + 1]
                    if floor and floor.strip():
                        floor = floor.strip()
                        floor = re.findall('[\d.,]+', floor)
                        floor = floor[0]
                        item['floor'] = floor

            if 'Location' in title:
                item['rent_buy'] = 'rent'
            self.count += 1
            print("Total Count: " + str(self.count))

            yield item