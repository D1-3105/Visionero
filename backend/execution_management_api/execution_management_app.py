import datetime
import os
import pathlib

import fastapi.concurrency
from fastapi import FastAPI, Path, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from backend.db.configs import acreate_session, acreate_persistent_session
from backend.db.models import RemoteProcessExecution
from backend.execution_management_api.input_schemas import ExecuteSchema
from backend.shared.process_execution import run_process
from backend.shared.process_scanner import scan_processes
from backend.shared.serializers import ProcessStateListSchema, EventSchema, TerminatedProcessSchema, ProcessListSchema

app: FastAPI = FastAPI()

app.mount("/static", StaticFiles(directory=pathlib.Path(os.getenv('STATIC_ROOT')) / 'static'), name="static")


@app.get("/")
async def read_index():
    return FileResponse(pathlib.Path(os.getenv('STATIC_ROOT')) / 'index.html')


@app.get("/manifest.json")
async def read_index():
    return FileResponse(pathlib.Path(os.getenv('STATIC_ROOT')) / 'manifest.json')


@app.get('/processes/states')
async def get_process_states() -> ProcessStateListSchema:
    processes = await fastapi.concurrency.run_in_threadpool(scan_processes)
    return {'processes': processes}


@app.post(
    '/processes/execute/',
    description="Execute process by executable path (WATCH BACKSLASHES)",
    status_code=201
)
async def execute_process(
        execute_info: ExecuteSchema,
        ases: AsyncSession = Depends(acreate_session)
) -> EventSchema:
    pid = await fastapi.concurrency.run_in_threadpool(run_process, execute_info.exe)
    new_instance = RemoteProcessExecution(pid=pid, executable=execute_info.exe, time=datetime.datetime.now())
    ases.add(new_instance)
    await ases.commit()
    return new_instance


@app.get('/processes/terminate/', status_code=204)
async def terminate_process(pid: int = Path(..., title="PID of process to terminate")):
    await fastapi.concurrency.run_in_threadpool(run_process, f'taskkill /PID {pid} /F')
    return {}


@app.get('/processes/terminate/all')
async def terminate_all_processes() -> TerminatedProcessSchema:
    process_names = ProcessStateListSchema(processes=scan_processes()['all']).processes
    pids = []
    for proc in process_names:
        if (pid := proc.process_state.pid) and proc.executable != 'pycharm64.exe':
            await fastapi.concurrency.run_in_threadpool(run_process, f'taskkill /PID {pid} /F')
            pids.append(pid)
    await fastapi.concurrency.run_in_threadpool(run_process, f'taskkill /F /IM *')
    return {'pids': pids}


@app.get('/processes/history/list')
async def get_history(ases: AsyncSession = Depends(acreate_persistent_session)) -> ProcessListSchema:
    processes_query = select(RemoteProcessExecution).order_by(RemoteProcessExecution.time.desc())
    processes = (await ases.execute(processes_query)).scalars()
    return {'processes': processes}
