import scrapy
from datetime import datetime
import re
import sys


class AirbnbSpider(scrapy.Spider):
    name = 'airbnb_scrap'
    allowed_domains = ['airbnb.com']

    def __init__(self, dataJson, **kwargs):
        super().__init__(**kwargs)
        try:
            if dataJson is None:
                raise Exception("Conf file error, json object is None")

            now_date = datetime.now()
            checkin = datetime.fromisoformat(dataJson['checkin'])
            checkout = datetime.fromisoformat(dataJson['checkout'])

            check_date_in_out = checkout < checkin
            check_date_to_now = checkin < now_date or checkout < now_date

            if check_date_in_out or check_date_to_now:
                raise Exception("Wrong date")

            url = 'https://www.airbnb.com/s/{}--{}/homes?refinement_paths%5B%5D=%2Fhomes&checkin={}&checkout={' \
                  '}&adults={}&children={}&infants={}&search_type=pagination '
            self.i = 2

            self.start_urls = [
                url.format(dataJson['place'], dataJson['country'], dataJson['checkin'], dataJson['checkout'],
                           dataJson['adults'], dataJson['children'], dataJson['infants'])
            ]

            date_time_obj = datetime.now()
            timestamp_str = date_time_obj.strftime("%d-%b-%Y_(%H:%M:%S.%f)")
            self.file_name = '{}_{}_{}_{}_{}.csv'.format(
                dataJson['checkin'], dataJson['checkout'],  dataJson['place'], dataJson['country'], timestamp_str)
            t = open(self.file_name, "w+")
            t.write('property_id,page_number,type,link\n')
            t.close()
        except Exception as e:
            print(e)

    def parse(self, response):
        self.parse_page(response)
        str_url = '//ul[contains(@data-id, \"SearchResultsPagination\")]/li[contains(@data-id, \"page-{0}\")]/a/@href'.format(
            str(self.i))

        res_next_url = response.xpath(str_url).get()

        if res_next_url is not None:
            next_url = 'https://www.airbnb.com' + res_next_url
            self.i += 1
            yield scrapy.Request(response.urljoin(next_url), callback=self.parse)

    def parse_page(self, response):

        rooms = response.xpath('//div[contains(@itemprop, \"itemListElement\")]/meta[contains(@itemprop, '
                               '\"url\")]/@content').getall()

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
            f.write(idR + ',' + str(self.i - 1) + ',' + typeR + ',' + room + '\n')

        f.close()

