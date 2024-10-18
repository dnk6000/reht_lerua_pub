import argparse
from argparse import ArgumentParser, Namespace


def get_parsed_cmd_args() -> (Namespace, None):
    parser = argparse.ArgumentParser(description='The format of crawler command-line:')
    parser.add_argument('operation', type=str, help='Operation to perform', choices=['crawl', 'crawlall', 'check'])
    parser.add_argument('project_cfg_file', type=str, help='Project config file')
    parser.add_argument('result_file', type=str, help='File for results')
    parser.add_argument('-cl', '--clearlog', action='store_true', help='Clear common log file')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--cat', type=str, default='', help='File containing list of categories for crawling')
    group.add_argument('--url', type=str, default='', help='The only url for crawling')
    group.add_argument('--urls', type=str, default='', help='File containing list of urls for crawling')
    group.add_argument('--article', type=str, default='', help='The only article for crawling')
    group.add_argument('--articles', type=str, default='', help='File containing list of articles for crawling')

    try:
        return parser.parse_args()
    except:
        with open('Help/read.me.reht') as f:
            print(f.read().encode('cp1251').decode())

        return None


if __name__ == '__main__':
    result = get_parsed_cmd_args()
    pass
