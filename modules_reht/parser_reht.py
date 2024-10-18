import log
from parser import Parser
from modules_reht.crawler_reht import CrawlerRehtSelenium
from crawler import QueueElem
from data import strip_name, ProductItem, GroupItem, TableGroups, TableProducts
from common import fillvals

from selenium.webdriver.common.by import By
from logging import Logger
import pandas as pd
# from line_profiler_pycharm import profile

from typing import Callable


class ParserReht(Parser):

    def __init__(self, project_name: str, logger: Logger, url_prefix: str = ''):
        super().__init__(logger)

        self.crawler: (CrawlerRehtSelenium, None) = None

        self.category_control: bool = False
        self.articles: list[str] = []
        self.urls: list[str] = []
        self.permitted_cat: list[str] = []
        self.forbidden_cat: list[str] = []

        self.table_groups: TableGroups = TableGroups(project_name, logger)
        self.table_products: TableProducts = TableProducts(project_name, logger)

        self.categories: dict = {}
        self.groups_cnt: int = 0
        self.products_cnt: int = 0
        self.urls_cnt: int = 0

        self.df_res: (pd.DataFrame, None) = None  # df for crawling articles
        self.df_crwl: (pd.DataFrame, None) = None  # df for crawling articles

        self.url_prefix: str = url_prefix

    def read_categories(self, category_file: str) -> bool:
        """Return True if success and False if not"""
        self.category_control = True

        try:
            with open(category_file, encoding="utf-8") as f:
                lines: list[str] = f.readlines()
        except FileNotFoundError:
            self.logger.error(f'File with categories not found: {category_file}')
            return False

        for line in lines:
            if line[0:1] == '-':
                self.forbidden_cat.append(line.strip()[1:])
            else:
                self.permitted_cat.append(line.strip())

        for cat in self.permitted_cat:
            self.logger.info(f'Permitted category: {cat}')
        for cat in self.forbidden_cat:
            self.logger.info(f'Forbidden category: {cat}')

        return True

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
        dfg = self.table_groups.df

        # user requested articuls
        df_req = pd.DataFrame(self.articles, columns=['articul'])

        # future result for user
        self.df_res = df_req.merge(dfp, left_on='articul', right_on='articul', how='left')

        # for crawling
        self.df_crwl = (
            dfg.merge(self.df_res['id_group'], left_on='id', right_on='id_group', how='inner').drop_duplicates())

        # dfa_ = dfp.loc[dfp['articul'].isin(self.parser.articles)]
        # self.crawler.queue.append(QueueElem(self.categories[cat], self.parse_page))
        for index, row in self.df_crwl.iterrows():
            gi = GroupItem(self.logger, url=self.get_full_url(row['url_id']))
            gi.id = row['id']
            gi.name = row['name']
            gi.full_name = row['full_name']
            # gi.url = self.get_full_url(row['url_id'])
            # gi.url_id = row['url_id']
            qe = QueueElem(item=gi, func=self.parse_page, groups_on=False)
            # qe.url = self.get_full_url(row['url_id'])
            self.crawler.queue.append(qe)

        self.crawler.crawl_queue()

        df_mod = dfp.loc[dfp['upd_session_id'] == self.table_products.upd_session_id]

        # 1 - successful articles
        df1_success = df_mod.loc[dfp['articul'].isin(df_req['articul'].to_numpy())]
        df1_success.loc[:, 'error'] = ''

        # 2 - not found articles
        df_err = df_mod.merge(self.df_res, on='articul', how='right', suffixes=('', '_y'))
        df_err = df_err.loc[df_err['name'].isnull()]
        match_err = dfp['articul'].isin(df_err['articul'].to_numpy())
        dfp.loc[match_err, 'error'] = 'not found'  # not found in website page - modify base table
        df2_notfound = dfp.loc[match_err]

        # 3 - not in base table
        df3_nonexist = self.df_res.loc[self.df_res['name'].isnull()]
        df3_nonexist.loc[:, 'error'] = 'not in db'

        self.df_res = pd.concat([df1_success, df2_notfound, df3_nonexist])

    def parse_page(self, qelem: QueueElem) -> None:
        ...

    def get_full_url(self, url_id: str) -> str:
        return self.url_prefix + url_id


class ParserRehtSelenium(ParserReht):

    def __init__(self, project_name: str, logger: Logger = None, url_prefix: str = ''):
        super().__init__(project_name, logger, url_prefix)
        self.crawler: (CrawlerRehtSelenium, None) = None

    def parse_categories(self):
        _categories = []

        elems = self.crawler.browser.find_elements(By.CLASS_NAME, 'glMenu')
        for elem in elems:
            cat_name = str(elem.accessible_name).strip()
            if cat_name not in _categories:
                cat_url = elem.get_property('href')
                if '&dbn' in cat_url:
                    _categories.append(cat_name)
                    item = GroupItem(self.logger, name=cat_name, parent=None, url=cat_url)
                    self.table_groups.append(item)
                    self.categories[cat_name] = item

        self.logger.info(f'Parse categories: {len(_categories)} found')

    def parse_page(self, qelem: QueueElem) -> None:
        _debug = False
        log.debug_error(_debug, self.logger, 'Enter func')
        ignoring_names = ['[..]', '[.]']
        groups, products = [], []
        qelem_is_str = type(qelem.item) is not GroupItem

        self.urls_cnt += 1

        elems_no_items = self.crawler.browser.find_elements(By.CLASS_NAME, "noItems")
        no_items = len(elems_no_items) > 0

        if no_items:
            self.logger.info(f'No items on {qelem}')
        else:
            # parse groups
            if qelem.groups_on:
                log.debug_error(_debug, self.logger, 'parse groups')
                try:
                    elem_tab = self.crawler.browser.find_element(By.XPATH, "//form[@method='post']")
                    elements = elem_tab.find_elements(By.CLASS_NAME, 'glMenu')
                    for elem in elements:
                        name = strip_name(elem.accessible_name)
                        if name not in ignoring_names:
                            url = elem.get_property('href')
                            groups.append(GroupItem(self.logger, name=name, parent=qelem.item, url=url))
                except:
                    self.logger.exception(f'Parsing groups on url: {qelem.item}')
                    # self.logger.critical(f'Parsing groups on url: {qelem.item}')

            # parse products
            if qelem.products_on:
                log.debug_error(_debug, self.logger, 'parse products')
                try:
                    elem_tab = self.crawler.browser.find_element(By.CSS_SELECTOR, "table[cellpadding='2']")
                    elem_prod_strs = elem_tab.find_elements(By.CSS_SELECTOR, "tr:has( > td > a.link_oreht)")
                    pattern = {'articul': '', 'name': '', 'amount': '', 'unit': '',
                               'per_pack': '', 'price': '', 'error': ''}
                    for elem in elem_prod_strs:
                        fields = elem.text.split('\n')
                        parsed = pattern.copy()

                        if len(fields) in [6, 7]:
                            mode = 0  # normal
                        elif len(fields) == 3 and fields[2].strip() == 'товар временно отсутствует':
                            mode = 1  # product absent
                        elif len(fields) == 3 and fields[2].strip() == 'нет в наличии заказать?':
                            mode = 2  # for order
                        else:
                            mode = -1  # unknown

                        keep_old: bool = qelem_is_str or mode in [1, 2]
                        if mode != -1:
                            parsed['articul'] = fields[0]
                            parsed['name'] = strip_name(fields[1])
                        if keep_old:
                            old_vals = self.table_products.get_existing_data(parsed['articul'])
                            fillvals(parsed, old_vals)
                        else:
                            old_vals = {}

                        if mode == 0:  # normal
                            shift = 0 if len(fields) == 6 else 1
                            parsed['amount'] = fields[2+shift]
                            parsed['unit'] = fields[3+shift]
                            parsed['per_pack'] = fields[4+shift]
                            parsed['price'] = fields[5+shift]
                            parsed['error'] = ''
                        elif mode == 1:  # product absent:
                            parsed['error'] = 'temporarily absent'
                        elif mode == 2:  # for order:
                            parsed['error'] = 'out of stock'
                        else:
                            self.logger.error(f'Unexpected format of line in the table of products on web page. \
                                                Line text: {elem.text}   url: {qelem.url}')
                            continue

                        parent = qelem if qelem_is_str else qelem.item

                        item = ProductItem(self.logger, parent=parent, tab_url=qelem.url, old_vals=old_vals, **parsed)
                        products.append(item)
                except:
                    self.logger.exception(f'Parsing products on url: {qelem.url}')
                    # self.logger.critical(f'Parsing products on url: {qelem.url}')

        log.debug_error(_debug, self.logger, 'Logging')
        self.logger.info(f'Parsed pages counter: {self.urls_cnt}')
        for group in groups:
            self.groups_cnt += 1
            self.logger.info(f'{self.groups_cnt:>4} Parsed group: {group}')
            # self.crawler.queue.append(QueueElem(group.name, group.url, self.parse_page))
            self.table_groups.append(group)
            self.crawler.queue.append(QueueElem(group, self.parse_page))
        for product in products:
            self.products_cnt += 1
            self.table_products.append(product)
            self.logger.info(f'{self.products_cnt:>5} Parsed product: {product}')

        # DEBUG
        # if len(groups) > 0:
        #     self.crawler.queue.append(QueueElem(groups[0].name, groups[0].url, self.parse_page))
        log.debug_error(_debug, self.logger, 'Exit func')

    def crawl_all(self):
        if self.category_control and len(self.permitted_cat) > 0:
            cat_list = self.permitted_cat
        else:
            cat_list = list(self.categories.keys())

        for cat in cat_list:
            if self.category_control and cat in self.forbidden_cat:
                continue
            if cat not in self.categories:
                self.logger.error(f'Not found url for category: {cat}')
                continue

            self.logger.info(f'Start crawling category: {cat}')
            self.crawler.queue.append(QueueElem(self.categories[cat], self.parse_page))
            self.crawler.crawl_queue()

    def crawl_urls(self, list_url: list, parse_fun: Callable = None):
        if parse_fun is None:
            parse_fun = self.parse_page

        for i, url in enumerate(list_url, start=1):
            self.crawler.queue.append(QueueElem(f'Url from list number {i}', parse_fun, url, groups_on=False))

        self.crawler.crawl_queue()
