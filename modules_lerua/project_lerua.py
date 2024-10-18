import projects
from modules_lerua.crawler_lerua import CrawlerLeruaSeleniumBase
from modules_lerua.parser_lerua import ParserLeruaSeleniumBase

from argparse import Namespace


class ProjectLerua(projects.Project):
    def __init__(self, operation: str, project_cfg_file: str, result_file: str):
        super().__init__(operation, project_cfg_file, result_file)
        if not self.options_ok:
            return

        self.parser = None

    def _init_parser(self, forced: bool = True):
        if not forced and self.parser is not None:
            return

        self.parser = ParserLeruaSeleniumBase(self.options['project_name'],
                                              self.logger,
                                              self.options['product_page_url'])

        self.parser.crawler = CrawlerLeruaSeleniumBase(domain=self.options['domain'],
                                                       login=self.options['login'],
                                                       password=self.options['password'],
                                                       logger=self.logger,
                                                       pause_sec=self.options['pause_sec'],
                                                       hide_window=self.options['hide_browser_window'],
                                                       url_product=self.options['product_page_url'],
                                                       url_search=self.options['search_page_url'])

    def quit(self):
        if self.parser is not None:
            if self.parser.crawler is not None:
                self.parser.crawler.quit()

    def check(self) -> None:
        self._init_parser()
        self.parser.crawler.get_page()

        # self.parser.crawler.authorize()
        # if self.parser.crawler.authorization:
        #     self.parser.parse_categories()
        #
        #     msg = f'{len(self.parser.categories)} categories found:'
        #     print(msg)
        #     self.logger.info(msg)
        #     for cat in self.parser.categories:
        #         print(cat)
        #         self.logger.info(cat)
        #
        #     self.parser.table_groups.save()
        pass

    def crawl(self, args: Namespace) -> None:
        required_options = ['articles']
        if not any([getattr(args, opt) != '' for opt in required_options]):
            self.logger.error(f"For operation 'crawl' one of the next options is required: {required_options}!")
            return

        option: str = ''
        for opt in required_options:
            if getattr(args, opt) != '':
                option = opt

        self._init_parser()

        match option:
            case 'articles':
                if not self.parser.read_articles(getattr(args, option)):
                    return
                self.parser.crawl_articles()
                self.parser.table_products.save_df(self.parser.df_res, self.result_file)
                self.parser.table_products.save()
            case _:
                self.logger.error(f"Unexpected option encountered: {option} !")
                return
        pass
