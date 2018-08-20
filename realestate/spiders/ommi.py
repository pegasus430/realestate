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

class ommiSpider(Spider):
    name = "ommi"
    start_url = 'https://www.ommi.fr/recherche/locations-paris-75-s4107978'
    domain1 = 'https://www.ommi.fr'

    use_selenium = False
    count = 0
    pageIndex = 1

    # sys.setdefaultencoding('utf-8')

   # //////// angel headers and cookies////////////
    headers = {
                'Cache-Control': 'max-age=0',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'en-US,en;q=0.9',
                'upgrade-insecure-requests': '1',
                'referer': 'https://www.tradecarview.com/my/favoritelist.aspx?list=1&sort=0&ps=25&&pn=0'
            }

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
        yield Request(self.start_url, callback= self.parse, headers=self.headers)

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
        urls = response.xpath('//*[@class="search-results"]/div/div/div/a[@target="_blank"]/@href').extract()
        if urls:
            # proxy = response.meta['proxy']
            for url in urls:
                yield Request(response.urljoin(url), callback=self.final_parse)

            next_page_url = response.xpath('//a[@class="btn btn-dark btn-page"]/i[@class="icon-right"]/parent::a/@href').extract_first()
            if next_page_url:
                # proxy = random.choice(self.list_proxy)
                yield Request(response.urljoin(next_page_url), callback=self.parse, dont_filter=True, errback=self.errCall)
        # else:
        #     proxy = random.choice(self.list_proxy)
        #     yield Request(response.url, callback=self.parse, dont_filter=True, meta={'proxy': proxy}, errback=self.errCall)

    def final_parse(self, response):
        item = RealestateItem()
        properties = ''
        try:
            properties = str(response.body).split('var __property = {};')[-1].split('__property.serverUrl')[0].split(';')
        except:
            return
        main_image = ''
        for prop in properties:
            if 'property.title' in prop:
                item['title']= prop.split('=')[-1].replace('\\', '').replace(';', '').strip()
            elif 'property.rooms' in prop:
                item['pieces'] = prop.split('=')[-1].replace(';', '').strip()
            elif 'property.description' in prop:
                item['description'] = prop.split('=')[-1].strip()[:-1].replace('\\\\', "\\").replace('"', '').encode('utf-8').decode('unicode-escape')
            elif 'property.description' in prop:
                item['description'] = prop.split('=')[-1].replace('\\', '').strip()[:-1]
            elif 'property.size' in prop:
                item['size'] = prop.split('=')[-1].replace('\\', '').replace(';', '').strip()
            elif 'property.loyer' in prop:
                item['price'] = prop.split('=')[-1].replace('\\', '').replace(';', '').strip()
            elif 'property.charges' in prop:
                item['other_charges'] = prop.split('=')[-1].replace('\\', '').replace(';', '').strip()
            # elif 'property.disponibilite' in prop:
            #     data = prop.split('=')[-1].replace('\\', '').replace(';', '').strip()
            #     if data !='':
            #         item['caf_avaliable'] = 1
            elif 'property.main_photo' in prop:
                main_image = prop.split('=')[-1].replace('\\', '').replace(';', '').strip()
            elif 'property.photos_all' in prop:
                datas = prop.split('=')[-1].replace('\\', '').replace(';', '').strip().replace(']', '').replace('[', '').replace('"', '')
                prifix = 'https://www.ommi.fr/image/by/w/900/h/900/i/' + main_image.replace(main_image.split('/')[-1], '').replace('/', '_').replace('"', '')
                images = []
                for img in datas.split(','):
                    image = prifix + img
                    images.append(image)
                item['images'] = ','.join(images)
            elif 'property.short_address' in prop:
                address = prop.split('=')[-1].replace('\\', '').replace(';', '').strip()
                if address and 'Paris' in address:
                    item['city'] = 'Paris'
                    # item['parisian_district'] = address.split(' ')[1].replace('er', '').replace('e', '').replace('"', '')
                    try:
                        item['district'] = int(address.split(' ')[1].replace('er', '').replace('e', '').replace('"', ''))
                    except:
                        try:
                            item['district'] = int(re.findall('[\d]+', address)[0])
                        except:
                            pass


        item['url'] = response.url
        title = response.xpath('//title/text()').extract_first()
        if title:
            item['title'] = title.split('-')[0].strip()

        type = response.url.split('/')[-1].split('-')[0]
        item['type'] = type
        rent = "rent"
        if 'achat' in str(response.url):
            rent = "buy"
        item['rent_buy'] = rent

        item['online'] = 1
        item['website'] = 'ommi'
        self.count += 1
        print (self.count)
        yield item


