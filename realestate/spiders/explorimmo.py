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
    name = "explorimmo"
    start_url = 'https://www.explorimmo.com/resultat/annonces.html?transaction=location&location=Paris&priceMax=&type=' \
                'maison%2Cvilla%2Cferme%2Cmoulin%2Cchalet&type=appartement%2Cchambre&type=atelier%2Cloft%2Cduplex&type' \
                '=hotel+particulier%2C+propriete%2Cchateau%2Cmanoir&roomMin=&fromSearchButton='
    domain1 = 'https://www.explorimmo.com'

    use_selenium = False
    count = 0
    pageIndex = 1

    sys.setdefaultencoding('utf-8')

    proxy_text = requests.get('https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt').text
    list_proxy_temp = proxy_text.split('\n')
    list_proxy = []
    for line in list_proxy_temp:
        if line.strip() != '' and (line.strip()[-1] == '+' or line.strip()[-1] == '-'):
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
        urls = response.xpath('//h2[@class="item-type js-item-title"]/a/@href').extract()
        if len(urls) > 0:
            proxy = response.meta['proxy']
            for url in urls:
                if '.html' in url:
                    yield Request(response.urljoin(url), callback=self.final_parse)

            yield Request(response.urljoin(urls[0]), callback= self.final_parse, dont_filter=True)

            main_url = '/annonces/resultat/annonces.html?transaction=location&type=Maison&type=Villa&type=Ferme&type=' \
                       'Moulin&type=Chalet&type=Appartement&type=Chambre&type=Atelier&type=Loft&type=Duplex&type=H%F4' \
                       'tel%20particulier&type=Propri%E9t%E9&type=Ch%E2teau&type=Manoir&location=paris&page={}'
            next_count = response.meta["next_count"] + 1
            next_page_url = main_url.format(next_count)
            yield Request(response.urljoin(next_page_url),
                          callback=self.parse,
                          dont_filter=True,
                          meta={"next_count": next_count})

    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['website_logo'] = 'https://header-figaroimmobilier.figarocms.com/img/logo-figimmo.4f72456.svg'
        item['url'] = response.url
        item['description'] = ''
        title = response.xpath('//div[@id="contenu"]/div/h1/text()').extract_first()
        if title:
            title = title.strip()
            item['title'] = title

        images = response.xpath('//div[@class="item js-img-popup"]/a/@href').extract()
        if images:
            image_urls = ','.join(images)
            item['images'] = image_urls

        location = response.xpath('//div[@id="contenu"]/div/h1/span/text()').extract_first()
        if location:
            location = location.strip()
            locations = location.split(' ')
            if len(locations) > 2:
                city = locations[1]
                district = locations[2].replace('me', '').replace('è', '').replace('er', '')
                item['city'] = city
                try:
                    item['district'] = int(district)
                except:
                    pass
            else:
                city = locations[1]
                item['city'] = city

        price = response.xpath('//div[@id="js-complements-infos"]//span[@class="price"]/text()').re(r'[\d.,]+')
        if price:
            try:
                price = ''.join(price)
                item['price'] = price.replace(',', '.')
            except:
                pass

        other_charges = response.xpath('//div[@id="js-complements-infos"]//span[@class="charges"]/text()').re(r'[\d.,]+')
        if other_charges:
            other_charges = ''.join(other_charges)
            item['other_charges'] = other_charges.replace(',', '.')

        deposit = response.xpath('//div[@id="js-complements-infos"]//span[@class="garantie"]/span[@class="value"]/text()').re(r'[\d.,]+')
        if deposit:
            deposit = ''.join(deposit)
            item['deposit'] = deposit.replace(',', '.')

        agency_fee = response.xpath('//div[@id="js-complements-infos"]//span[@class="honoraires"]/span[@class="value"]/text()').re(r'[\d.,]+')
        if agency_fee:
            agency_fee = ''.join(agency_fee)
            item['agency_fee'] = agency_fee.replace(',', '.')

        agency_name = response.xpath('//div[@class="container-agency-infos "]/span[@class="agency-name"]/text()').extract_first()
        if agency_name:
            agency_name = agency_name.strip()
            item['agency_name'] = agency_name

        agency_address_xpaths = response.xpath('//div[@class="agency-location"]')
        if agency_address_xpaths:
            agency_address_xpath = agency_address_xpaths[0]
            agency_address = agency_address_xpath.xpath('./text()').extract()
            new_agency_address = []
            for addr in agency_address:
                new_agency_address.append(addr.strip())
            if new_agency_address:
                item['agency_address'] = ' '.join(new_agency_address)

        ageny_logo = response.xpath('//a[@class="agencyInformation"]/img/@src').extract_first()
        if ageny_logo:
            item['agency_logo'] = ageny_logo

        descs = response.xpath('//p[@id="js-clicphone-description"]/text()').extract_first()
        if descs:
            descs = descs.strip()
            item['description'] = descs

        type1 = response.xpath('//div[@id="js-container-secondary-infos"]//ul[@class="unstyled flex"]/li/text()').extract()
        if type1:
            try:
                type1 = type1[1].strip()
                item['type'] = type1
            except:
                pass

        characteristics_tds = response.xpath('//div[@class="container-features"]/ul[@class="list-features"]/li')
        for td in characteristics_tds:
            spans_strs = td.xpath('./text()').extract_first()
            if spans_strs:
                if 'm²' in spans_strs:
                    area = td.xpath('./text()').re(r'[\d.,]+')
                    if area:
                        area = area[0].replace(',', '.')
                        item['size'] = area
                elif 'pièce' in spans_strs:
                    pieces = td.xpath('./text()').re(r'[\d.,]+')
                    if pieces:
                        pieces = pieces[0]
                        item['pieces'] = pieces
                elif 'chambre' in spans_strs:
                    rooms = td.xpath('./text()').re(r'[\d.,]+')
                    if rooms:
                        rooms = rooms[0]
                        item['rooms'] = rooms
                elif 'salle de bain' in spans_strs:
                    bath_rooms = td.xpath('./text()').re(r'[\d.,]+')
                    if bath_rooms:
                        bath_rooms = bath_rooms[0]
                        item['rooms'] = rooms
                elif 'Toilettes:' in spans_strs:
                    toilettes = td.xpath('./text()').re(r'[\d.,]+')
                    if toilettes:
                        toilettes = toilettes[0]
                        # item['toilettes'] = toilettes
                elif 'étage' in spans_strs:
                    floors = td.xpath('./text()').re(r'[\d.,]+')
                    if floors:
                        floors = floors[0]
                        item['floor'] = floors
                if 'Meublé' in spans_strs:
                    furnished = 1
                else:
                    furnished = 0
                    furnished = td.xpath('./text()').extract_first()
                    if furnished:
                        if 'Non' in furnished:
                            furnished = 0
                        else:
                            furnished = 1
                item['furnished'] = furnished

        rent = "rent"
        item['rent_buy'] = rent

        self.count += 1
        print("Total Count: " + str(self.count))

        yield item