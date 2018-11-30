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
    name = "fnaim"
    start_url = 'https://www.fnaim.fr/18-louer.htm?localites=%5B%7B%22label%22%3A%22PARIS+%2875%29%22%2C%22value%22%3A%22PARIS+%2875%29%22%2C%22id%22%3A%2275%22%2C%22type%22%3A%222%22%7D%5D&TYPE%5B%5D=1&TYPE%5B%5D=2&SURFACE_MIN=&PRIX_MAX=&idtf=18&TRANSACTION=2&submit=Rechercher'
    domain1 = 'https://www.fnaim.fr'

    use_selenium = False
    count = 0
    pageIndex = 1

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
        urls = response.xpath('//div[@class="tplAvecColonneDroite"]/ul/li[@class="item"]//a[@class="visuel"]/@href').extract()
        if len(urls) > 0:
            # proxy = response.meta['proxy']
            for url in urls:
                yield Request(response.urljoin(url), callback=self.final_parse)

            ##################_---------------- for test ----------------------##############
            # yield Request(response.urljoin(urls[0]), callback= self.final_parse, dont_filter=True)
            ###################################################################################

            next_tags = response.xpath('//div[@class="regletteNavigation"]/span/a')
            next_count = response.meta["next_count"] + 1
            next_exist = False
            for next_tag in next_tags:
                if next_exist:
                    break
                if str(next_count) == next_tag.xpath('./text()').extract_first():
                    next_page_url = next_tag.xpath('./@href').extract_first()
                    next_exist = True
                    yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True, meta={"next_count": next_count})


    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['website_logo'] = 'https://www.fnaim.fr/uploads/Image/6e/SIT_FNAIM_637_SIT_FNAIM_537_LOGOFNAIM-SSBASELINE-AGENCE.png'
        item['url'] = response.url
        item['description'] = ''
        title = response.xpath('//h1[@itemprop="name"]/text()').extract_first()
        if title:
            title = title.strip()
            item['title'] = title

        price = response.xpath('//span[@itemprop="price"]/text()').extract_first()
        if price:
            try:
                item['price'] = price.replace(',', '.').replace(' ', '')
            except:
                pass

        images = response.xpath('//div[@id="carousel"]//img/@src').extract()
        if images:
            image_urls = ','.join(images)
            item['images'] = image_urls

        temp_data = response.xpath('//p[@id="chemin"]/span//span[@itemprop="title"]/text()').extract()
        if temp_data:
            temp_data = temp_data[3]
            item['city'] = temp_data.split(' ')[0]
            district = temp_data.split(' ')[1]
            district = re.findall('[\d.,]+', district)
            district = ''.join(district)
            try:
                item['district'] = int(district)
            except:
                pass

        area = response.xpath('//li[@class="picto surface"]/b/text()').re(r'[\d.,]+')
        if area:
            area = area[0].replace(',', '.')
            item['size'] = area

        pieces = response.xpath('//li[@class="picto pieces"]/b/text()').re(r'[\d.,]+')
        if pieces:
            pieces = pieces[0]
            item['pieces'] = pieces

        agency_name = response.xpath('//div[@class="libelle"]/a/text()').extract_first()
        if agency_name:
            agency_name = agency_name.strip()
            item['agency_name'] = agency_name

        agency_address = response.xpath('//div[@class="coordonnees"]/p/text()').extract()
        if agency_address:
            new_agency_address = []
            for addr in agency_address:
                new_agency_address.append(addr.strip())
            if new_agency_address:
                item['agency_address'] = ' '.join(new_agency_address)
        item['agency_logo'] = response.xpath('//a[@class="visuel"]/img/@src').extract_first()
        # other_charges_tages = response.xpath('//div[@class="description"]/p/text()').re(r'[\d.,]+')
        # other_charges = response.xpath('//div[@class="description"]/p[@itemprop="description"]/text()').re(r'[\d.,]+')
        temps = response.xpath('//div[@class="description"]/p[not(@itemprop="description")]/text()').extract()
        if temps:
            for t in temps:
                if 'provision pour charges' in t:
                    other_charges = re.findall('[\d.,]+', t)
                    other_charges = ''.join(other_charges)
                    item['other_charges'] = other_charges.replace(',', '.')
                elif 'Honoraires charge locataire' in t:
                    agency_fee = re.findall('[\d.,]+', t)
                    agency_fee = ''.join(agency_fee)
                    item['agency_fee'] = agency_fee.replace(',', '.')
                elif 'Dépôt de garantie' in t:
                    deposit = re.findall('[\d.,]+', t)
                    deposit = ''.join(deposit)
                    item['deposit'] = deposit.replace(',', '.')

        descs = response.xpath('//div[@class="description"]/p[@itemprop="description"]/text()').extract_first()
        if descs:
            descs = descs.strip()
            item['description'] = descs

        characteristics_tds = response.xpath('//div[@class="caracteristique tab-left"]/ul/li')
        for td in characteristics_tds:
            spans_strs = td.xpath('./label/text()').extract_first()
            if spans_strs:
                if 'Type d’habitation' in spans_strs:
                    type1 = td.xpath('./text()').extract_first()
                    if type1:
                        type1 = type1.strip()
                        item['type'] = type1
                elif 'Surface habitable' in spans_strs:
                    area = td.xpath('./text()').re(r'[\d.,]+')
                    if area:
                        area = area[0].replace(',', '.')
                        item['size'] = area
                elif 'Meublé' in spans_strs:
                    furnished = td.xpath('./text()').extract_first()
                    if furnished:
                        if 'Oui' == furnished.strip():
                            furnished = 1
                        else:
                            furnished = 0
                        item['furnished'] = furnished
                elif 'chambre' in spans_strs:
                    rooms = td.xpath('./text()').re(r'[\d.,]+')
                    if rooms:
                        rooms = rooms[0]
                        item['rooms'] = rooms
                elif 'construction' in spans_strs:
                    construction_year = td.xpath('./text()').re(r'[\d.,]+')
                    if construction_year:
                        construction_year = construction_year[0]
                        item['construction_year'] = construction_year
                elif 'Nombre d’étages:' in spans_strs:
                    total_floors = td.xpath('./text()').re(r'[\d.,]+')
                    if total_floors:
                        total_floors = total_floors[0]
                        # item['toilettes'] = total_floors
                elif 'Étage' in spans_strs:
                    floors = td.xpath('./text()').re(r'[\d.,]+')
                    if floors:
                        floors = floors[0]
                        item['floor'] = floors


        rent = "rent"
        item['rent_buy'] = rent

        self.count += 1
        print("Total Count: " + str(self.count))

        yield item