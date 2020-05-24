import time
import json
from bs4 import BeautifulSoup
from datetime import datetime
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from amazon_config import (
    get_chrome_web_driver,
    get_web_driver_options,
    set_ignore_certificate_error,
    set_browser_as_incognito,
    set_automation_as_head_less,
    DIRECTORY,
    NAME,
    CURRENCY,
    FILTERS,
    BASE_URL
)

class GenerateReport:
    def __init__(self, file_name, filters, base_link, currency, data):
        self.data = data
        self.file_name = file_name
        self.filters = filters
        self.base_link = base_link
        self.currency = currency
        report = {
            "title": self.file_name,
            'date': self.get_now(),
            'best_item': self.get_best_item(),
            'currency': self.currency,
            'filters': self.filters,
            'base_link': self.base_link,
            'product': self.data
        }
        print("Creating report...")
        with open(f'{DIRECTORY}/{file_name}.json', 'w') as f:
            json.dump(report, f)
        print("Done...")
    @staticmethod
    def get_now():
        now = datetime.now()
        return now.strftime("%d/%m/%Y %H:%M:%S")

    def get_best_item(self):
        try:
            return sorted(self.data, key = lambda k:k['price'])[0]
        except Exception as e:
            print(e)
            print("Cannot get best product...")
            return None


class AmazonAPI:
    def __init__(self, search_term, filters, base_url, currency):
        self.base_url = base_url
        self.search_term = search_term
        options = get_web_driver_options()
        set_ignore_certificate_error(options)
        set_browser_as_incognito(options)
        self.driver = get_chrome_web_driver(options)
        self.currency = currency
        self.price_filter = f"@rh=p_36%3A{filters['min']}00-{filters['max']}00"

    def run(self):
        print("Starting script")
        print(f"Looking for {self.search_term} products")
        (links, asins) = self.get_products_links()
        if not links:
            print("Stopped Script")
            return
        print("Got", len(links), "link to products")
        print("Getting info about products.....")
        products = self.get_product_info(links, asins)
        print("Got info about", len(products), "products")
        self.driver.quit()
        return products

    def get_products_links(self):
        self.driver.get(self.base_url)
        element = self.driver.find_element_by_xpath('//*[@id ="twotabsearchtextbox"]')
        element.send_keys(self.search_term)
        element.send_keys(Keys.ENTER)
        time.sleep(2)
        self.driver.get(f'{self.driver.current_url}{self.price_filter}')
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        results = soup.find_all("div", {"data-component-type": "s-search-result"})
        links = []
        asins = []
        for result in results:
            asin = result.get('data-asin', None)
            asins.append(asin)
            links.append(f"{self.base_url}dp/{asin}")

        print(links)
        return links, asins

    def get_product_info(self, links, asins):
        products = []
        for i in range(len(links)):
            url = f'{links[i]}?language=en_GB'
            self.driver.get(url)
            time.sleep(2)
            title = self.get_title()
            seller = self.get_seller()
            price = self.get_price()
            if title and price and seller:
                product = {
                    'asin': asins[i],
                    'url': links[i],
                    'title': title,
                    'seller': seller,
                    'price': price
                }
                products.append(product)
        return products

    def get_title(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            # Testing
            print("Title of product -", soup.find(id='productTitle').get_text().strip())
            return soup.find(id='productTitle').get_text().strip()
        except Exception as e:
            print(e)
            print("Cannot get title of product -", self.driver.current_url)
            return None

    def get_seller(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            # Testing
            print("Seller of product", soup.find(id='bylineInfo').get_text().strip())
            return soup.find(id='bylineInfo').get_text().strip()
        except Exception as e:
            print(e)
            print("Cannot get seller of product -", self.driver.current_url)
            return None

    def get_price(self):
        price = None
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        try:
            price = soup.find(id='priceblock_ourprice')
            price = price.get_text().strip()
            price = self.convert_price(price)
            # Testing
            print("Price of product -", price)
        except Exception as e:
            try:
                availability = soup.find(id='availability').get_text().strip()
                print(availability)
                if 'Available' in availability or 'In Stock' in availability:
                    price = soup.find("span", {"class": "olp-padding-right"}).get_text().strip()
                    price = price[price.find(self.currency):]
                    price = self.convert_price(price)
                    print(price)
                elif 'ships' in availability or 'in stock' in availability:
                    price = soup.find(id="olp-upd-new-used").get_text().strip()
                    price = price[price.find(self.currency):]
                    price = self.convert_price(price)
                    print(price)
            except Exception as e:
                print(e)
                print("Cannot get price of product -", self.driver.current_url)
                return None
        return price

    def convert_price(self, price):
        price = price.split(self.currency)[1]
        try:
            price = price.split("\n")[0] + "." + price.split("\n")[1]
        except:
            Exception()
        try:
            price = price.split(",")[0] + price.split(",")[1]
        except:
            Exception()
        return float(price)


if __name__ == '__main__':
    am = AmazonAPI(NAME, FILTERS, BASE_URL, CURRENCY)
    data = am.run()
    GenerateReport(NAME, FILTERS, BASE_URL, CURRENCY, data)

