import logging
import psycopg2


def create_table_name(prefix: str, table_name: str):
    return f'{prefix.lower()}_{table_name.lower()}'


def create_schema_from_config(prefix: str, table_name: str, config: dict):
    table_schema = config['tables'][table_name]
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
    return f'create table {create_table_name(prefix, table_name)}({columns_str});'


class DataManager:
    def __init__(self, bot_config):
        self.config = bot_config['data_manager']
        self.logger = logging.getLogger(__name__)
        self.logger.level = logging.INFO
        try:
            self.logger.info('Trying to connect to {user}@{host}:{port}'.format(
                user=self.config['username'], host=self.config['host'], port=self.config['port']))
            self.connection: psycopg2.connection = psycopg2.connect(
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
        self.connection = False

    def setup_cog(self, cog_name: str, working_config: dict):
        if 'tables' not in working_config:
            self.logger.info(f'Skipping table setup for \'{cog_name}\' since there is no \'tables\' field in the config')
            return
        for table_name in working_config['tables']:
            if not self.check_for_table(prefix=cog_name, table_name=table_name):
                self.logger.warning(f'Table {create_table_name(prefix=cog_name, table_name=table_name)} not found, creating from schema')
                with self.connection.cursor() as cursor:
                    cursor.execute(create_schema_from_config(prefix=cog_name, table_name=table_name, config=working_config))
                self.connection.commit()
                self.logger.info(f'Creation of table {create_table_name(prefix=cog_name, table_name=table_name)} successful.')

    def check_for_table(self, prefix: str, table_name: str):
        with self.connection.cursor() as cursor:
            cursor.execute(f'SELECT EXISTS (SELECT FROM pg_tables WHERE tablename  = \'{create_table_name(prefix, table_name)}\');')
            return cursor.fetchone()
