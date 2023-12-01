
import sqlalchemy as sa

from backend.db.setting_pool import BaseORMModel


class RemoteProcessExecution(BaseORMModel):
    __tablename__ = "remote_process_execution"
    id: int = sa.Column(sa.Integer, primary_key=True)
    pid: int = sa.Column(sa.Integer, nullable=False)
    executable: str = sa.Column(sa.String, nullable=False)
    time: sa.DateTime = sa.Column(sa.DateTime, nullable=False)
