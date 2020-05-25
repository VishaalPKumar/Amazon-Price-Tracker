import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json


class SpreadsheetUpdater(object):
    def __init__(self, spreadsheet_name):

        self.product_title_col = 1
        self.product_seller_col = 2
        self.product_price_col = 3
        self.product_url_col = 4

        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

        creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)

        client = gspread.authorize(creds)

        self.sheet = client.open(spreadsheet_name).sheet1

    def process_item_list(self):
        items = self.sheet.col_values(self.product_title_col)
        available_row = len(items)
        data = open("reports/output.json").read()
        data = json.loads(data)
        products = data['product']
        title = []
        seller = []
        price = []
        url = []
        for product in products:
            title.append(product['title'])
            seller.append(product['seller'])
            price.append(product['price'])
            url.append(product['url'])
        for i in range(len(title)):
            self.sheet.update_cell(i + 2 + available_row, self.product_title_col, title[i])
            self.sheet.update_cell(i + 2 + available_row, self.product_seller_col, seller[i])
            self.sheet.update_cell(i + 2 + available_row, self.product_price_col, price[i])
            self.sheet.update_cell(i + 2 + available_row, self.product_url_col, url[i])


spreadsheet_updater = SpreadsheetUpdater("AmazonPrices")
spreadsheet_updater.process_item_list()
