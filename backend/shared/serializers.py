import datetime
from typing import Literal

from pydantic import BaseModel


class EventSchema(BaseModel):
    pid: int
    executable: str
    time: datetime.datetime

    class Config:
        from_attributes = True


class ProcessListSchema(BaseModel):
    processes: list[EventSchema]

    class Config:
        from_attributes = True


class ProcessWithStateSchema(BaseModel):
    class ProcessStateSchema(BaseModel):
        pid: int | None
        state: Literal['running', 'idle']

    executable: str
    process_state: ProcessStateSchema


class ProcessStateListSchema(BaseModel):
    processes: list[ProcessWithStateSchema]


class TerminatedProcessSchema(BaseModel):
    pids: list[int]
