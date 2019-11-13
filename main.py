from scrapers.airbnbscrape import AirbnbSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())
process.crawl(AirbnbSpider)
process.start()
