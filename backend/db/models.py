
import sqlalchemy as sa

from backend.db.setting_pool import BaseORMModel


class RemoteProcessExecution(BaseORMModel):
    __tablename__ = "remote_process_execution"
    id = sa.Column(sa.Integer, primary_key=True)
    pid = sa.Column(sa.Integer, nullable=False)
    executable = sa.Column(sa.String, nullable=False)
    time= sa.Column(sa.DateTime, nullable=False)
