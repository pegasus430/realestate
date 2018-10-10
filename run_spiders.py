# -*- coding: utf-8 -*-
#!/usr/bin/python
from multiprocessing import Pool
import os, sys


def _crawl(spider_name_params=None):
	if spider_name_params:
		print (spider_name_params)
		print (">>>>> Starting {} spider".format(spider_name_params))
		file_name = 'output/{}_result.csv'.format(spider_name_params)
		os.remove(file_name)
		command = 'scrapy crawl {}'.format(spider_name_params)

		os.system(command)
		print ("finished.")
	return None

def run_crawler(spider_names):

	for spider_name in spider_names:
		pool = Pool(processes=5)
		pool.map(_crawl, [spider_name])

if __name__ == '__main__':
	spider_names = []
	if len(sys.argv) == 1:
		spider_names = ['seloger', 'avendrealouer', 'explorimmo', 'fnaim', 'leboncoin', 'orpi', 'century21', 'laforet', 'lesiteimmo', 'meilleursagents',
						'flatlooker', 'lacartedescolocs', 'logic_immo', 'ommi', 'pap', 'spotahome', 'bienici', 'foncia', 'location_etudiant', 'nexity', 'paruvendu']
	elif len(sys.argv) == 2:
		spider_names = [sys.argv[1]]
	run_crawler(spider_names)
