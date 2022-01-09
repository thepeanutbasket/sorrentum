"""
Tools for handling IM Postgres DB.

Import as:

import im_v2.common.db.utils as imvcodbut
"""
import logging
from typing import Optional

import psycopg2 as psycop

import helpers.hsql_test as hsqltest
import helpers.hsql as hsql
import im.ib.sql_writer as imibsqwri
import im.kibot.sql_writer as imkisqwri
import im_v2.ccxt.db.utils as imvccdbut
import im_v2.im_lib_tasks as imvimlita

_LOG = logging.getLogger(__name__)


def get_common_create_table_query() -> str:
    """
    Get SQL query that is used to create tables for common usage.
    """
    sql_query = """
    CREATE TABLE IF NOT EXISTS Exchange (
        id integer PRIMARY KEY DEFAULT nextval('serial'),
        name text UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Symbol (
        id integer PRIMARY KEY DEFAULT nextval('serial'),
        code text UNIQUE,
        description text,
        asset_class AssetClass,
        start_date date DEFAULT CURRENT_DATE,
        symbol_base text
    );

    CREATE TABLE IF NOT EXISTS TRADE_SYMBOL (
        id integer PRIMARY KEY DEFAULT nextval('serial'),
        exchange_id integer REFERENCES Exchange,
        symbol_id integer REFERENCES Symbol,
        UNIQUE (exchange_id, symbol_id)
    );
    """
    return sql_query


def get_data_types_query() -> str:
    """
    Define custom data types inside a database.
    """
    # Define data types.
    # TODO(Grisha): Futures -> futures.
    # TODO(Grisha): T -> minute, D -> daily.
    query = """
    CREATE TYPE AssetClass AS ENUM ('Futures', 'etfs', 'forex', 'stocks', 'sp_500');
    CREATE TYPE Frequency AS ENUM ('T', 'D', 'tick');
    CREATE TYPE ContractType AS ENUM ('continuous', 'expiry');
    CREATE SEQUENCE serial START 1;
    """
    return query


def create_all_tables(connection: hsql.DbConnection) -> None:
    """
    Create tables inside a database.

    :param connection: a database connection
    """
    queries = [
        get_data_types_query(),
        get_common_create_table_query(),
        imibsqwri.get_create_table_query(),
        imkisqwri.get_create_table_query(),
        imvccdbut.get_ccxt_ohlcv_create_table_query(),
        imvccdbut.get_exchange_name_create_table_query(),
        imvccdbut.get_currency_pair_create_table_query(),
    ]
    # Create tables.
    for query in queries:
        _LOG.debug("Executing query %s", query)
        try:
            cursor = connection.cursor()
            cursor.execute(query)
        except psycop.errors.DuplicateObject:
            _LOG.warning("Duplicate table created, skipping.")


def create_im_database(
    connection: hsql.DbConnection,
    new_db: str,
    overwrite: Optional[bool] = None,
) -> None:
    """
    Create database and SQL schema inside it.

    :param connection: a database connection
    :param new_db: name of database to connect to, e.g. `im_db_local`
    :param overwrite: overwrite existing database
    """
    _LOG.debug("connection=%s", connection)
    hsql.create_database(connection, dbname=new_db, overwrite=overwrite)
    conn_details = hsql.db_connection_to_tuple(connection)
    new_connection = hsql.get_connection(
        host=conn_details.host,
        dbname=new_db,
        port=conn_details.port,
        user=conn_details.user,
        password=conn_details.password,
    )
    create_all_tables(new_connection)
    new_connection.close()


# #############################################################################


class TestImDbHelper(hsqltest.TestDbHelper):
    @staticmethod
    def _get_compose_file() -> str:
        return "im_v2/devops/compose/docker-compose.yml"

    @staticmethod
    def _get_service_name() -> str:
        return "im_postgres"

    @staticmethod
    def _get_db_env_path() -> str:
        """
        See `_get_db_env_path()` in the parent class.
        """
        # Use the `local` stage for testing.
        env_file_path = imvimlita.get_db_env_path("local")
        return env_file_path  # type: ignore[no-any-return]
