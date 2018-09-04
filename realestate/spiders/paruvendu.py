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
    name = "paruvendu"
    start_url = 'https://www.paruvendu.fr/immobilier/annonceimmofo/liste/listeAnnonces?tt=5&tbApp=1&tbDup=1&tbChb=1&tbLof=1&tbAtl=1&tbPla=1&tbMai=1&tbVil=1&tbCha=1&tbPro=1&tbHot=1&tbMou=1&tbFer=1&at=1&nbp0=99&pa=FR&lo=75&lol=0&ray=50'
    domain1 = 'https://www.paruvendu.fr'

    use_selenium = False
    count = 0
    pageIndex = 1
    totalpage= None

    custom_settings = {
	    'CRAWLERA_ENABLED': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        "DOWNLOADER_MIDDLEWARES":{
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 400,
            'scrapy_crawlera.CrawleraMiddleware': 610,
            'random_useragent.RandomUserAgentMiddleware': None
        }
	}

    def start_requests(self):
        yield Request(self.start_url, callback= self.parse, meta={"next_count": 1})

    def parse(self, response):
        urls = response.xpath('//div[contains(@class,"ergov3-annonce")]/a[2]/@href').extract()
        for url in urls:
            yield Request(response.urljoin(url), callback=self.final_parse)

        next_page_url = response.xpath('//*[@class="pv15-pagsuiv flol"]/a[contains(text(), "Page suivante")]/@href').extract_first()

        if next_page_url:
            yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True)


    def final_parse(self, response):
        item = RealestateItem()

        item['online'] = 1
        item['website'] = self.name
        item['website_logo'] = 'https://static.paruvendu.fr/2018073108/communfo/img/structuresite/home/logoparuvendufr2016.png'
        item['url'] = response.url
        item['description'] = ''
        title = ' '.join(response.xpath('//h1[@class="auto2012_dettophead1txt1"]//text()').extract()).replace('\n', '').replace('\r', '').strip()
        item['title'] = title

        price = response.xpath('//div[@id="autoprix"]/text()').re(r'[\d.,]+')
        if price:
            try:
                price = ''.join(price)
                item['price'] = price.replace(',', '.')
            except:
                pass

        type1 = response.xpath('//h1[@class="auto2012_dettophead1txt1"]/span/text()').extract_first()
        type1 = response.url.split('/')[-3]
        item['type'] = type1

        addr_text = response.xpath('//h1[@class="auto2012_dettophead1txt1"]/text()').extract()[-1].strip()
        if addr_text:
            addr = addr_text.strip().split('\n')[-1].strip().split(' ')
            item['city'] = addr[0]

            district = re.findall(r'[\d]+', addr_text)
            if len(district) > 1:
                try:
                    item['district'] = int(district[-1])
                except:
                    pass

        images = response.xpath('//div[@class="imdet15-ConteneurMiniGlob"]//img/@src').extract()
        if images:
            imgs = []
            for img in images:
                img = img.replace('88x88', '1000x1000')
                imgs.append(img)
            image_urls = ','.join(imgs)
            item['images'] = image_urls

        # agency_fee = response.xpath('//span[@class="lbl-agencyfees"]/text()').re(r'[\d.,]+')
        # if agency_fee:
        #     agency_fee = ''.join(agency_fee)
        #     item['agency_fee'] = agency_fee.replace(',', '.')

        desc = ''.join(response.xpath('//div[@class="im12_txt_ann im12_txt_ann_auto"]/text()').extract()).strip()
        if desc != '':
            item['description'] = desc

        if addr_text:
            addr = addr_text.strip().split('\n')[0].strip().split(' ')
            size = re.findall(r'[\d.,]+', addr[0])
            if size:
                item['size'] = size[0]

        pieces = response.xpath('//h1[@class="auto2012_dettophead1txt1"]/strong/text()').re(r'[\d]+')
        if pieces:
            pieces = pieces[0]
            item['pieces'] = pieces

        options = response.xpath('//div[@class="im11_hd_det"]')
        for option in options:
            key = option.xpath('./span/text()').extract_first()
            if 'Dont charges/mois' in key:
                other_charges = option.xpath('./strong/text()').re(r'[\d.,]+')
                if other_charges:
                    item['other_charges'] = other_charges[0]
            elif 'Dépôt de garantie' in key:
                deposit = option.xpath('./strong/text()').re(r'[\d.,]+')
                if deposit:
                    item['deposit'] = ''.join(deposit)
            elif 'Honoraires' in key:
                agency_fee = option.xpath('./strong/text()').re(r'[\d.,]+')
                if agency_fee:
                    item['agency_fee'] = ''.join(agency_fee)

        agency_name = response.xpath('//div[@class="contact16-lheig"]/strong/text()').extract_first()
        if agency_name:
            item['agency_name'] = agency_name.strip().replace('\n', ' ')

        agency_logo = response.xpath('//div[@clas="im11_blc_visite_R"]/a/img/@src').extract_first()
        if agency_logo:
            item['agency_logo'] = agency_logo

        agency_address = response.xpath('//div[@class="contact16-lheig contact16-lname"]/span/text()').extract_first()
        if agency_address:
            item['agency_address'] = agency_address.strip()
        else:
            agency_address = response.xpath('//div[@class="contact16-adr"]/text()').extract()
            if agency_address:
                item['agency_address'] = '\n'.join(agency_address)

        li_attrs = response.xpath('//ul[@class="imdet15-infoscles"]/li')
        for li_attr in li_attrs:
            furnished = li_attr.xpath('./strong/text()').extract_first()
            if 'Meublé'== furnished :
                item['furnished'] = 1

        floors = response.xpath('//div[@class="im11_col_enr"]/dd/text()').extract()
        for text_floor in floors:
            if 'étage' in text_floor or 'Etage' in text_floor:
                item['rent_buy'] = re.findall(r'[\d]+', text_floor)[-1]

        if 'location' in response.url:
            item['rent_buy'] = 'rent'
        else:
            item['rent_buy'] = 'buy'

        self.count += 1
        print("Total Count: " + str(self.count))

        yield item