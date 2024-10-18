import projects
from modules_reht.crawler_reht import CrawlerRehtSelenium
from modules_reht.parser_reht import ParserRehtSelenium

from argparse import Namespace


class ProjectReht(projects.Project):
    def __init__(self, operation: str, project_cfg_file: str, result_file: str):
        super().__init__(operation, project_cfg_file, result_file)
        if not self.options_ok:
            return

        self.parser = None

    def _init_parser(self, forced: bool = True):
        if not forced and self.parser is not None:
            return

        self.parser = ParserRehtSelenium(self.options['project_name'], self.logger, self.options['table_page_url'])

        self.parser.crawler = CrawlerRehtSelenium(domain=self.options['domain'],
                                                  login=self.options['login'],
                                                  password=self.options['password'],
                                                  logger=self.logger,
                                                  pause_sec=self.options['pause_sec'],
                                                  hide_window=self.options['hide_browser_window'])

    def quit(self):
        if self.parser is not None:
            if self.parser.crawler is not None:
                self.parser.crawler.quit()

    def check(self) -> None:
        self._init_parser()
        self.parser.crawler.authorize()
        if self.parser.crawler.authorization:
            self.parser.parse_categories()

            msg = f'{len(self.parser.categories)} categories found:'
            print(msg)
            self.logger.info(msg)
            for cat in self.parser.categories:
                print(cat)
                self.logger.info(cat)

            self.parser.table_groups.save()

            print('Table groups: \n')
            print(self.parser.table_groups.df.iloc[:50].to_string())
            print('Table products: \n')
            print(self.parser.table_products.df.iloc[:50].to_string())



    def crawlall(self, args: Namespace) -> None:
        error = False
        forbidden_options = ['cat', 'urls', 'url', 'article', 'articles']
        for opt in forbidden_options:
            if getattr(args, opt) != '':
                self.logger.error(f"For operation 'crawlall' option '{opt}' is forbidden!")
                error = True

        if not error:
            self._init_parser()
            self.parser.crawler.authorize()
            if self.parser.crawler.authorization:
                self.parser.parse_categories()
                self.parser.crawl_all()
                self.parser.table_groups.save()
                self.parser.table_products.save()

    def crawl(self, args: Namespace) -> None:
        required_options = ['cat', 'urls', 'url', 'articles']
        if all([getattr(args, opt) != '' for opt in required_options]):
            self.logger.error(f"For operation 'crawl' one of the next options is required: {required_options}!")
            return

        option: str = ''
        for opt in required_options:
            if getattr(args, opt) != '':
                option = opt

        self._init_parser()

        match option:
            case 'cat':
                self.make_result_file_bak()
                if not self.parser.read_categories(getattr(args, option)):
                    return
                self.parser.crawler.authorize()
                if self.parser.crawler.authorization:
                    self.parser.parse_categories()
                    self.parser.crawl_all()
                    self.parser.table_groups.save()
                    self.parser.table_products.save()
            case 'urls':
                if not self.parser.read_urls(getattr(args, option)):
                    return
                self.parser.crawler.authorize()
                if self.parser.crawler.authorization:
                    self.parser.crawl_urls(self.parser.urls)
                self.parser.table_groups.save()
                self.parser.table_products.save()
            case 'articles':
                self.make_result_file_bak()
                if not self.parser.read_articles(getattr(args, option)):
                    return
                self.parser.crawler.authorize()
                if self.parser.crawler.authorization:
                    self.parser.crawl_articles()
                self.parser.table_products.save_df(self.parser.df_res, self.result_file)
                self.parser.table_products.save()
            case _:
                self.logger.error(f"Unexpected option encountered: {option} !")
                return
        pass
