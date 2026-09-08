"""FastAPI entry point for LAWSEER."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .engine import simulate
from .knowledge import default_situation
from .models import CounterfactualRequest, SimulationRequest, SimulationResult


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="LAWSEER",
    description="A transparent counterfactual decision simulator for an educational civic/legal demo.",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "demo"}


@app.post("/api/simulate", response_model=SimulationResult)
def run_simulation(request: SimulationRequest) -> SimulationResult:
    try:
        return simulate(request.situation)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/counterfactual", response_model=SimulationResult)
def run_counterfactual(request: CounterfactualRequest) -> SimulationResult:
    facts = [fact.model_copy(deep=True) for fact in request.situation.facts]
    target = next((fact for fact in facts if fact.key == request.fact_key), None)
    if target is None:
        raise HTTPException(status_code=422, detail=f"Unknown fact key: {request.fact_key}")
    previous_value = target.value
    target.value = request.new_value
    updated_situation = request.situation.model_copy(update={"facts": facts})
    try:
        return simulate(
            updated_situation,
            changed_fact_key=request.fact_key,
            changed_from=previous_value,
            changed_to=request.new_value,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/demo", response_model=SimulationResult)
def demo_simulation() -> SimulationResult:
    return simulate(default_situation())
