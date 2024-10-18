from sys import executable

import const
import crawler

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from logging import Logger


class CrawlerSelenium(crawler.Crawler):

    def __init__(self,
                 domain: str,
                 login: str = None,
                 password: str = None,
                 logger: Logger = None,
                 pause_sec: int = 2,
                 hide_window=False):
        super().__init__(domain, login, password, logger, pause_sec)

        options = Options()
        # options.add_argument('--ignore-certificate-errors')
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0"
            # "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            )
        # options.add_argument("--disable-blink-features=AutomationControlled")
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option('useAutomationExtension', False)
        if hide_window:
            options.add_argument("--headless")
        options.headless = True

        service = Service(const.CHROMEDRIVER_DIR+'chromedriver.exe')
        # browser = webdriver.Chrome(options=options, executable_path=PATH_TO_CROMEDRIVER)
        self.browser = webdriver.Chrome(service=service, options=options)

    def quit(self):
        try:
            self.browser.quit()
        except:
            pass

    def __del__(self):
        # self.quit()
        pass
