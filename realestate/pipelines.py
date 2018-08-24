# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import MySQLdb, os,datetime
from scrapy import signals
import shutil

class RealestatePipeline(object):
    def __init__(self):
        #####-------------------- server side ------------------------- ####################
        self.conn = MySQLdb.connect(host='127.0.0.1', user='root', passwd='root', db='realstatedb', charset='utf8')
        # self.conn = MySQLdb.connect(host='127.0.0.1', user='root', passwd='vXZ3aR6DyhBbcENA', db='realstatedb',
        #                             charset='utf8')
        #####------------------------------------------------------------#############################

        #####-------------------- local test ------------------------- ####################
        # self.conn = MySQLdb.connect(host='127.0.0.1', user='root', passwd='kelong501', db='realestate', charset='utf8')
        #####------------------------------------------------------------#############################
        self.conn.ping(True)
        self.cursor = self.conn.cursor()
        self.files = {}
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        # query3 = "CREATE TABLE IF NOT EXISTS car_inform(" \
        #          "id int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,"\
        #          "car_name varchar(255) DEFAULT NULL,"\
        #         "price varchar(255) DEFAULT NULL,"\
        #         "ref_no varchar(255) DEFAULT NULL,"\
        #         "chassis text, model_code varchar(255) DEFAULT NULL,"\
        #         "engine_size varchar(255) DEFAULT NULL,"\
        #         "drive text,transmiss text,"\
        #         "location varchar(255) DEFAULT NULL,"\
        #         "version varchar(255) DEFAULT NULL,"\
        #         "mileage varchar(255) DEFAULT NULL,"\
        #         "engine_code varchar(255) DEFAULT NULL,"\
        #         "steering varchar(255) DEFAULT NULL,"\
        #         "color varchar(255) DEFAULT NULL,"\
        #         "disel_petrol varchar(255) DEFAULT NULL,"\
        #         "seats varchar(255) DEFAULT NULL,"\
        #         "doors varchar(255) DEFAULT NULL,"\
        #         "dimension varchar(255) DEFAULT NULL,"\
        #         "carCheck tinyint(1) DEFAULT 0,"\
        #         "date_added timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP)"\
                # "date_updated timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        try:
            # self.cursor.execute(query3)
            # self.conn.commit()
            # print ("Table products created successfully.")
            query= ""
            # spider_key = 'BF'
            # if spider.name == "tradecarview":
            #     spider_key = 'TCV'
            # elif spider.name == "flexnet":
            #     spider_key = 'FX'
            # elif spider.name == "fujicars":
            #     spider_key = 'FJ'

            # try:
            #     query = "SELECT * FROM listings Where website='{}'".format(spider.name)
            #     if spider.name == "flexnet":
            #         query = "SELECT ref_no FROM car_inform Where carCheck<>4 AND ref_no LIKE '{}%'".format(spider_key)
            #     result = self.cursor.execute(query)
            #     row = self.cursor.fetchone()
            #     existing_data_list = []
            #     while row is not None:
            #         existing_data_list.append(row[0])
            #         row = self.cursor.fetchone()
            #     path = "../scraperimages/"
            #     for name in os.listdir(path):
            #         if os.path.isdir(path + name) and not name in existing_data_list and spider_key in name:
            #             shutil.rmtree(path + name)
            # except:
            #     pass
            query = "UPDATE listings SET online=0 Where website='{}'".format(spider.name)
            # if spider.name == "flexnet":
            #     query = "DELETE FROM car_inform Where carCheck=4 AND ref_no LIKE '{}%'".format(spider_key)

            self.cursor.execute(query)
            self.conn.commit()
        except Exception as e:
            print ("MYSQL ERROR %d: %s" % (e.args[0], e.args[1]))


    def spider_closed(self, spider):
        pass

    def process_item(self, item, spider):
        try:
            query = "SELECT * FROM listings WHERE website='{}' AND description='{}'".format(item['website'], item['description'].replace("'", '´'))
            result = self.cursor.execute(query)
            if result > 0:
                key_txt = ','.join(item.keys())
                keys = key_txt.split(',')
                values = ""
                for i, val in enumerate(item.values()):
                    if isinstance(val,float) or isinstance(val,int):
                        val = str(val)
                    elif isinstance(val, datetime.datetime):
                        val = str(val)
                        val = "'" + val + "'"
                    else:
                        if val == None:
                            val = "''"
                        else:
                            val = "'" + val.replace("'", '´') + "'"
                    val = '{}={}'.format(keys[i], val)
                    values = values + ',' + val

                values = values[1:]
                query = "UPDATE listings SET {} WHERE website='{}' AND title='{}'".format(values, item['website'], item['title'].replace("'", '´'))
                result = self.cursor.execute(query)
                self.conn.commit()
                return item

            query = "SELECT * FROM listings WHERE description='{}'".format(item['description'].replace("'", '´'))
            result = self.cursor.execute(query)
            if result > 0:
                return item

            key_txt = ','.join(item.keys()).lower()
            values = ""
            for val in item.values():
                if isinstance(val,float) or isinstance(val,int):
                    val = str(val)
                elif isinstance(val, datetime.datetime):
                    val = str(val)
                    val = "'" + val + "'"
                else:
                    if val == None:
                        val = "''"
                    else:
                        try:
                            val = "'" + val.replace("'", '´') + "'"
                        except:
                            pass
                values = values + ',' + val
            values = values[1:]

            # values = str(','.join(item.values())).encode('utf-8')
            sql = "INSERT INTO listings (%s) VALUES (%s)"%(key_txt, values)
            self.cursor.execute(sql)
            self.conn.commit()
            return item
        except Exception as e:
            print ("MYSQL ERROR %d: %s" % (e.args[0], e.args[1]))
            return item
