import logging
import psycopg2


class DataManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
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


class DataObject:
    def __init__(self, table_name: str, data_manager: DataManager):
        self.data_manager = data_manager
        self.table_name = table_name
