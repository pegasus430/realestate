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
    name = "avendrealouer"
    start_url = 'https://www.avendrealouer.fr/recherche.html?pageIndex=1&sortPropertyName=ReleaseDate&' \
                'sortDirection=Descending&searchTypeID=2&typeGroupCategoryID=6&transactionId=2&localit' \
                'yIds=3-75&typeGroupIds=47,48#o=Home'
    domain1 = 'https://www.avendrealouer.fr'

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
        yield Request(self.start_url, callback= self.parse)

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
        urls = response.xpath('//ul[@id="result-list"]/li[@data-tranid="2"]/a/@href').extract()
        if len(urls) > 0:
            # proxy = response.meta['proxy']
            for url in urls:
                yield Request(response.urljoin(url), callback=self.final_parse)

            ##################_---------------- for test ----------------------##############
            # yield Request(response.urljoin(urls[0]), callback= self.final_parse, dont_filter=True)
            ###################################################################################

            next_page_url = response.xpath('//ul[@class="pagination"]/li/a[@class="next"]/@href').extract_first()
            if next_page_url:
                yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True)

    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['url'] = response.url
        item['description'] = ''

        title = response.xpath('//div[@class="fd-title"]/h1/span[@class="mainh1"]/text()').extract_first()
        if title:
            title = title.strip()
            item['title'] = title

        temp_data = title.split(' ')
        item['type'] = temp_data[1]
        try:
            item['district'] = int(re.findall('[\d]+', title.split('Paris')[-1])[-1])
        except:
            pass
        item['city'] = temp_data[len(temp_data) - 4]


        images = response.xpath('//div[@id="bxSliderContainer"]//img[contains(@id, "media")]/@src').extract()
        if images:
            image_urls = ','.join(images)
            item['images'] = image_urls

        price = response.xpath('//span[@id="fd-price-val"]/text()').re(r'[\d.,]+')
        if price:
            try:
                price = ''.join(price)
                item['price'] = price
            except:
                pass

        descs = response.xpath('//div[@id="propertyDesc"]/text()').extract_first()
        if descs:
            descs = descs.strip()
            item['description'] = descs

        item['furnished'] = 0
        characteristics_tds = response.xpath('//div[@class="property-description-characteristics"]/table//td')
        for td in characteristics_tds:
            spans_strs = td.xpath('./span/text()').extract()
            if len(spans_strs) > 1:
                if 'Surface:' in spans_strs[0]:
                    area = td.xpath('./span[2]/text()').re(r'[\d.,]+')
                    if area:
                        area = area[0]
                        item['size'] = area
                elif 'Pièce(s):' in spans_strs[0]:
                    pieces = td.xpath('./span[2]/text()').re(r'[\d.,]+')
                    if pieces:
                        pieces = pieces[0]
                        item['pieces'] = pieces
                elif 'Chambre(s):' in spans_strs[0]:
                    rooms = td.xpath('./span[2]/text()').re(r'[\d.,]+')
                    if rooms:
                        rooms = rooms[0]
                        item['rooms'] = rooms
                elif 'Salle(s)' in spans_strs[0]:
                    bath_rooms = td.xpath('./span[2]/text()').re(r'[\d.,]+')
                    if bath_rooms:
                        bath_rooms = bath_rooms[0]
                        # item['rooms'] = rooms
                elif 'Toilettes:' in spans_strs[0]:
                    toilettes = td.xpath('./span[2]/text()').re(r'[\d.,]+')
                    if toilettes:
                        toilettes = toilettes[0]
                        # item['toilettes'] = toilettes
                elif 'Nombre d\'étages:' in spans_strs[0]:
                    floors = td.xpath('./span[2]/text()').re(r'[\d.,]+')
                    if floors:
                        floors = floors[0]
                        item['floor'] = floors
                elif 'Construit en:' in spans_strs[0]:
                    construction_year = td.xpath('./span[2]/text()').extract_first()
                    if construction_year:
                        item['construction_year'] = construction_year
                elif 'Meublé' == spans_strs[0]:
                    item['furnished'] = 1

        pricing_data_spans = response.xpath('//div[@class="pricing-data"]/ul/li/span')
        for span in pricing_data_spans:
            spans_strs = span.xpath('./text()').extract_first()
            if spans_strs:
                if 'Loyer mensuel:' in spans_strs:
                    rent = span.xpath('./text()').re(r'[\d.,]+')
                    if rent:
                        rent = ''.join(rent)
                        # item['rent_price'] = rent
                elif 'Charges mensuelles:' in spans_strs:
                    other_charges = span.xpath('./text()').re(r'[\d.,]+')
                    if other_charges:
                        other_charges = ''.join(other_charges)
                        item['other_charges'] = other_charges
                elif 'Honoraires à la charge du locataire:' in spans_strs:
                    agency_fee = re.findall('[\d.,]+', spans_strs.split('(')[0])
                    if agency_fee:
                        agency_fee = ''.join(agency_fee)
                        item['agency_fee'] = agency_fee
                # elif 'Règlement des charges:' in spans_strs:
                #     other_agency_fee = re.findall('[\d.,]+', spans_strs.split('(')[0])
                #     if other_agency_fee:
                #         other_agency_fee = ''.join(other_agency_fee)
                #         item['other_agency_fee'] = other_agency_fee
                elif 'Dépôt de garantie:' in spans_strs:
                    deposit = re.findall('[\d.,]+', spans_strs.split('(')[0])
                    if deposit:
                        deposit = ''.join(deposit)
                        item['deposit'] = deposit
        agency_name = response.xpath('//div[@class="agency-title"]/span/@title').extract_first()
        if agency_name:
            item['agency_name'] = agency_name

        agency_address = response.xpath('//div[@class="agency-address"]/span/text()').extract_first()
        if agency_address:
            item['agency_address'] = agency_address
        agency_logo = response.xpath('//div[@class="agency-logo"]/img/@src').extract_first()
        if agency_logo:
            item['agency_logo'] = agency_logo

        rent = "buy"
        if 'location' in str(response.url):
            rent = "rent"
        item['rent_buy'] = rent

        self.count += 1
        print("Total Count: " + str(self.count))
        item['website_logo'] = 'https://www.avendrealouer.fr/Content/Default/Images/57x57-logoAVAL.png'
        yield item