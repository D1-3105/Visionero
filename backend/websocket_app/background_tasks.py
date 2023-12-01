import asyncio
import uuid

import fastapi.concurrency

from backend.shared.process_scanner import scan_terminated_processes, LOG_DESC, scan_processes


class NotificationWrapper:
    notify_queues: dict[str, asyncio.Queue]

    def __init__(self):
        self.notify_queues = {}

    def __getitem__(self, item):
        return self.notify_queues[item]

    def subscribe(self, event_q: asyncio.Queue):
        gen_id = uuid.uuid1()
        self.notify_queues[gen_id] = event_q
        return gen_id

    def unsubscribe(self, gen_id):
        self.notify_queues.pop(gen_id)

    async def anotify_event(self, event):
        for gen_id, queue in self.notify_queues.items():
            await queue.put(event)


notificator_dead_processes = NotificationWrapper()
notificator_active_processes = NotificationWrapper()


async def arun_process_scanner():
    current_processes = await fastapi.concurrency.run_in_threadpool(scan_processes)
    await notificator_active_processes.anotify_event(current_processes)
    await asyncio.sleep(1)
    return await arun_process_scanner()


async def arun_terminated_process_scanner():
    current_terminated = await fastapi.concurrency.run_in_threadpool(
        scan_terminated_processes, LOG_DESC
    )
    await notificator_dead_processes.anotify_event(current_terminated)
    await asyncio.sleep(1)
    return await arun_terminated_process_scanner()
