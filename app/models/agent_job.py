from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.db.session import Base


class AgentJob(Base):
    __tablename__ = "agent_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    workflow_key = Column(String(64), nullable=False, index=True)
    org_id = Column(Integer, nullable=False, default=1)
    workspace_id = Column(Integer, nullable=False, index=True)

    # pending | running | succeeded | failed | cancelled
    status = Column(String(32), nullable=False, default="pending", index=True)

    input_payload = Column(JSON, nullable=True)
    output_payload = Column(JSON, nullable=True)
    report_payload = Column(JSON, nullable=True)

    error_summary = Column(Text, nullable=True)
    steps_log = Column(JSON, nullable=True)

    etl_run_id = Column(Integer, nullable=True)
    correlation_id = Column(String(100), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
