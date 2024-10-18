import log
from parser import Parser
from modules_lerua.crawler_lerua import CrawlerLeruaSeleniumBase
from crawler import QueueElem
from data import ProductItem, TableProducts
from common import fillvals
from const import Errors

from logging import Logger
import pandas as pd
# from line_profiler_pycharm import profile
from seleniumbase import SB
from bs4 import BeautifulSoup
import re

from typing import Callable


class ProductItemLerua(ProductItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_url_id(self, url):
        return url


class ParserLerua(Parser):

    def __init__(self,
                 project_name: str,
                 logger: Logger,
                 url_prefix: str = ''):
        super().__init__(logger)

        self.crawler: (CrawlerLeruaSeleniumBase, None) = None

        self.category_control: bool = False
        self.articles: list[str] = []
        self.urls: list[str] = []

        self.table_products: TableProducts = TableProducts(project_name, logger)

        self.products_cnt: int = 0

        self.df_res: (pd.DataFrame, None) = None  # df for crawling articles
        self.df_crwl: (pd.DataFrame, None) = None  # df for crawling articles

        self.url_prefix: str = url_prefix

    def read_articles(self, articles_file: str) -> bool:
        """Return True if success and False if not"""
        try:
            with open(articles_file, encoding="utf-8") as f:
                lines: list[str] = f.readlines()
        except UnicodeDecodeError:
            with open(articles_file, encoding="cp1251") as f:
                lines: list[str] = f.readlines()
        except FileNotFoundError:
            self.logger.error(f'File with articles not found: {articles_file}')
            return False

        for line in lines:
            if not line.startswith('#') and line.strip() != '':
                art: list[str] = list(map(lambda s: s.strip(), line.split(',')))
                self.articles.extend(art)

        return True

    def read_urls(self, url_file: str) -> bool:
        """Return True if success and False if not"""
        try:
            with open(url_file, encoding="utf-8") as f:
                self.urls = f.readlines()
        except UnicodeDecodeError:
            with open(url_file, encoding="cp1251") as f:
                self.urls = f.readlines()
        except FileNotFoundError:
            self.logger.error(f'File with articles not found: {url_file}')
            return False

        self.urls = list(map(lambda s: s.strip(), self.urls))

        return True

    def crawl_articles(self) -> None:
        dfp = self.table_products.df

        # user requested articuls
        df_req = pd.DataFrame(self.articles, columns=['articul'])

        # future result for user
        self.df_res = df_req.merge(dfp, left_on='articul', right_on='articul', how='left')

        for index, row in self.df_res.iterrows():
            if pd.isna(row['url_id']):
                qe = QueueElem(item=row['articul'], func=self.parse_page, groups_on=False)
            else:
                pi = ProductItemLerua(logger=self.logger, articul=row['articul'],
                                      name=row['name'],tab_url=row['url_id'])
                qe = QueueElem(item=pi, func=self.parse_page, url=row['url_id'], groups_on=False)
            self.crawler.queue.append(qe)

        self.crawler.crawl_queue()

        df_mod = dfp.loc[dfp['upd_session_id'] == self.table_products.upd_session_id]

        # 1 - successful articles
        df1_success = df_mod.loc[dfp['articul'].isin(df_req['articul'].to_numpy())]
        df1_success.loc[:, 'error'] = ''

        # 2 - articles with error
        df2_error = df_mod.loc[dfp['articul'].isin(df_req['articul'].to_numpy())]
        df2_error = df2_error[df2_error['error'] != '']

        # 3 - not in db
        df3_nonexist = pd.merge(df_mod, self.df_res, on='articul', how='outer', indicator=True, suffixes=('_x', ''))
        df3_nonexist = df3_nonexist[df3_nonexist['_merge'] == 'right_only']
        columns_to_drop = [col for col in df3_nonexist.columns if col.endswith('_x')]
        df3_nonexist = df3_nonexist.drop(columns=columns_to_drop)
        df3_nonexist = df3_nonexist.drop(columns='_merge')
        df3_nonexist.loc[:, 'error'] = 'not in db'

        self.df_res = pd.concat([df1_success, df2_error, df3_nonexist])

    def parse_page(self, qelem: QueueElem, **kwargs) -> None:
        ...

    def __extract_number(self, s: str) -> str:
        return re.search(r'\d+(?:\.\d+)?', s).group()

    def __extract_price_unit(self, s: str):
        price_pattern = r'\d+(?:\s\d+)*'
        unit_pattern = r'\/(\w+\.)'

        price_match = re.search(price_pattern, s)
        unit_match = re.search(unit_pattern, s)

        if price_match and unit_match:
            price = price_match.group()
            unit = unit_match.group(1)
            return price, unit
        else:
            return None, None

    def _parse_page(self, qelem, html) -> bool:

        repeat: bool = False

        data = {'articul': '', 'name': '', 'amount': 0, 'unit': '',
                'per_pack': '', 'price': '', 'error': ''}

        old_vals = self.table_products.get_existing_data(qelem.item)
        fillvals(data, old_vals)

        if type(qelem.item) is str:
            processing_articul = qelem.item
        else:
            processing_articul = qelem.item.articul
        data['articul'] = processing_articul
        data['per_pack'] = -1  # to skip processing
        data['amount'] = 0
        data['error'] = qelem.error

        if qelem.error:
            item = ProductItemLerua(self.logger, tab_url=qelem.url, old_vals=old_vals, **data)
            self.table_products.append(item)
            return repeat

        soup = BeautifulSoup(html, 'html.parser')

        # 404 check
        elements = soup.find_all(attrs={"data-id": "404-header"})
        if elements:
            data['error'] = Errors.Bad_url
            item = ProductItemLerua(self.logger, tab_url='', old_vals=old_vals, **data)
            item.url_id = ''
            self.table_products.append(item)
            repeat = True
            self.logger.warning(f"Bad url for articul {data['articul']}. Trying to find url via search.")
            return repeat

        # articul & name
        elements = soup.find_all(attrs={"opp-data-product-id": data['articul']})
        if elements:
            field: str = elements[0].div.span.next
            data['articul'] = field.replace('ЛМ ','').strip()
            data['name'] = elements[0].h1.span.next
        else:
            data['error'] = Errors.Bad_url
            item = ProductItemLerua(self.logger, tab_url='', old_vals=old_vals, **data)
            item.url_id = ''
            self.table_products.append(item)
            repeat = True
            self.logger.warning(
                f"Wrong previous url for {data['articul']}. Trying to find url via search. Url: {qelem.url}")
            return repeat

        # # name
        # elements = soup.find_all(attrs={"opp-data-product-id": data['articul']})
        # if elements:
        #     data['name'] = elements[0].h1.span.next

        # price
        elements = soup.find_all(attrs={'data-qa': 'price-view','class': lambda x: x and x.startswith('primary-price')})
        if elements:
            price_str, unit_str = self.__extract_price_unit(elements[0].text)
            if price_str is not None:
                data['price'] = price_str.replace(chr(160),'')
            else:
                self.logger.error(f"Can't extract price for articul {data['articul']}. Price string is: {elements[0].text}")
            if unit_str is not None:
                data['unit'] = unit_str
            else:
                self.logger.error(f"Can't extract price for articul {data['articul']}. Price string is: {elements[0].text}")

            # field: str = elements[0].text
            # field = field.replace(' ', '')
            # field = field.replace(chr(160), '')
            # data['price'] = self.__extract_number(field)
            # data['unit'] = field.split('/')[-1]

        # amount on the wirehouse
        elements = soup.find_all(attrs={"data-qa": "out-of-stock-label"})
        if elements:
            data['error'] = Errors.Out_of_stock
        else:
            elements = soup.find_all(string=lambda text: 'Доступно для заказа' in text)
            if elements:
                field: str = elements[0].parent.next
                field = field.replace('Доступно для заказа ','')
                data['amount'] = self.__extract_number(field)

        item = ProductItemLerua(self.logger, tab_url=qelem.url, old_vals=old_vals, **data)
        self.products_cnt += 1
        self.table_products.append(item)
        self.logger.info(f'{self.products_cnt:>5} Parsed product: {data['articul']}')

        return repeat

    def get_full_url(self, url_id: str) -> str:
        return self.url_prefix + url_id


class ParserLeruaSeleniumBase(ParserLerua):

    def __init__(self,
                 project_name: str,
                 logger: Logger = None,
                 url_prefix: str = ''):
        super().__init__(project_name, logger, url_prefix)
        self.crawler: (CrawlerLeruaSeleniumBase, None) = None

    def parse_page(self, qelem: QueueElem, **kwargs) -> bool:
        _debug = False
        # sb: SB = kwargs['sb']
        sb: SB = self.crawler.sb

        html = sb.get_page_source()
        return self._parse_page(qelem, html)

    def crawl_all(self):
        pass

    def crawl_urls(self, list_url: list, parse_fun: Callable = None):
        if parse_fun is None:
            parse_fun = self.parse_page

        for i, url in enumerate(list_url, start=1):
            self.crawler.queue.append(QueueElem(f'Url from list number {i}', parse_fun, url, groups_on=False))

        self.crawler.crawl_queue()
