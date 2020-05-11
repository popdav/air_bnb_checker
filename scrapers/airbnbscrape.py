import os
import re
from datetime import datetime

import scrapy
from scrapy_splash import SplashRequest
# get docker on Linux: sudo docker pull scrapinghub/splash
# get docker on OS X: docker pull scrapinghub/splash
# start splash docker
#  on Windows 10 with: docker run -p 5023:5023 -p 8050:8050 -p 8051:8051 scrapinghub/splash
#  on Linux: sudo docker run -it -p 8050:8050 --rm scrapinghub/splash
#  on OS X: docker run -it -p 8050:8050 --rm scrapinghub/splash

from database.mongodb.mongo_client import MongoDB

db = MongoDB('Airbnb')

WAIT_TIME_SPLASH = 20  # seconds


class AirbnbSpider(scrapy.Spider):
    name = 'airbnb_scrap'

    allowed_domains = ['airbnb.com']
    dataJson = {}

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

            self.dataJson = dataJson

            url = 'https://www.airbnb.com/s/{}--{}/homes?refinement_paths%5B%5D=%2Fhomes&checkin={}&checkout={' \
                  '}&adults={}&children={}&infants={}&search_type=pagination '
            self.i = 2

            self.start_urls = [
                url.format(dataJson['place'], dataJson['country'], dataJson['checkin'], dataJson['checkout'],
                           dataJson['adults'], dataJson['children'], dataJson['infants'])
            ]

            date_time_obj = datetime.now()
            timestamp_str = date_time_obj.strftime("%d-%b-%Y_(%H:%M:%S.%f)")
            self.file_name = u'{}_{}_{}_{}_{}.csv'.format(
                dataJson['checkin'], dataJson['checkout'], dataJson['place'], dataJson['country'], timestamp_str)

            # self.file_name = r'test.csv'
            print(self.file_name)
            t = open(os.path.join(self.file_name), "w+")
            t.write('property_id,page_number,type,link\n')
            t.close()
        except Exception as e:
            print(e)

    def parse(self, response):

        for req in self.parse_page(response):
            yield req


        str_url = '//ul[contains(@data-id, \"SearchResultsPagination\")]/li[contains(@data-id, \"page-{0}\")]/a/@href' \
            .format(str(self.i))

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

        f = open(os.path.join(self.file_name), 'a')
        for room in rooms:
            typeR = re.search('https://www.airbnb.com/([a-zA-Z]*)/([0-9]*)', room).group(1)
            idR = re.search('https://www.airbnb.com/([a-zA-Z]*)/([0-9]*)', room).group(2)
            f.write(idR + ',' + str(self.i - 1) + ',' + typeR + ',' + room + '\n')

        f.close()

        for url in rooms:
            idR = re.search('https://www.airbnb.com/([a-zA-Z]*)/([0-9]*)', url).group(2)
            finUrl = url + '?&check_in={}&check_out={}&adults={}&children={}&infants={}' \
                .format(self.dataJson['checkin'], self.dataJson['checkout'], self.dataJson['adults'],
                        self.dataJson['children'], self.dataJson['infants'])
            if idR != '':
                yield SplashRequest(
                    url=response.urljoin(url),
                    callback=self.parse_room,
                    meta={'id': idR},
                    args={
                        'html': 1,
                        'png': 1,
                        'wait': WAIT_TIME_SPLASH,
                        'render_all': 1,
                    }
                )

    def parse_room(self, response):
        html = response.body

        name = response.xpath('//*[@id="summary"]/div/div/div[1]/div/div/div[1]/div[1]/div/span/h1/span/text()').get()

        price = response.xpath('//*[@id="room"]/div[2]/div/div[2]/div[2]/div/div/div/div[2]/div/div/div['
                               '1]/div/div/div/div[1]/div/div/div[1]/div/span[2]/span/text()').get()

        if price is not None:
            price_search = re.search('\$([0-9]*)', price)
            if price_search is not None:
                price = price_search.group(1)

        details = response.xpath('//*[@id="room"]/div[2]/div/div[2]/div[1]/div/div[3]/div/div/div['
                                 '@class="_504dcb"]/div/div/div[2]/div/span/text()').getall()

        superhost = False
        if details is not None:
            for d in details:
                has_superhost = re.search('Superhost', d)
                if has_superhost is not None:
                    superhost = True
                    break

        stars = response.xpath('//*[@id="room"]/div[2]/div/div[2]/div[2]/div/div/div/div[2]/div/div/div['
                               '1]/div/div/div/div[1]/div/div/div[2]/button/div/div[1]/div[2]/div/div/text()').get()

        sleeping_arr = response.xpath('//*[@id="room"]/div[2]/div/div[2]/div[1]/div/div[3]/div/div/div['
                                      '1]/div/div/div/div/text()').getall()
        sleeping = {}
        if sleeping_arr is not None:
            for i in range(len(sleeping_arr)):
                number_search = re.search('([0-9]*) ([a-zA-Z]*)', sleeping_arr[i])
                if number_search is None:
                    number = 0
                else:
                    number = number_search.group(1)

                type_of_search = re.search('([0-9]*) ([a-zA-Z]*)', sleeping_arr[i])
                if type_of_search is None:
                    type_of = 'not_found'
                else:
                    type_of = type_of_search.group(2)

                sleeping[type_of] = int(number if number != '' else 0)

        review_fields = response.xpath('//*[@id="reviews"]/div/div/section/div[2]/div[1]/div/div/div/div'
                                       '/div/div/div/span[@class="_czm8crp"]/text()').getall()

        review_grades = response.xpath('//*[@id="reviews"]/div/div/section/div[2]/div[1]/div/div/div/div'
                                       '/div/div/div[2]/div/div/div[2]/div/div[@class="_1p3joamp"]/text()').getall()
        review_number = response.xpath('//*[@id="reviews"]/div/div/section/div[1]/div/div[2]/div['
                                       '1]/div/div/div/div/div/div[3]/span[1]/text()').get()
        review = {}
        if review_fields is not None and review_grades is not None:
            for i in range(len(review_fields)):
                review[review_fields[i].lower() if review_fields[i] is not None else ''] = float(review_grades[i]) if review_grades[i] is not None else None

        insert_object = {
            'airbnb_id': response.meta['id'],
            'name': name,
            'price': float(price) if price is not None else None,
            'sleeping': sleeping,
            'superhost': superhost,
            'stars': float(stars) if stars is not None else None,
            'review_number': int(review_number) if review_number is not None else None,
            'review': review
        }
        collection_name = self.file_name[:self.file_name.find('.csv')]
        db.insert_one(insert_object, collection_name)
        print(f"inserted: \n url: {response.url}, id: {response.meta['id']}, name: {name}")
