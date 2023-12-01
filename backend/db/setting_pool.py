import asyncio
from pathlib import Path
from typing import Type

from sqlalchemy import NullPool, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

BASE_PATH = Path(__file__).parent


class DBSettings:
    """
        From my other project
    """
    CUR_DB_PARAMETERS = None
    CUR_DB_URL = None
    engine = None
    async_session_class: Type[AsyncSession] = None
    sync_session_class: Type[Session] = None
    persistent_ses: AsyncSession
    ses_obtain_lock: asyncio.Lock
    async_session_usages: asyncio.Queue
    connection_semaphore = asyncio.Semaphore(50)


    def __init__(self, is_persistent):
        self.async_session_usages = asyncio.Queue()
        self.ses_obtain_lock = asyncio.Lock()
        self.PERSISTENT_SES = is_persistent

    async def asetup(self):
        self.reset_aengine()
        self.create_ases_class()
        if self.PERSISTENT_SES:
            self.persistent_ses = self.async_session_class()

    def setup(self):
        self.reset_engine()
        self.create_ses_class()
        if self.PERSISTENT_SES:
            self.persistent_ses = self.sync_session_class()

    @staticmethod
    def build_url(cdp):
        return f"{cdp['driver']}://{cdp['user']}:{cdp['password']}@" \
               f"{cdp['host']}:{cdp['port']}/{cdp['dbname']}"

    @classmethod
    def from_cdp(cls, cdp: dict, is_persistent: bool) -> 'DBSettings':
        self = cls(is_persistent)
        self.CUR_DB_URL = self.build_url(cdp)
        self.CUR_DB_PARAMETERS = cdp
        return self

    def reset_aengine(self):
        self.engine = create_async_engine(self.CUR_DB_URL, pool_pre_ping=True, poolclass=NullPool)

    def reset_engine(self):
        self.engine = create_engine(self.CUR_DB_URL, pool_pre_ping=True, poolclass=NullPool)

    def create_ases_class(self):
        self.async_session_class = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )

    def create_ses_class(self):
        self.sync_session_class = sessionmaker(
            self.engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )

    def ases(self):
        if self.PERSISTENT_SES:
            return self.persistent_ses
        else:
            return self.async_session_class()

    def ses(self):
        if self.PERSISTENT_SES:
            return self.persistent_ses
        else:
            return self.sync_session_class()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.engine:
            await self.engine.dispose()


class BaseORMModel(DeclarativeBase):
    ...
