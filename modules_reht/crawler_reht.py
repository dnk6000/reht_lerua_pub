import crawler
from crawler_selenium import CrawlerSelenium

import logging
from logging import Logger
from selenium.webdriver.common.by import By
import time


class CrawlerReht(crawler.Crawler):
    def __init__(self, domain: str,
                 login: str = None,
                 password: str = None,
                 logger: Logger = None,
                 pause_sec: int = 2):
        super().__init__(domain, login, password, logger, pause_sec)


class CrawlerRehtSelenium(CrawlerSelenium):

    def __init__(self, domain: str,
                 login: str = None,
                 password: str = None,
                 logger: Logger = None,
                 pause_sec: int = 2,
                 hide_window=False):
        self.authorization = False

        if login is None or login == '' or password is None or password == '':
            logging.getLogger('root').info(f'Login and Password for Reht crawler must be specified!')
            return

        super().__init__(domain, login, password, logger, pause_sec, hide_window)
        self.browser.implicitly_wait(15)  # TODO make as parameter !!!

    def authorize(self, forced: bool = True):
        if not forced and self.authorization:
            return

        self.logger.info(f'Opening start page: {self.domain}')
        self.get_page(self.domain)
        self.logger.info(f'Start page opened')

        buttons = self.browser.find_elements(By.CSS_SELECTOR, 'div.support-close.header-button')
        if len(buttons) > 0:
            buttons[0].click()
        self.pauser.smart_sleep()

        self.logger.info(f'Performing authorization: {self.domain}')
        elem = self.browser.find_element(By.NAME, 'inn')
        elem.send_keys(self.login)  # + Keys.RETURN
        elem = self.browser.find_element(By.NAME, 'pass')
        elem.send_keys(self.password)
        enter = self.browser.find_element(By.NAME, 'submit')
        enter.click()

        for elem in self.browser.find_elements(By.CLASS_NAME, 'icart'):
            if 'КОРЗИНА' in elem.text:
                self.authorization = True
                break

        if self.authorization:
            self.logger.info(f'Successfully authorized by login {self.login} in domain {self.domain}')
        else:
            self.logger.error(f'Failed authorization by login {self.login} in domain {self.domain}')

    def get_page(self, url):
        self.logger.info(f'Get url: {url}')
        self.browser.get(url)
        self.pauser.smart_sleep()

    def crawl_queue(self):
        while len(self.queue) > 0:
            qelem = self.queue.popleft()
            if type(qelem.item) is str:
                qelem_name = qelem.item
                qelem_url = qelem.url
            else:
                qelem_name = qelem.item.name
                qelem_url = qelem.item.url

            self.logger.info(f'Start crawl: {qelem_name}: {qelem_url}')
            self.get_page(qelem_url)
            qelem.func(qelem)
            self.logger.info(f'Finish crawl: {qelem_name}: {qelem_url}')
