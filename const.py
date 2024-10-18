import os
import sys

COMMON_LOG = 'Log\\common.log'
LOG_TO_SCREEN = True
PATH_TO_INNER_DB = 'DB'  # without \ at the end

def get_path_of_current_file() -> str:
    exe_path = sys.executable
    if exe_path.endswith('python.exe') or exe_path.endswith('python3.exe'):
        return os.path.dirname(os.path.abspath(__file__))+'\\'
    else:
        exe_dir = os.path.dirname(exe_path)
        return exe_dir+'\\'

    # return False

CHROMEDRIVER_DIR = get_path_of_current_file()
os.environ['CHROMEDRIVER_DIR'] = CHROMEDRIVER_DIR

CSV_SEPARATOR = chr(167)  # 167 is paragraph  +  available tilda symbol ~


class Errors:
    No_error = ''
    Unclassified = 'unclassified'
    Not_found = 'not found'
    Url_not_found = 'url not found'
    Out_of_stock = 'out of stock'
    Bad_url = 'bad url'
    Exception_on_search_page = 'exception on search page'
    Exception_on_product_page = 'exception on product page'


