"""
FastAPI REST API Server for Shock Index Modified Calculator.
"""
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from shock_index import calculate_shock_index
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Shock Index Modified Calculator API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


class CalculateRequest(BaseModel):
    hr: float = Field(gt=0, allow_inf_nan=False)
    sbp: float = Field(gt=0, allow_inf_nan=False)
    dbp: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    age: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    sex: Optional[str] = None

    @model_validator(mode="after")
    def validate_bp(self):
        if self.dbp is not None and self.dbp > self.sbp:
            raise ValueError("DBP cannot exceed SBP")
        return self


@app.post("/api/calculate")
def api_calculate(payload: CalculateRequest):
    """A stateless numerical endpoint, without storing patient inputs."""
    try:
        return calculate_shock_index(
            payload.hr, payload.sbp, dbp=payload.dbp,
            age=payload.age, sex=payload.sex
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "shock-index-modified-calculator", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# Mounted last so existing REST routes keep precedence. Also makes the same
# self-contained UI available locally, without coupling its math to the API.
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "web"), html=True), name="web")
