from scrapers.airbnbscrape import AirbnbSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import json

f = open("/home/popdav/rista/airbnb_checker/scrapers/conf.json", "r")
data = f.read()
dataJson = json.loads(data)
f.close()

process = CrawlerProcess(get_project_settings())

for data in dataJson:
    process.crawl(AirbnbSpider, dataJson=data)

process.start()
