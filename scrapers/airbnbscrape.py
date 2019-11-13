import json
import scrapy
from datetime import datetime
import re


class AirbnbSpider(scrapy.Spider):
    name = 'airbnb_scrap'
    allowed_domains = ['airbnb.com']
    f = open("/home/popdav/rista/airbnb_checker/scrapers/conf.json", "r")
    data = f.read()
    dataJson = json.loads(data)
    f.close()
    url = 'https://www.airbnb.com/s/{}--{}/homes?refinement_paths%5B%5D=%2Fhomes&checkin={}&checkout={}&adults={' \
          '}&children={}&infants={}&search_type=pagination'
    i = 2
    current_page = 'page-' + str(i)
    start_urls = [
        url.format(dataJson['place'], dataJson['country'], dataJson['checkin'], dataJson['checkout'],
                   dataJson['adults'], dataJson['children'], dataJson['infants'])
    ]

    date_time_obj = datetime.now()
    timestamp_str = date_time_obj.strftime("%d-%b-%Y_(%H:%M:%S.%f)")
    file_name = 'place={}&country={}&checkin={}&checkout={}&adults={}&children={}&infants={}_{}.csv'.format(
        dataJson['place'],
        dataJson['country'], dataJson['checkin'], dataJson['checkout'],
        dataJson['adults'], dataJson['children'], dataJson['infants'], timestamp_str)
    t = open(file_name, "w+")
    t.write('property_id,type,link\n')
    t.close()

    def parse(self, response):
        print(response.url)

        self.parse_page(response)
        str_url = '//ul[contains(@data-id, \"SearchResultsPagination\")]/li[contains(@data-id, \"page-{0}\")]/a/@href'.format(
            str(self.i))
        res_next_url = response.xpath(str_url).get()
        if res_next_url is not None:
            next_url = 'https://www.airbnb.com' + res_next_url

        self.i += 1

        if res_next_url is not None:
            yield scrapy.Request(response.urljoin(next_url), callback=self.parse)

    def parse_page(self, response):

        rooms = response.xpath('//div[contains(@itemprop, \"itemListElement\")]/meta[contains(@itemprop, \"url\")]/@content').getall()

        rooms = list(
            map(lambda x: 'https://www.airbnb.com/' +
                          re.search('undefined/([a-zA-Z]*)/([0-9]*)', x).group(1) + '/' +
                          re.search('undefined/([a-zA-Z]*)/([0-9]*)', x).group(2),
                rooms)
        )

        f = open(self.file_name, 'a')
        for room in rooms:
            typeR = re.search('https://www.airbnb.com/([a-zA-Z]*)/([0-9]*)', room).group(1)
            idR = re.search('https://www.airbnb.com/([a-zA-Z]*)/([0-9]*)', room).group(2)
            f.write(idR + ',' + typeR + ',' + room + '\n')

        f.close()

