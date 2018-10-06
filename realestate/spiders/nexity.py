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
from collections import OrderedDict

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

class selogerSpider(Spider):
    name = "nexity"
    start_url = 'https://www.nexity.fr/ws-rest/offre/biens/moteur.json?1=1&types_bien=Appartement,Maison/Villa&type_commercialisation=Location&pageNumber=1&pageSize=12&anciennete=0&locations=104&sortField=prix&sortOrder=asc&withPartners=1'
    domain1 = 'https://www.nexity.fr'

    use_selenium = False
    count = 0
    pageIndex = 1
    totalpage= None

    custom_settings = {
	    'CRAWLERA_ENABLED' : False,
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
        json_data = json.loads(response.body)
        for data in json_data['results']:
            try:
                item = RealestateItem()
                item['online'] = 1
                item['website'] = self.name
                item['website_logo'] = 'https://media2.nexity.fr/nfr2016/picto/nexity-logo.svg'
                item['url'] = 'https://www.nexity.fr/'+data['0']['url']
                item['pieces'] = data['0']['nb_piece']
                item['description'] = data['0']['description'].replace('<br>', '')
                item['title'] = data['0']['visuel_alt']

                if 'surface' in data['0'].keys():
                    item['size'] = data['0']['surface']

                if 'location' in item['url']:
                    item['rent_buy'] = 'rent'
                else:
                    item['rent_buy'] = 'buy'
                item['type'] = 'appartment'
                item['city'] = data['0']['ville'].lower()
                item['district'] = data['0']['code_postal']
                item['price'] = data['c_prix_min']
                imgs = []
                for img in data['0']['photos']:
                    imgs.append(img['direct'])
                item['images'] = ','.join(imgs)
                item['deposit'] = data['0']['depot_garantie']
                if 'etage' in data['0'].keys():
                    item['floor'] = data['0']['etage']

                if 'honoraires' in data['0'].keys() and data['0']['honoraires'] != 0:
                    item['agency_fee'] = int(data['0']['honoraires'])
                if 'honoraires_part_etat_des_lieux' in data['0'].keys() and data['0']['honoraires_part_etat_des_lieux'] != 0:
                    item['other_charges'] = int(data['0']['honoraires_part_etat_des_lieux'])
                    item['agency_fee'] = int(data['0']['honoraires']) - int(data['0']['honoraires_part_etat_des_lieux'])


                self.count += 1
                print("Total Count: " + str(self.count))
                yield item
            except Exception as e:
                print("err: " + e.args[0] )
                self.count += 1
                print("Total Count: " + str(self.count))
                yield item

        total = int(json_data['pagination']['pageCount'])
        current = int(json_data['pagination']['current'])
        if current < total:
            next = current+ 1
            next_page_url = 'https://www.nexity.fr/ws-rest/offre/biens/moteur.json?1=1&types_bien=Appartement,Maison/Villa&type_commercialisation=Location&pageNumber={}&pageSize=12&anciennete=0&locations=104&sortField=prix&sortOrder=asc&withPartners=1'.format(next)
            yield Request(next_page_url, self.parse)


