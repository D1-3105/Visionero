import asyncio

from fastapi import FastAPI, WebSocket

from backend.websocket_app.background_tasks import notificator_dead_processes, arun_process_scanner, \
    arun_terminated_process_scanner, notificator_active_processes
from backend.shared.serializers import ProcessListSchema

app: FastAPI = FastAPI()


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(arun_process_scanner())
    asyncio.create_task(arun_terminated_process_scanner())


async def aqueue_wrapper(async_queue: asyncio.Queue):
    while True:
        event = await async_queue.get()
        yield event


@app.websocket('/dead_processes/stream')
async def websocket_subscribe_on_process_termination(ws: WebSocket):
    await ws.accept()
    event_q = asyncio.Queue()
    notificator_dead_processes.subscribe(event_q)

    async for event in aqueue_wrapper(event_q):
        msg = ProcessListSchema(**event).model_dump_json()
        await ws.send_text(msg)


@app.websocket('/live_processes/stream')
async def websocket_subscribe_on_process_active(ws: WebSocket):
    await ws.accept()
    event_q = asyncio.Queue()
    notificator_active_processes.subscribe(event_q)

    async for event in aqueue_wrapper(event_q):
        msg = ProcessListSchema(processes=event['delta']).model_dump_json()
        await ws.send_text(msg)
