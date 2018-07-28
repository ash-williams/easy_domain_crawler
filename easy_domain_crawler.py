"""
	EASY DOMAIN CRAWLER FOR MONGODB
	
	This simple crawler starts with a seed page and will continuously crawl pages linked to from this seed page as long as the pages are within the same top level domain. It writes the output to a Mongo database.
	
	To use:
		import easy_domain_crawler
		easy_domain_crawler.crawl(seed_page, db_url, db_client)
	
	Where the seed_page variable is the url you want to begin crawling (for example, when crawling a blog, you'd probably want to use the sites 'archive' page), the optional db_url variable is the url to your mongo instance (defaulted to mongodb://localhost:27017) and the optional db_client variable is the name of the database within mongo that you want to use (defaulted to 'crawler_results').
	
	Because state is persisted to a DB, any crash can be recovered from by simply just starting the server up again.
		
	WARNING: This crawler does not take into account the robots.txt file. 
	
	Future work/additions: 
		- currently if a 404 response is given, the crawler moves onto the next link and continues. This isn't ideal if, for example, the internet connection temporarily drops. Some handling of this would be nice.
	
	Author: Ashley Williams, 29th July 2018
"""
import sys
from pymongo import MongoClient
from bs4 import BeautifulSoup
from urllib.parse import urlparse



def getDB(db_url, db_client):
	""" returns a db object """
	try:
		client = MongoClient(db_url)
		db = client[db_client]
	except Exception as e:
		print(e)
		sys.exit()
	else:
		return db
		
		

def get_all_links(url, SEED_DOMAIN):
	""" 
		Get all links from the same domain and returns as a list
	"""
	html = um.get_html(url)
	soup = BeautifulSoup(html, "html5lib")
	all_urls = []
		
	try:
		for link in soup.find_all('a'):
			#print(link)
			all_urls.append(link.get('href'))
	except Exception as e:
		print(e)
		
	result_urls = []
	
	for url in all_urls:
		domain = urlparse(url).netloc
		
		if domain == SEED_DOMAIN:
			result_urls.append(url)
	
	return result_urls, html
	

	
	
def crawl(seed_page, db_url="mongodb://localhost:27017", db_client="crawler_results"):
	"""
	The main method to be run.
	"""
	DB = getDB(db_url, db_client)
	SEED_DOMAIN = urlparse(seed_page).netloc
			
	DB.to_crawl.insert_one({"url": seed_page})
	
	flag = True
	
	while flag:
		print()
		print("To crawl: " + str(DB.to_crawl.count()))
		print("Crawled: " + str(DB.crawled_links.count()))
		print()
		if DB.to_crawl.count() != 0:
			link = DB.to_crawl.find()[0]		
			url = link['url']
			
			DB.to_crawl.remove({"url": url})
			
			all_links, html = get_all_links(url, SEED_DOMAIN)
			
			for u in all_links:
				exists = DB.to_crawl.find({"url": u})
				crawled = DB.crawled_links.find({"url": u})
				if exists.count() == 0 and crawled.count == 0:
					DB.to_crawl.insert_one({"url": u})
			
			exists = DB.crawled_links.find({"url": url})
			if exists.count() == 0:
				DB.crawled_links.insert_one({"url":url})
				DB.pages.insert_one({"url":url, "html": html})
		else:
			flag = False
	
	print("Finished")
	
	