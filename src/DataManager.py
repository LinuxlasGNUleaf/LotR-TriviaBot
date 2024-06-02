import logging
from typing import Callable

import psycopg2


def create_table_name(prefix: str, table_name: str):
    return f'{prefix.lower()}_{table_name.lower()}'


def create_schema_from_config(prefix: str, table_name: str, config: dict):
    table_schema: dict = config['tables'][table_name]
    columns_str: str = ''

    for col_name, col_settings in table_schema.items():
        col_type = col_settings['type']
        default = col_settings.get('default', None)
        columns_str += f'{col_name} {col_type}'
        if default is not None:
            columns_str += f' default '
            if isinstance(default, str):
                columns_str += f'\'{default}\''
            else:
                columns_str += f'{default}'
        columns_str += ','

    columns_str = columns_str[:-1]
    return f'CREATE TABLE {create_table_name(prefix, table_name)}({columns_str});'


def wrap(obj: object):
    if isinstance(obj, str):
        return repr(obj)
    else:
        return str(obj)


class DataManager:
    def __init__(self, bot_config: dict):
        self.config = bot_config['data_manager']
        self.logger = logging.getLogger(__name__)
        self.logger.level = logging.INFO
        try:
            self.logger.info('Trying to connect to {user}@{host}:{port}'.format(
                user=self.config['username'], host=self.config['host'], port=self.config['port']))
            self.connection = psycopg2.connect(
                database='postgres',
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['username'],
                password=self.config['password']
            )
            self.logger.info(f'PostgreSQL DB connection established, server version: {self.connection.server_version}')
        except psycopg2.OperationalError as exc:
            raise exc

    def disconnect(self):
        self.connection.close()

    def setup_cog(self, cog_name: str, working_config: dict):
        if 'tables' not in working_config:
            self.logger.info(
                f'Skipping table setup for \'{cog_name}\' since there is no \'tables\' field in the config')
            return

        # check if all configured tables exist and create them if necessary
        self.logger.info(f'Checking configured tables for \'{cog_name}\'')
        for table_name in working_config['tables']:
            if not self.check_for_table(prefix=cog_name, table_name=table_name):
                self.logger.warning(
                    f'Table {create_table_name(prefix=cog_name, table_name=table_name)} not found, creating from schema')
                with self.connection.cursor() as cursor:
                    cursor.execute(
                        create_schema_from_config(prefix=cog_name, table_name=table_name, config=working_config))
                self.connection.commit()
                self.logger.info(
                    f'Creation of table {create_table_name(prefix=cog_name, table_name=table_name)} successful')

        data = {}
        for table_name in working_config['tables']:
            data[table_name] = DataInterface(create_table_name(prefix=cog_name, table_name=table_name), self)
        return data

    def check_for_table(self, prefix: str, table_name: str):
        with self.connection.cursor() as cursor:
            cursor.execute(
                f'SELECT EXISTS (SELECT FROM pg_tables WHERE tablename  = \'{create_table_name(prefix, table_name)}\');')
            return cursor.fetchone()[0]


class DataInterface:
    def __init__(self, table_name: str, data_mgr: DataManager):
        self.table_name: str = table_name
        self.data_mgr: DataManager = data_mgr
        self.connection = data_mgr.connection

    def __contains__(self, item: int):
        return self.get_row(item) is not None

    def get(self, uid: int, columns: list[str] | str):
        if columns == '*':
            pass
        elif isinstance(columns, str):
            columns: str = columns
            return_single = True
        else:
            columns = ','.join(columns)
            return_single = False

        with self.data_mgr.connection.cursor() as cursor:
            cursor.execute(f'SELECT {columns} FROM {self.table_name} WHERE uid = {uid}')
            res = cursor.fetchone()

        if columns == '*':
            return res[1:] if res else res
        elif return_single:
            return res[0] if res else res
        else:
            return res

    def get_row(self, uid: int):
        return self.get(uid, '*')

    def get_rows(self, uids: list[int] = None):
        with self.data_mgr.connection.cursor() as cursor:
            if uids:
                cursor.execute(
                    f'SELECT * FROM {self.table_name} WHERE {col_name} = ({",".join(str(uid) for uid in uids)})')
            else:
                cursor.execute(f'SELECT * FROM {self.table_name}')
            return cursor.fetchall()

    def keys(self):
        with self.data_mgr.connection.cursor() as cursor:
            cursor.execute(f'SELECT uid FROM {self.table_name}')
            return [element[0] for element in cursor.fetchall()]

    def set(self, uid: int, field: str, val: object):
        with self.data_mgr.connection.cursor() as cursor:
            cursor.execute(f"UPDATE {self.table_name} SET {field}={wrap(val)} WHERE uid={uid}")
        self.connection.commit()

    def add(self, uid: int, field: str, delta: object):
        """
        adds delta to the column field for the specified UID
        """
        with self.data_mgr.connection.cursor() as cursor:
            cursor.execute(f"UPDATE {self.table_name} SET {field}={field}+{delta} WHERE uid={uid}")
        self.connection.commit()

    def add_row(self, uid):
        with self.data_mgr.connection.cursor() as cursor:
            cursor.execute(f"INSERT INTO {self.table_name} (uid) VALUES ({uid})")
        self.connection.commit()

    def delete_row(self, uid):
        with self.data_mgr.connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {self.table_name} WHERE uid={uid}")
        self.connection.commit()