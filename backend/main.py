import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import uvicorn

from alembic import command
from alembic.config import Config

from backend.websocket_app.websocket_app import app as websocket_app
from backend.execution_management_api.execution_management_app import app as execution_management_app


BASE_PATH = Path(__file__).parent


def run_alembic():
    alembic_cfg = Config(os.getenv('ALEMBIC_INI'))
    command.upgrade(alembic_cfg, "head")


def run_websocket_application():
    uvicorn.run(websocket_app, host="localhost", port=8005)


def run_execution_management_api():
    uvicorn.run(execution_management_app, host="localhost", port=8006)


if __name__ == '__main__':
    """
        Separate apps for each FastAPI application to avoid race conditions
    """
    run_alembic()
    with ProcessPoolExecutor(max_workers=2) as executor:
        executor.submit(run_websocket_application)
        executor.submit(run_execution_management_api).done()  # infinite wait

