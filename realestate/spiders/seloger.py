# -*- coding: utf-8 -*-
from scrapy import Spider, Request, FormRequest
import sys
import re, os, requests, urllib
from scrapy.utils.response import open_in_browser
import time
from shutil import copyfile
import json, re, random
from realestate.items import RealestateItem

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
# def download(url, destfilename, temppath):
#     filename = temppath+'tmp'
#     if not os.path.exists(destfilename):
#         print "Downloading from {} to {}...".format(url, filename)
#         try:
#             r = requests.get(url, stream=True)
#             with open(filename, 'wb') as f:
#                 for chunk in r.iter_content(chunk_size=1024):
#                     if chunk:
#                         f.write(chunk)
#                         f.flush()
#
#             with Image.open(filename) as image:
#                 cover = resizeimage.resize_cover(image, [640, 430])
#                 cover.save(destfilename, image.format)
#             os.remove(filename)
#         except Exception as e:
#             print(e)
#             print "Error downloading file."

class selogerSpider(Spider):
    name = "seloger"
    start_url = 'https://www.seloger.com/list.htm?tri=initial&idtypebien=2,1&idtt=1&naturebien=1,2,4&cp=75'
    domain1 = 'https://www.seloger.com'

    use_selenium = False
    count = 0
    pageIndex = 1

    handle_httpstatus_list = [407]

    # sys.setdefaultencoding('utf-8')

   # # //////// angel headers and cookies////////////
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
        yield Request(self.start_url, callback= self.parse)

    def errCall(self, response):
        ban_proxy = response.request.meta['proxy']
        self.list_proxy.remove(ban_proxy)
        proxy = random.choice(self.list_proxy)
        # response.request.meta['proxy'] = proxy
        print ('err proxy: ' + proxy)
        yield Request(response.request.meta['url'],
                      callback=self.parse,
                      meta={'proxy': proxy, 'url':response.request.meta['url']},
                      dont_filter=True,
                      errback=self.errCall)

    def parse(self, response):
        urls = response.xpath('//*[@class="c-pa-link link_AB"]/@href').extract()
        # if urls:
        #     proxy = response.meta['proxy']
        for url in urls:
            yield Request(url, callback=self.final_parse, dont_filter=True)

        next_page_url = response.xpath('//*[@title="Page suivante"]/@href').extract_first()
        if next_page_url:
            # proxy = random.choice(self.list_proxy)
            yield Request(next_page_url, callback=self.parse, dont_filter=True)
        # else:
        #     proxy = random.choice(self.list_proxy)
        #     url = response.meta['url']
        #     yield Request(url, callback=self.parse, dont_filter=True, meta={'proxy': proxy, 'url': url}, errback=self.errCall)

    def errProduct(self, response):
        # ban_proxy = response.request.meta['proxy']
        # self.list_proxy.remove(ban_proxy)
        proxy = random.choice(self.list_proxy)
        # response.request.meta['proxy'] = proxy
        # print ('err product proxy: ' + proxy)
        yield Request(response.request.url,
                      callback=self.final_parse,
                      meta={'proxy': proxy},
                      dont_filter=True,
                      errback=self.errProduct)
    def final_parse(self, response):
        item = RealestateItem()
        title= response.xpath('//h1[@class="detail-title title1"]/text()').extract_first()
        if title:
            title = title.strip()
        item['title'] = title

        item['type'] = response.xpath('//h2[@class="c-h2"]/text()').extract_first()
        item['url'] = response.url

        rent = "rent"
        if 'achat' in str(response.url):
            rent = "buy"
        item['rent_buy'] = rent

        # price = response.xpath('//a[@class="js-smooth-scroll-link price"]/text()').extract_first()
        # if price:
        #     price = price.strip().replace('\xa0', '').replace('€', '').replace(' ', '').strip()
        #     item['price'] = float(price)
        # else:
        #     item['price'] = None

        rooms= 0
        pieces= 0
        size= 0

        details= response.xpath('//ul[@class="criterion"]/li')
        for detail_li in details:
            detail = detail_li.xpath('./text()').extract_first()
            if 'pièce' in detail:
                pieces= detail.split(" ")[0]
            if 'chambre' in detail:
                rooms= detail.split(" ")[0]
            if 'm²' in detail:
                size= detail.split(" ")[0].replace(",", ".")
        item['rooms'] = rooms
        item['pieces'] = pieces
        item['size'] = size

        location = response.xpath('//p[@class="localite"]/text()').extract_first()
        if location and 'Paris' in location:
            city= 'Paris'
            parisian_district= location.split(' ')[1].replace('ème', '')
        else:
            city= location
            parisian_district = None
        item['city'] = city
        # item['parisian_district'] = parisian_district
        try:
            item['district'] = int(parisian_district)
        except:
            pass

        agency_name= response.xpath('//a[@class="agence-link"]/@title').extract_first()
        item['agency_name'] = agency_name
        try:
            agency_address= response.xpath('//div[@class="agence-adresse fi fi-map-pin"]/text()').extract_first().strip()
        except:
            agency_address= None
        item['agency_address'] = agency_address

        agency_phone= response.xpath('//a[@class="bub-phone tagClick"]/@data-phone').extract_first()
        item['agency_phone'] = agency_phone
        try:
            agency_postal_code= [i for i in agency_address.split(" ") if RepresentsInt(i)][0]
        except:
            agency_postal_code= None
        item['agency_postal_code'] = agency_postal_code
        item['agency_logo'] = response.xpath('//img[@class="agence-logo-img"]/@src').extract_first()
        images= response.xpath('//div[contains(@class, "carrousel_slide")]/div/@data-lazy').extract()
        pic = []
        for img_data in images:
            picture = json.loads(img_data)['url'].replace("//", "")
            pic.append(picture)

        images1= response.xpath('//div[contains(@class, "carrousel_slide")]/img/@src').extract()
        for img_data in images1:
            pic.append(img_data)
        pics = ",".join(pic)




        charges_val_keys = response.xpath('//*[@class="categorie with-padding-bottom"]//p/text()').extract()
        charges_val_texts = response.xpath('//*[@class="categorie with-padding-bottom"]//p/span/text()').extract()

        item['images'] = pics
        item['online'] = 1
        item['website'] = 'seloger'
        item['website_logo'] = 'https://static-seloger.com/z/produits/sl/homepage/assets/img/bandeau_app/sl_logo_152x152_thumb.png'

        id = str(response.url).split('/')[-1].split('.')[0]
        if id:
            url = 'https://www.seloger.com/detail,json,caracteristique_bien.json?idannonce=' + id

            # proxy = response.meta['proxy']
            yield Request(url, callback=self.final_attr, meta={'item':item}, dont_filter=True)

    def errCallJson(self, response):
        # ban_proxy = response.request.meta['proxy']
        # self.list_proxy.remove(ban_proxy)
        proxy = random.choice(self.list_proxy)
        # response.request.meta['proxy'] = proxy
        print ('err product proxy: ' + proxy)
        yield Request(response.request.url,
                      callback=self.final_attr,
                      meta={'proxy': proxy, 'item':response.request.meta['item']},
                      dont_filter=True,
                      errback=self.errCallJson)

    def final_attr(self, response):
        item = response.meta['item']

        try:
            floor = None
            construction_year = None
            bathroom = None
            toilet = None
            json_data = json.loads(response.body)
            for category in json_data['categories']:
                if category['name']== 'Général':
                    for order in category["criteria"]:
                        if order['order']== 2096:
                            floor= order['value'].split(" ")[1].replace("ème", "")
                            if 'rez-de-chaussée' in floor:
                                floor= 0
                            if '1er' in str(floor):
                                floor= 1
                        elif order['order']== 2092:
                            construction_year= order['value'].split(" ")[-1]

                elif 'intérieur' in category['name']:
                    for order in category["criteria"]:
                        if order['order']== 2175:
                            bathroom= order['value'].split(" ")[0]
                        elif order['order']== 2180:
                            toilet= order['value'].split(" ")[0]

            item['floor'] = floor
            item['construction_year'] = construction_year
            item['price'] = json_data["infos_acquereur"]["prix"]["prix"]
            try:
                complement_loyer= json_data["infos_acquereur"]["prix"]["complement_loyer"]
                item['other_charges'] = complement_loyer
            except KeyError:
                item['other_charges'] = 0

            try:
                other_charges= json_data["infos_acquereur"]["prix"]["charges_forfaitaires"]
                item['other_charges'] = other_charges
            except KeyError:
                other_charges= 0


            try:
                agency_fee= json_data["infos_acquereur"]["prix"]["honoraires_locataires"]
            except KeyError:
                agency_fee= 0
            item['agency_fee'] = agency_fee

            # try:
            #     other_agency_fee= json_data["infos_acquereur"]["prix"]["honoraires_edl"]
            # except KeyError:
            #     other_agency_fee= 0
            # item['other_agency_fee'] = other_agency_fee

            try:
                deposit= json_data["infos_acquereur"]["prix"]["garantie"]
            except KeyError:
                deposit= 0
            item['deposit'] = deposit
            item['description'] = json_data['descriptif'].replace("'", '´')

            if item['title'] and item['title'] !='':
                self.count += 1
                print (self.count)
                yield item
            else:
                print('no title')
        except:
            if item['title'] and item['title'] !='':
                self.count += 1
                print (self.count)
                yield item
