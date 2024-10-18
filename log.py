import const
import logging
from logging import Logger

from datetime import datetime

class ColoredFormatter(logging.Formatter):
    # ANSI color codes https://main--aroy-art.netlify.app/blog/ansi-color-codes/
    # BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    # GREEN = "\033[0;32m"
    # BROWN = "\033[0;33m"
    # BLUE = "\033[0;34m"
    # PURPLE = "\033[0;35m"
    # CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    # DARK_GRAY = "\033[1;30m"
    # LIGHT_RED = "\033[1;31m"
    # LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[0;93m"
    # LIGHT_BLUE = "\033[1;34m"
    # LIGHT_PURPLE = "\033[1;35m"
    # LIGHT_CYAN = "\033[1;36m"
    # LIGHT_WHITE = "\033[1;37m"
    WHITE = "\033[0;97m"
    BOLD = "\033[1m"
    # FAINT = "\033[2m"
    # ITALIC = "\033[3m"
    # UNDERLINE = "\033[4m"
    # BLINK = "\033[5m"
    # NEGATIVE = "\033[7m"
    # CROSSED = "\033[9m"
    END = "\033[0m"

    def __init__(self, _format):
        super().__init__()

        c = ColoredFormatter

        self.FORMATS = {
            logging.DEBUG:    c.LIGHT_GRAY   + _format + c.END,
            logging.INFO:     c.WHITE        + _format + c.END,
            logging.WARNING:  c.YELLOW       + _format + c.END,
            logging.ERROR:    c.RED          + _format + c.END,
            logging.CRITICAL: c.RED + c.BOLD + _format + c.END
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def init_common_logger() -> None:
    if len(logging.RootLogger.root.handlers) > 0:
        return

    # log_level = logging.DEBUG
    log_level = logging.INFO

    logger = logging.getLogger('root')
    logger.setLevel(log_level)
    logger.propagate = 0

    formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(formatstr)

    fh = logging.FileHandler(const.COMMON_LOG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    if const.LOG_TO_SCREEN:
        ch = logging.StreamHandler()
        # ch.setLevel(logging.INFO)
        formatter = ColoredFormatter(formatstr)
        ch.setFormatter(formatter)
        logger.addHandler(ch)


def clear_common_log(enable: bool):
    if enable:
        f = open(const.COMMON_LOG, 'r+')
        f.truncate(0)


def date_to_str(dt):
    return dt.strftime("%d.%m.%Y %H:%M:%S")


def date_now_str():
    return date_to_str(datetime.now().astimezone())


def debug_error(debug: bool, _logger: Logger, msg: str):
    if debug:
        _logger.error(msg)


init_common_logger()
