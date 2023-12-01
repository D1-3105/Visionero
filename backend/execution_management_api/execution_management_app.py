import datetime

import fastapi.concurrency
from fastapi import FastAPI, Path

from backend.execution_management_api.input_schemas import ExecuteSchema
from backend.shared.process_execution import run_process
from backend.shared.process_scanner import scan_processes
from backend.shared.serializers import ProcessStateListSchema, EventSchema, TerminatedProcessSchema

app: FastAPI = FastAPI()


@app.get('/processes/states')
async def get_process_states() -> ProcessStateListSchema:
    processes = scan_processes()['all']
    return {'processes': processes}


@app.post(
    '/processes/execute/',
    description="Execute process by executable path (WATCH BACKSLASHES)"
)
async def execute_process(execute_info: ExecuteSchema) -> EventSchema:
    pid = await fastapi.concurrency.run_in_threadpool(run_process, execute_info.exe)
    return {'pid': pid, 'executable': execute_info.exe, 'time': datetime.datetime.now()}


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
