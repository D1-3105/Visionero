from sqlalchemy.orm import DeclarativeBase

from backend.db.setting_pool import DBSettings
from backend.shared.configs import db_parameters

settings_persistent = DBSettings.from_cdp(db_parameters, True)
settings_nonpersistent = DBSettings.from_cdp(db_parameters, False)


async def acreate_persistent_session():
    """
        Dependency func for controllers
    """
    await settings_persistent.ses_obtain_lock.acquire()
    settings_persistent.ses_obtain_lock.release()
    await settings_persistent.async_session_usages.put(1)
    try:
        if not settings_persistent.async_session_class:
            await settings_persistent.asetup()
        yield settings_persistent.ases()
    finally:
        await settings_persistent.async_session_usages.get()
        settings_persistent.async_session_usages.task_done()


async def acreate_session():
    async with settings_nonpersistent.connection_semaphore:
        if not settings_nonpersistent.async_session_class:
            await settings_nonpersistent.asetup()
        async with settings_nonpersistent.async_session_class() as async_session:
            yield async_session
            await async_session.close()
