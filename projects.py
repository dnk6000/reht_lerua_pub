import configparser
import logging

import common
from log import ColoredFormatter
import const


class Project:

    def __init__(self, operation: str, project_cfg_file: str, result_file: str):
        self.operation = operation
        self.project_cfg_file = project_cfg_file
        self.result_file = result_file

        self.options = {'debug': False,
                        'debug_urls': [],
                        'pause_sec': 2.0,
                        'hide_browser_window': False,
                        'delete_result_file': False}

        self.required_options = ['project_name', 'domain', 'login', 'password', 'log_file']
        for k in self.required_options:
            self.options[k] = ''

        self.options_ok = False  # options filled successfully

        self.init_parameters()

        self.debug = self.options['debug']

    def _load_project_cfg_file(self) -> None:
        logger = logging.getLogger('root')

        config = configparser.ConfigParser()
        res_reading = config.read(self.project_cfg_file)

        if len(res_reading) == 0:
            logger.error(f"Can't find config file {self.project_cfg_file}")
            return

        need_sections = ['common', 'logging', 'debug']
        sections = config.sections()

        if not all([s in sections for s in need_sections]):
            logger.error(f"Incorrect structure of cfg file {self.project_cfg_file}")
            return

        self.options['project_name'] = config['common'].get('project_name', '')
        self.options['log_file'] = config['logging'].get('log_file', f"Log\\{self.options['project_name']}.log")
        self.options['pause_sec'] = config['logging'].get('pause_sec', '2')

        for k in config['common']:
            if config['common'][k] in ['False', 'True', 'false', 'true']:
                self.options[k] = config['common'].getboolean(k)
            else:
                self.options[k] = config['common'][k]

        for k in config['logging']:
            self.options[k] = config['logging'][k]

        for k in config['debug']:
            if k == 'debug':
                self.options[k] = config['debug'].getboolean(k)
            else:
                self.options[k] = config['debug'][k]

        if 'password' in self.options:
            self.options['password'] = self.options['password'].encode('cp1251').decode()

        self.options['pause_sec'] = float(self.options['pause_sec'])

        self.options['debug_urls'] = self.options['debug_urls'].strip()
        if self.options['debug_urls'] != '':
            self.options['debug_urls'] = self.options['debug_urls'].splitlines()

        logger.info(f"Loaded successfully: cfg file {self.project_cfg_file}")

        self.options_ok = True
        for k in self.required_options:
            if self.options[k] is None or str(self.options[k]) == '':
                logger.error(f"Parameter '{k}' not specified")
                self.options_ok = False

    def _setup_logger(self):
        log_level = logging.INFO

        self.logger = logging.getLogger(self.options['project_name'])
        self.logger.setLevel(log_level)
        self.logger.propagate = 0

        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(formatstr)

        fh = logging.FileHandler(self.options['log_file'])
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        fh = logging.FileHandler(self.options['log_file_err'])
        fh.setLevel(logging.ERROR)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        if const.LOG_TO_SCREEN:
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = ColoredFormatter(formatstr)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        # clear log file if it specified in cfg file
        if self.options.get('clear_log', False):
            f = open(self.options['log_file'], 'r+')
            f.truncate(0)
            f = open(self.options['log_file_err'], 'r+')
            f.truncate(0)

        logging.getLogger('root').info(f'Project log file: {self.options['log_file']}')

    def init_parameters(self) -> None:
        self._load_project_cfg_file()

        if not self.options_ok:
            return

        self._setup_logger()

    def make_result_file_bak(self) -> None:
        if self.options['delete_result_file']:
            common.make_file_bak(self.result_file)