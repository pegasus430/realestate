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
    name = "orpi"
    start_url = 'https://www.orpi.com/recherche/rent?realEstateTypes%5B%5D=maison&realEstateTypes%5B%5D=appartement&locations%5B%5D=paris&sort=date-down&layoutType=mixte'
    domain1 = 'https://www.orpi.com/'

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
        response.request.meta['proxy'] = proxy
        print ('err proxy: ' + proxy)
        yield Request(response.request.url,
                      callback=self.parse,
                      meta={'proxy': proxy},
                      dont_filter=True,
                      errback=self.errCall)

    def parse(self, response):
        dataInfos = json.loads(response.text.split('Orpi.saveResultsInSession(')[-1].split('], ')[0] + ']')
        for data in dataInfos:
            slug = data['slug']
            yield Request('https://www.orpi.com/annonce-location-' + slug, callback=self.final_parse)

            ##################_---------------- for test ----------------------##############
            # yield Request(response.urljoin(urls[0]), callback= self.final_parse, dont_filter=True)
            ###################################################################################

            main_url = 'https://www.orpi.com/recherche/rent?realEstateTypes%5B%5D=maison&realEstateTypes%5B1%5D=appartement&locations%5B0%5D=paris&sort=date-down&layoutType=mixte&page={}'
            next_count = response.meta["next_count"] + 1
            next_page_url = main_url.format(str(next_count))
            yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True, meta={"next_count": next_count})


    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['website_logo'] = 'https://www.orpi.com/mstile-310x310.png'
        item['url'] = response.url
        item['description'] = ''
        title = response.xpath('//div[@class="synopsis-textcell"]/h1/span//text()').extract()
        if title:
            title = ''.join(title)
            item['title'] = title

        price = response.xpath('//span[@class="price"]/text()').re(r'[\d.,]+')
        if price:
            try:
                price = ''.join(price)
                item['price'] = price.replace(',', '.')
            except:
                pass

        type1 = response.xpath('//span[@class="c-vignette__type"]/text()').extract_first()
        if type1:
            type1 = type1.split(' ')[0]
            if type1:
                item['type'] = type1

        addr = response.xpath('//span[@class="c-vignette__address"]/text()').extract_first()
        if addr:
            addr = addr.split(' ')
            item['city'] = addr[0]
            if len(addr) > 1:
                try:
                    item['district'] = int(addr[1])
                except:
                    pass

        images = response.xpath('//ul[@class="estate-carousel-nav-dots show-for-large js-estate-carousel-nav"]/li/img/@src').extract()
        if images:
            image_urls = ','.join(images)
            item['images'] = image_urls

        desc = response.xpath('//div[@class="estateNeighborhood gutters brd-rg estateDescription"]//div[@class="paragraphs-textcell"]/p/text()').extract_first()
        if desc:
            item['description'] = desc

        address = response.xpath('//address[@class="address"]/text()').extract_first()
        if address:
            address = address.split(' ')
            if len(address) > 1:
                item['city'] = address[0]
                item['district'] = address[1]
            elif len(address) == 1:
                item['city'] = address[0]

        characteristics_tds = response.xpath('//ul[@class="dotted-list dotted-list--ocom"]/li')
        for td in characteristics_tds:
            spans_strs = td.xpath('./mark[1]/text()').extract_first()
            if spans_strs:
                if 'Nombre de pièce(s)' in spans_strs:
                    pieces = td.xpath('./mark[2]/text()').extract_first()
                    if pieces:
                        pieces = pieces.strip()
                        item['pieces'] = pieces
                elif 'Surface' in spans_strs:
                    area = td.xpath('./mark[2]/text()').re(r'[\d.,]+')
                    if area:
                        area = area[0].replace(',', '.')
                        item['size'] = area
                elif 'Nombre de chambre(s)' in spans_strs:
                    rooms = td.xpath('./mark[2]/text()').re(r'[\d.,]+')
                    if rooms:
                        rooms = rooms[0]
                        item['rooms'] = rooms
                elif 'Année de construction' in spans_strs:
                    construction_year = td.xpath('./mark[2]/text()').extract_first()
                    if construction_year:
                        item['construction_year'] = construction_year
                elif 'Nombre d\'étages de l\'immeuble' in spans_strs:
                    total_floors = td.xpath('./mark[2]/text()').extract_first()
                    if total_floors:
                        total_floors = total_floors
                        item['toilettes'] = total_floors
                elif 'Nombre de salle(s) de bain/d’eau' in spans_strs:
                    bath_rooms = td.xpath('./mark[2]/text()').extract_first()
                    if bath_rooms:
                        bath_rooms = bath_rooms
                        item['bath_rooms'] = bath_rooms
                elif 'Étage' in spans_strs:
                    floors = td.xpath('./mark[2]/text()').extract_first()
                    if floors:
                        floors = floors[0]
                        item['floor'] = floors

        characteristics_tds = response.xpath('//div[@class="onusBlock onusBlock--ocom"]/ul/li')
        for td in characteristics_tds:
            spans_strs = td.xpath('./text()').extract_first()
            if spans_strs:
                if 'Dépôt' in spans_strs:
                    deposit = td.xpath('./text()').re(r'[\d.,]+')
                    if deposit:
                        deposit = ''.join(deposit)
                        item['deposit'] = deposit.replace(',', '.')
                elif 'Honoraires TTC à la charge du locataire' in spans_strs:
                    agency_fee = td.xpath('./text()').re(r'[\d.,]+')
                    if agency_fee:
                        agency_fee = ''.join(agency_fee)
                        item['agency_fee'] = agency_fee.replace(',', '.')
                elif 'd\'honoraires d\'état des lieux' in spans_strs:
                    other_agency_fee = td.xpath('./text()').re(r'[\d.,]+')
                    if other_agency_fee:
                        other_agency_fee = ''.join(other_agency_fee)
                        item['other_agency_fee'] = other_agency_fee.replace(',', '.')
                elif 'Provisions pour charges' in spans_strs:
                    other_charges = td.xpath('./text()').re(r'[\d.,]+')
                    if other_charges:
                        other_charges = ''.join(other_charges)
                        item['other_charges'] = other_charges.replace(',', '.')

        rent = "rent"
        item['rent_buy'] = rent

        self.count += 1
        print("Total Count: " + str(self.count))

        yield item