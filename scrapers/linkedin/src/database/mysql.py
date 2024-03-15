import dataclasses
import logging
import os
from typing import Iterator

import aiomysql

from .interface import Database
import models

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Table:
    name: str

    # each entry in this list is (column name, column type)
    columns: list[tuple[str, str]]


tables = [
    Table(
        name="companies",
        columns=[
            ("name", "Varchar(1023) not null"),
            ("url", "Varchar(2047)"),
            ("logo", "Varchar(2047)"),
            ("actively_hiring", "BOOL"),
        ]
    ),
    Table(
        name="locations",
        columns=[
            ("full_location", "Varchar(1023) not null"),
            ("city", "Varchar(1023)"),
            ("region", "Varchar(1023)"),
            ("country", "Varchar(1023)"),
        ]
    ),
    Table(
        name="jobs",
        columns=[
            ("url", "Varchar(2047) not null"),
            ("title", "Varchar(2047) not null"),
            ("description", "Varchar(2047) not null"),
            ("company_id", "int not null"),
            ("location_id", "int not null"),
            ("posted_time", "Varchar(127)"),
            ("tags", "Varchar(1023)"),
            ("criteria", "Varchar(2047)"),
        ]
    ),
]


@dataclasses.dataclass
class DBConnectionData:
    host: str
    port: int
    user: str
    password: str
    dbname: str

    @classmethod
    def from_environment(cls) -> "DBConnectionData":
        """
        Read Database  address, credentials & db name from environments
        """
        # load from environments
        host, port = os.getenv("MYSQL_DB_ADDRESS").split(":")
        user = os.getenv("MYSQL_USER")
        password = os.getenv("MYSQL_PASSWORD")
        dbname = os.getenv("MYSQL_DATABASE")

        # transform port to an int
        # it should raise if the port has not the right format
        try:
            port = int(port)
        except ValueError as e:
            raise ValueError(f"Error: Wrong db port format: {port}!") from e

        return cls(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname
        )


class MySQLClient(Database):
    @classmethod
    async def create(cls):
        """
        __init__ can't be async. This function simulate an async __init__
        It should be called to initialize a Database

        >>> db = await MySQLClient.create()
        """
        self = cls()

        # Read Database  address, credentials & db name from environments
        data = DBConnectionData.from_environment()

        # The password is not logged (even debug) for security reasons
        logger.info(
            f"Connecting to Database=(address={data.host}:{data.port} "
            f"creds={data.user}:xxx dbname={data.dbname} )")

        # create the pool
        self._pool = await aiomysql.create_pool(
            host=data.host, port=data.port,
            user=data.user, password=data.password,
            db=data.dbname, autocommit=False)
        return self

    async def save_jobs(self, jobs: Iterator[models.LinkedInJob]):
        pass
