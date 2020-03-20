import scrapy
from datetime import datetime
import re, json
from database.mongodb.mongo_client import MongoDB
from scrapy_selenium import SeleniumRequest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

db = MongoDB('airbnb')


class AirbnbSpider(scrapy.Spider):
    name = 'airbnb_scrap'

    allowed_domains = ['airbnb.com']
    dataJson = {}

    def __init__(self, dataJson, **kwargs):
        super().__init__(**kwargs)

        self.driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.set_window_size(1500, 1000)

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
            self.file_name = '{}_{}_{}_{}_{}.csv'.format(
                dataJson['checkin'], dataJson['checkout'], dataJson['place'], dataJson['country'], timestamp_str)
            t = open(self.file_name, "w+")
            t.write('property_id,page_number,type,link\n')
            t.close()
        except Exception as e:
            print(e)

    def parse(self, response):

        for req in self.parse_page(response):
            yield req

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

        for url in rooms:
            idR = re.search('https://www.airbnb.com/([a-zA-Z]*)/([0-9]*)', url).group(2)
            finUrl = url + '?&check_in={}&check_out={}&adults={}&children={}&infants={}' \
                .format(self.dataJson['checkin'], self.dataJson['checkout'], self.dataJson['adults'],
                        self.dataJson['children'], self.dataJson['infants'])
            yield scrapy.Request(
                url=response.urljoin(finUrl),
                callback=self.parse_room,
                dont_filter=True,
                meta={'id': idR}
            )

    def parse_room(self, response):

        idR = response.meta.get('id')

        self.driver.get(response.url)
        self.driver.implicitly_wait(10)

        name = self.driver.find_element_by_xpath('//*[@id="summary"]/div/div/div[1]/div/div/div[1]/div[1]/'
                                                 'div/span/h1/span')
        print(name.text)

        stars = self.driver.find_element_by_xpath('//*[@id="room"]/div[2]/div/div[2]/div[2]/div/div/div[1]/div/div/'
                                                  'div[1]/div/div/div[2]/div[2]/button/div/div[1]/div[2]/div/div')
        print(stars.text)

        price_per_day = self.driver.find_element_by_xpath('//*[@id="room"]/div[2]/div/div[2]/div[2]/div/div/div[1]/'
                                                          'div/div/div[1]/div/div/div[2]/div[1]/div/span[2]/span')
        print(price_per_day.text)

        cleaning_fee = self.driver.find_element_by_xpath('//*[@id="book_it_form"]/div[2]/div[2]/div[1]/div[2]/span/span')
        print(cleaning_fee.text)

        service_fee = self.driver.find_element_by_xpath('//*[@id="book_it_form"]/div[2]/div[3]/div[1]/div[2]/span/span')
        print(service_fee.text)

        total_price = self.driver.find_element_by_xpath('//*[@id="book_it_form"]/div[4]/div[2]/div/div/div[2]/span/span')
        print(total_price.text)
        print("################################################################")
