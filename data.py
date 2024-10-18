import pandas as pd
from logging import Logger
from numpy import isnan, nan
import re

import const
import common


class Item:
    def __init__(self, logger: Logger):
        self.logger = logger

    def get_url_id(self, url):
        match = re.findall(r'&cdir=\d*', url)
        if len(match) == 0:
            self.logger.error(f'Cannot get url id from url: {url}')
            return ''
        else:
            return match[0][6:]


class GroupItem(Item):
    def __init__(self, logger: Logger, name: str = '', parent: (Item, str, None) = None, url: str = ''):
        # , parent_url: str = ''
        super().__init__(logger)
        self.id = 0
        self.name = strip_name(name)
        self.parent = parent
        if parent is None:
            self.full_name = self.name
            self.id_parent = -1
            self.parent_url = ''
        elif parent is str:
            self.full_name = parent + ' | ' + self.name
            self.id_parent = -1
            self.parent_url = ''
        else:
            self.full_name = parent.full_name + ' | ' + self.name
            self.id_parent = parent.id
            self.parent_url = parent.url
        self.url = url
        self.url_id = self.get_url_id(url)
        self.updated = common.date_now_str()

    def __str__(self):
        return f'group name: {self.name} || parent: {self.parent} || url: {self.url} || parent_url: {self.parent_url}'


class ProductItem(Item):
    def __init__(self, logger: Logger, articul: str = '', name: str = '', amount: int = 0, unit: str = '',
                 per_pack: int = -1, price: float = 0, parent: GroupItem = None, tab_url: str = '',
                 error: str = '', old_vals: dict = None):
        super().__init__(logger)
        self.id = 0
        self.articul = self._get_default_str('articul', articul, old_vals)
        self.name = self._get_default_str('name', name, old_vals)
        self.unit = self._get_default_str('unit', unit, old_vals)

        try:
            self.amount = self._get_default_float('amount', amount, old_vals)
        except:
            self.amount = 0
            self.logger.error(f"Can't get amount from string: {amount} for articul {self.articul}")
        try:
            if per_pack != -1:
                self.per_pack = self._get_default_int('per_pack', per_pack, old_vals)
            else:
                self.per_pack = 0
        except:
            self.per_pack = 0
            self.logger.error(f"Can't get per_pack from string: {per_pack} for articul {self.articul}")

        str_value = str(price).strip()
        if str_value[-4:] == 'руб.':
            str_value = str_value[:-4]
        elif str_value[-3:] == 'руб':
            str_value = str_value[:-3]
        try:
            self.price = self._get_default_float('price', str_value, old_vals)
        except:
            self.price = 0
            self.logger.error(f"Can't get price from string: {str_value} for articul {self.articul}")

        self.tab_url = self._get_default_str('tab_url', tab_url, old_vals)
        self.parent = self._get_default_str('parent', parent, old_vals)
        self.url_id = self._get_default_str('url_id', self.get_url_id(tab_url), old_vals)

        if type(parent) is GroupItem:
            self.id_group = parent.id
            self.parent_url_id = parent.url_id
        else:
            self.id_group = self._get_default_int('id_group', 0, old_vals)
            self.parent_url_id = self._get_default_str('parent_url_id', '', old_vals)

        self.updated = common.date_now_str()
        self.error = error

    @staticmethod
    def _get_default_str(attr_name: str, val: (int, str), old_vals: dict):
        if val != '' or old_vals is None or attr_name not in old_vals:
            return str(val).strip()
        return str(old_vals[attr_name])

    @staticmethod
    def _get_default_int(attr_name: str, val: (int, str), old_vals: dict):
        if val != 0 or old_vals is None or attr_name not in old_vals:
            return int(str(val).strip())
        return int(old_vals[attr_name])

    @staticmethod
    def _get_default_float(attr_name: str, val: (int, str), old_vals: dict):
        if val != 0 or old_vals is None or attr_name not in old_vals:
            return float(str(val).strip())
        return float(old_vals[attr_name])

    def __str__(self):
        _parent = self.parent.name if type(self.parent) is GroupItem else ''
        return f'{self.articul} || {self.amount} || {self.unit} || {self.per_pack}' \
               f'|| {self.price} || {self.name}  || {_parent} || {self.tab_url}'


class Table:
    def __init__(self, project_name: str, logger: Logger):
        self.df_name = ''
        self.cols = {}
        self.result_cols = None
        self.df = pd.DataFrame()
        self.result_path = const.PATH_TO_INNER_DB
        self.project_name = project_name
        self.logger = logger
        self._cols_zero_values = {}

    def _get_result_file_name(self) -> str:
        return self.result_path + '\\' + self.project_name + '_' + self.df_name + '.csv'

    def _get_row_dict_from_item(self, item: (GroupItem, ProductItem)) -> dict:
        attrs = vars(item)
        row = self.cols.copy()
        for k in row.keys():
            if k in attrs:
                row[k] = getattr(item, k)
            else:
                row[k] = self._cols_zero_values[k]
        return row

    def create_table(self):
        if self.df is None:
            self.df = pd.DataFrame(self.cols)
            # self.df.set_index(['id', 'name'], inplace=True)
        else:
            for col in self.cols:
                if col not in self.df.columns:
                    # self.df.insert(len(self.df.columns), col, [self.cols[col]] * len(self.df.index))
                    # self.df.insert(len(self.df.columns), col, [''] * len(self.df.index))
                    self.df.insert(len(self.df.columns), col, [self._cols_zero_values[col]] * len(self.df.index))
                pass
                # self.cols[col].dtype

    def append(self, item):
        pass

    def save(self) -> None:
        try:
            self.df.to_csv(self._get_result_file_name())
            # self.df.to_excel(self.result_path + '\\' + self.project_name + '_' + self.df_name + '_example.xlsx',
            #                  columns=self.result_cols, index=False)
            # self.df.to_csv(self.result_path + '\\' + self.project_name + '_' + self.df_name + '_example.csv', sep='|',
            #                encoding='cp1251', columns=self.result_cols, index=False)
        except:
            self.logger.exception('')

    def save_df(self, df: pd.DataFrame, fname: str) -> None:
        try:
            df.to_csv(fname, sep=const.CSV_SEPARATOR, encoding='utf-8', columns=self.result_cols, index=False)
        except:
            self.logger.exception('')

    def load(self) -> None:
        try:
            dtypes = {k: self.cols[k].dtype.name for k in self.cols.keys()}
            self.df = pd.read_csv(self._get_result_file_name(), index_col=0, dtype=dtypes, encoding='utf-8')
        except FileNotFoundError:
            self.logger.warning(f'File with groups {self._get_result_file_name()} not found. A new table will be created.')
        except:
            self.logger.exception('')
            raise


class TableGroups(Table):
    def __init__(self, project_name: str, logger: Logger):
        super().__init__(project_name, logger)

        self.df_name = 'groups'

        self.df = None

        self.cols = {'id': pd.Series(dtype='int'),
                     'name': pd.Series(dtype='str'),
                     'id_parent': pd.Series(dtype='int'),
                     'url_id': pd.Series(dtype='str'),
                     'updated': pd.Series(dtype='str'),
                     'full_name': pd.Series(dtype='str')}
        self._cols_zero_values = {'id': 0, 'name': '', 'full_name': '', 'id_parent': 0, 'url_id': '',
                                  'updated': common.date_now_str()}

        self.load()

        self.create_table()

    def append(self, item: GroupItem) -> None:
        new_row = self._get_row_dict_from_item(item)
        row = self.df.loc[self.df['full_name'] == item.full_name]
        its_new = len(row) == 0
        if its_new:
            new_row['id'] = self.df['id'].max()
            new_row['id'] = 0 if isnan(new_row['id']) else new_row['id']+1
            id_row = len(self.df.index)
        else:
            id_row = row.index[0]
            new_row['id'] = row.at[id_row, 'id']

        self.df.loc[id_row] = new_row
        item.id = new_row['id']
        # if item.name not in self.df['name'].values:
        #     self.df.loc[id_row] = new_row
        # row['id'] = 0 if self.df.shape[0] == 0 else self.df['id'].max() + 1
        # self.df.loc[-1] = row
        # df.loc[df['id'].idxmax(), 'sn']  # self.df.idxmax()


class TableProducts(Table):
    def __init__(self, project_name: str, logger: Logger):
        super().__init__(project_name, logger)

        self.df_name = 'products'

        self.df: pd.DataFrame = pd.DataFrame()

        self.cols = {
               'articul': pd.Series(dtype='str'),
               'name': pd.Series(dtype='str'),
               'amount': pd.Series(dtype='float'),
               'unit': pd.Series(dtype='str'),
               'per_pack': pd.Series(dtype='float'),
               'price': pd.Series(dtype='float'),
               'id_group': pd.Series(dtype='int'),
               'updated': pd.Series(dtype='str'),
               'upd_session_id': pd.Series(dtype='int'),
               'url_id': pd.Series(dtype='str'),
               'parent_url_id': pd.Series(dtype='str'),
               'error': pd.Series(dtype='str')
                }
        self._cols_zero_values = {
            'id': 0,
            'articul': '',
            'name': '',
            'amount': 0,
            'unit': '',
            'per_pack': 0,
            'price': 0.0,
            'id_group': 0,
            'url_id': '',
            'parent_url_id': '',
            'updated': common.date_now_str(),
            'upd_session_id': 0,
            'error': ''}
        self.result_cols = ['articul','name','unit','per_pack','price','amount','error']

        self.load()
        self.create_table()

        self.upd_session_id = 1 if len(self.df) == 0 else int(self.df['upd_session_id'].max()) + 1

    def append(self, item: ProductItem) -> None:
        new_row = self._get_row_dict_from_item(item)
        new_row['upd_session_id'] = self.upd_session_id
        row = self.df.loc[self.df['articul'] == item.articul]
        its_new = len(row) == 0
        if its_new:
            id_row = len(self.df.index)
        else:
            id_row = row.index[0]

        self.df.loc[id_row] = new_row

    # def _get_existing_data(self, articul: str, res_dict: dict) -> None:
    #     row = self.df.loc[self.df['articul'] == articul]
    #     if len(row) != 0:
    #         for k in res_dict.keys():
    #             res_dict[k] = row.iloc[0][k]

    def get_existing_data(self, articul: str) -> dict:
        row = self.df.loc[self.df['articul'] == articul]
        if len(row) != 0:
            res = {k: '' if row.iloc[0][k] is nan else row.iloc[0][k] for k in row.columns}
        else:
            res = {k: self._cols_zero_values[k] for k in row.columns}
        return res

def strip_name(name: str) -> str:
    stripped = str(name).replace('АКЦИЯ!', '')
    return stripped.strip()
