from pydantic import BaseModel


class ExecuteSchema(BaseModel):
    exe: str
