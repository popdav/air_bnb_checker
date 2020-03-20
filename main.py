from scrapers.airbnbscrape import AirbnbSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import json

f = open("./scrapers/conf.json", "r")
data = f.read()
dataJson = json.loads(data)
f.close()

s = get_project_settings()
s['USER_AGENTS'] = [
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/57.0.2987.110 '
     'Safari/537.36'),  # chrome
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/61.0.3163.79 '
     'Safari/537.36'),  # chrome
    ('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) '
     'Gecko/20100101 '
     'Firefox/55.0'),  # firefox
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/61.0.3163.91 '
     'Safari/537.36'),  # chrome
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/62.0.3202.89 '
     'Safari/537.36'),  # chrome
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/63.0.3239.108 '
     'Safari/537.36'),  # chrome
]
s['DOWNLOAD_DELAY'] = 1
s['DOWNLOADER_MIDDLEWARES'] = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_useragents.downloadermiddlewares.useragents.UserAgentsMiddleware': 500,
    'scrapy_splash.SplashCookiesMiddleware': 723,
    'scrapy_splash.SplashMiddleware': 725,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
    'scrapy_selenium.SeleniumMiddleware': 800
}
s['COOKIES_ENABLED'] = True
s['COOKIES_DEBUG'] = True
s['SPLASH_URL'] = 'http://192.168.59.103:8050'

s['SPIDER_MIDDLEWARES'] = {
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}
s['DUPEFILTER_CLASS'] = 'scrapy_splash.SplashAwareDupeFilter'
s['HTTPCACHE_STORAGE'] = 'scrapy_splash.SplashAwareFSCacheStorage'

process = CrawlerProcess(s)

for data in dataJson:
    process.crawl(AirbnbSpider, dataJson=data)

process.start()
