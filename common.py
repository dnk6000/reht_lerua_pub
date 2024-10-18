import datetime
from typing import Any
import logging
import os

def date_to_str(dt):
    return dt.strftime("%d.%m.%Y %H:%M:%S")


def str_to_date(dt_str):
    return datetime.datetime.strptime(dt_str, "%d.%m.%Y %H:%M:%S")


def date_now_str():
    return date_to_str(datetime.datetime.now().astimezone())


def date_now():
    return datetime.datetime.now()


def fillvals(receiver: Any, source: Any, attrs: dict = None) -> None:
    rec_is_dict = type(receiver) is dict
    src_is_dict = type(source) is dict

    if attrs is None:
        attrs = receiver if rec_is_dict else attrs == vars(receiver)
    attrs_src = source if src_is_dict else attrs == vars(source)

    for k in attrs:
        if k in attrs_src:
            if rec_is_dict:
                receiver[k] = attrs_src[k]
            else:
                setattr(receiver, k, attrs_src[k])


def make_file_bak(fname):
    logger = logging.getLogger('root')
    fname_new = fname+".bak"

    if not os.path.exists(fname):
        return

    if os.path.exists(fname_new):
        try:
            os.remove(fname_new)
        except PermissionError:
            logger.error(f"Permission denied: unable to delete {fname_new}.")
        except Exception as e:
            logger.exception(f"An error occurred while deleting the file: {e}")

    try:
        os.rename(fname, fname_new)
        logger.info(f"File {fname} has been deleted successfully.")
    except PermissionError:
        logger.error(f"Permission denied: unable to rename {fname}.")
    except Exception as e:
        logger.exception(f"An error occurred while renaming the file: {e}")
