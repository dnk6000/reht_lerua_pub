import pauser
from data import GroupItem, ProductItem
import const

from logging import Logger
from collections import deque
from dataclasses import dataclass
from typing import Callable


class Crawler:
    def __init__(self,
                 domain: str,
                 login: str = None,
                 password: str = None,
                 logger: Logger = None,
                 pause_sec: int = 2):
        self.domain = domain
        self.login = login
        self.password = password
        self.logger = logger

        self.queue = deque()

        self.pauser = pauser.IntervalPauser(pause_sec)

    def crawl_queue(self):
        pass

    def quit(self):
        pass


@dataclass
class QueueElem:
    item: (GroupItem, ProductItem, str) = None
    func: Callable = None
    url: str = ''
    groups_on: bool = True
    products_on: bool = True
    error: str = ''

    def __post_init__(self):
        if self.url == '' and type(self.item) is GroupItem:
            self.url = self.item.url

    def __str__(self):
        if type(self.item) is str:
            return f'Noname queue item. Url: {self.item}'
        else:
            return f'{self.item.name}  Url: {self.item.url}'
