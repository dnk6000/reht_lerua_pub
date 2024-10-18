import crawler
from const import Errors

from logging import Logger

from seleniumbase import SB
from bs4 import BeautifulSoup


class CrawlerLerua(crawler.Crawler):
    def __init__(self, domain: str,
                 login: str = None,
                 password: str = None,
                 logger: Logger = None,
                 pause_sec: int = 2,
                 url_search: str = '',
                 url_product: str = ''):
        super().__init__(domain, login, password, logger, pause_sec)
        self.url_search: str = url_search
        self.url_product: str = url_product

    def normalize_product_url(self, url: str):
        url = url.replace(self.url_product, '')
        url = url.replace(self.domain, '')
        product_part_url = self.url_product.replace(self.domain, '')
        url = url.replace(product_part_url, '')
        return url


class CrawlerLeruaSeleniumBase(CrawlerLerua):

    def __init__(self, domain: str,
                 login: str = None,
                 password: str = None,
                 logger: Logger = None,
                 pause_sec: int = 2,
                 hide_window: bool = False,
                 url_search: str = '',
                 url_product: str = ''):

        super().__init__(domain, login, password, logger, pause_sec, url_search, url_product)

        # after updating seleniumbase library you need to modify 4 files with the next 2 strings of code
        # for setting DRIVER_DIR const:
        #if 'CHROMEDRIVER_DIR' in os.environ:
        #    DRIVER_DIR = os.environ.get('CHROMEDRIVER_DIR')
        # \.venv\Lib\site-packages\seleniumbase\core\browser_launcher.py
        # \.venv\Lib\site-packages\seleniumbase\utilities\selenium_grid\grid_hub.py
        # \.venv\Lib\site-packages\seleniumbase\utilities\selenium_grid\grid_node.py
        # \.venv\Lib\site-packages\seleniumbase\console_scripts\sb_install.py

        self.hide_window = hide_window
        self.sb: (SB, None) = None


    def crawl_find_product_link(self, article):
        name, href, err = '', '', Errors.No_error
        try:
            self.sb.open(self.url_search + article)   # TODO  get via function
        except Exception:
            self.logger.exception("Error during looking for product link")
            err = Errors.Exception_on_search_page

        if not err:
            html = self.sb.get_page_source()
            soup = BeautifulSoup(html, 'html.parser')
            elems = soup.find_all(attrs={"opp-data-product-id": article})
            if elems:
                name = elems[0].a.attrs['aria-label']
                href = elems[0].a.attrs['href']
                href = self.normalize_product_url(href)
            else:
                err = Errors.Unclassified
                elems = soup.find('div', {'data-qa-nothing-found': ''})
                if elems:
                    err = Errors.Not_found
                else:
                    elems = soup.find_all(attrs={"data-qa": "error-layout"})
                    if elems:
                        err = Errors.Not_found

        return name, href, err

    def crawl_queue(self):

        repeat = False
        repeat_cnt = 0

        with SB(uc=True, page_load_strategy='eager', headless=self.hide_window) as self.sb:
            while len(self.queue) > 0 or repeat:
                if not repeat:
                    qelem = self.queue.popleft()
                    repeat_cnt = 0
                if type(qelem.item) is str:
                    qelem_id = qelem.item
                    self.logger.info(f'New articul {qelem_id}. Looking for url via search page.')
                    qelem_url = ''
                else:
                    qelem_id = qelem.item.articul
                    qelem_name = qelem.item.name
                    qelem_url = qelem.item.url_id
                    err = ''

                if repeat:
                    qelem_url = ''
                repeat = False

                if qelem_url == '':
                    qelem_name, qelem_url, err = self.crawl_find_product_link(qelem_id)
                    qelem.url = qelem_url

                if err:
                    self.logger.error(f"Error during finding url for article {qelem_id}: {err}")
                    qelem.error = err
                    qelem.func(qelem)
                    continue

                if not qelem_url:
                    self.logger.error(f"Can't find url for article: {qelem_id}")
                    qelem.error = Errors.Url_not_found
                    qelem.func(qelem)
                    continue

                qelem_url = f'{self.url_product}{qelem_url}'
                self.logger.info(f'Start crawl: {qelem_id} {qelem_name}: {qelem_url}')
                try:
                    self.sb.open(qelem_url)
                except Exception:
                    self.logger.exception(f"Error during fetching url: {qelem_url}")
                    qelem.error = Errors.Exception_on_product_page
                    qelem.func(qelem)
                    continue

                repeat = qelem.func(qelem)
                if repeat and repeat_cnt > 0:
                    repeat = False
                else:
                    repeat_cnt += 1


    def crawl_queue_old(self):
        from bs4 import BeautifulSoup

        with SB(uc=True, page_load_strategy='eager') as sb:
            # sb.open(self.domain)

            while len(self.queue) > 0:
                qelem = self.queue.popleft()
                if type(qelem.item) is str:
                    qelem_name = qelem.item
                    qelem_url = qelem.url
                else:
                    qelem_name = qelem.item.name
                    qelem_url = qelem.item.url

                qelem_url_ = 'new articul. will be using the search field to find it' if qelem_url == '' else qelem_url
                self.logger.info(f'Start crawl: {qelem_name}: {qelem_url_}')
                if qelem_url == '':
                    sb.open(self.domain+qelem.item)
                    # selector = 'div[data-qa="product"]:nth-of-type(1)>a'
                    # elements = sb.find_elements(selector)

                    soup = BeautifulSoup(sb.get_page_source(), 'html.parser')

                    # sb.switch_to_window(0)
                    # selector = '[data-qa="search-button"]'
                    # sb.wait_for_element_present(selector)
                    # buttons = sb.find_elements(selector)
                    # if buttons:
                    #     try:
                    #         sb.wait_for_element_clickable('[data-qa="search-button"]', timeout=10)
                    #         buttons[0].click()
                    #     except Exception:
                    #         self.logger.exception('Error during pushing the search-button')
                    #         continue
                    # else:
                    #     self.logger.error(f"Can't find search-button on the page {sb.get_current_url()}"
                    #                       f"    id = {qelem_name}")
                    #     continue

                    # Use the string selector directly with the 'type' method
                #     input_selector = 'input[data-qa="search-input"]'
                #     elements = sb.find_elements(input_selector)
                #     if elements:
                #         try:
                #             # sb.wait_for_element_visible(input_selector, timeout=10)
                #             sb.clear(input_selector)
                #             sb.type(input_selector, qelem_name + '\n')
                #         except Exception:
                #             self.logger.exception('Error during typing articul into the search field')
                #             continue
                #     else:
                #         self.logger.error(f"Can't find search-submit-button on the page {sb.get_current_url()}"
                #                           f"    id = {qelem_name}")
                #         continue
                #
                #     qelem.url = qelem_url = sb.driver.current_url
                # else:
                #     if len(sb.driver.window_handles) < 2:
                #         sb.open_new_tab(qelem_url)
                #     else:
                #         sb.switch_to_window(1)
                #         sb.open(qelem_url)

                # qelem.func(qelem, sb=sb)  # parsing
                self.logger.info(f'Finish crawl: {qelem_name}: {qelem_url}')
