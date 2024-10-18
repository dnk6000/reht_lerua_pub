""" The main file of reht.ru crawler and parser """

import log
import const
from modules_reht.project_reht import ProjectReht
from cmd_line_parser import get_parsed_cmd_args

import sys
import logging


def parse_args() -> dict:
    res = {'project_name': '', 'clearlog': False}
    for arg in sys.argv[1:]:
        if arg == 'clearlog' or arg == 'clear_log':
            res['clearlog'] = True
        else:
            res['project_name'] = arg
    return res


def check_project_name(project_name_: str) -> str:
    if project_name_ == '':
        logging.getLogger('root').error(
            f"Can't start project. Please, specify the project name in the command line argument")
        return ''

    if 'reht' not in project_name_:
        logging.getLogger('root').error(
            f"The project name '{project_name_}' is not available! Project name must include 'reht' string!")
        return ''

    return project_name_


if __name__ == '__main__':
    app_args = get_parsed_cmd_args()
    if app_args is None:
        sys.exit()

    log.clear_common_log(app_args.clearlog)

    logger = logging.getLogger('root')
    logger.info("Application started")
    logger.info(f"Common log file: {const.COMMON_LOG}")
    logger.info(f"Operation: {app_args.operation}")
    logger.info(f"Project cfg file: {app_args.project_cfg_file}")
    logger.info(f"Result file: {app_args.result_file}")

    project = ProjectReht(app_args.operation, app_args.project_cfg_file, app_args.result_file)

    if not project.options_ok:
        logger.error(f"Incorrect format of project cfg file {app_args.project_cfg_file}")
        sys.exit()

    logger.info(f"Project name: {project.options['project_name']}")

    try:
        match app_args.operation:
            case 'check':    project.check()
            case 'crawl':    project.crawl(app_args)
            case 'crawlall': project.crawlall(app_args)
            case _: logger.info(f"Unknown operation: {app_args.operation}")
    except:
        logging.exception('')

    project.quit()

    logger.info(f"Application finished successfully")
