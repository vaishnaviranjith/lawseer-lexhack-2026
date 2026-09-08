"""Strict API and domain models for the LAWSEER simulator."""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, field_validator


FactValue = Annotated[Union[StrictBool, StrictInt, StrictStr, None], Field(description="A JSON-safe fact value")]


class StrictModel(BaseModel):
    """Reject unknown fields so the decision state stays explicit."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Fact(StrictModel):
    key: StrictStr = Field(min_length=1)
    label: StrictStr = Field(min_length=1)
    value: FactValue
    source: StrictStr | None = None
    confidence: float = Field(default=0.75, ge=0, le=1)


class Action(StrictModel):
    id: StrictStr = Field(min_length=1)
    title: StrictStr = Field(min_length=1)
    description: StrictStr = Field(min_length=1)


class Situation(StrictModel):
    narrative: StrictStr = Field(min_length=1)
    facts: list[Fact] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)

    @field_validator("facts")
    @classmethod
    def unique_fact_keys(cls, facts: list[Fact]) -> list[Fact]:
        keys = [fact.key for fact in facts]
        if len(keys) != len(set(keys)):
            raise ValueError("fact keys must be unique")
        return facts


class Constraint(StrictModel):
    id: StrictStr = Field(min_length=1)
    title: StrictStr = Field(min_length=1)
    detail: StrictStr = Field(min_length=1)
    status: Literal["relevant", "uncertain", "clear"]
    based_on: list[StrictStr] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class EvidenceItem(StrictModel):
    id: StrictStr = Field(min_length=1)
    label: StrictStr = Field(min_length=1)
    status: Literal["supported", "missing", "uncertain"]
    why: StrictStr = Field(min_length=1)
    source_hint: StrictStr | None = None
    strength: int = Field(ge=0, le=100)


class Consequence(StrictModel):
    id: StrictStr = Field(min_length=1)
    title: StrictStr = Field(min_length=1)
    detail: StrictStr = Field(min_length=1)
    kind: Literal["process", "evidence", "timing", "uncertainty"]
    confidence: float = Field(ge=0, le=1)
    depends_on: list[StrictStr] = Field(default_factory=list)


class ScenarioStep(StrictModel):
    label: StrictStr = Field(min_length=1)
    detail: StrictStr = Field(min_length=1)
    tone: Literal["state", "action", "possible", "evidence", "uncertainty"]


class ScenarioBranch(StrictModel):
    id: StrictStr = Field(min_length=1)
    action: Action
    headline: StrictStr = Field(min_length=1)
    summary: StrictStr = Field(min_length=1)
    steps: list[ScenarioStep] = Field(min_length=1)
    consequences: list[Consequence] = Field(min_length=1)
    evidence_required: list[EvidenceItem] = Field(default_factory=list)
    uncertainty_score: int = Field(ge=0, le=100)
    uncertainty_label: Literal["lower", "moderate", "higher"]
    dependencies: list[StrictStr] = Field(default_factory=list)
    changed_fact_keys: list[StrictStr] = Field(default_factory=list)


class DecisionComparison(StrictModel):
    action_id: StrictStr
    action_title: StrictStr
    possible_consequences: list[StrictStr] = Field(min_length=1)
    evidence_required: list[StrictStr] = Field(default_factory=list)
    uncertainty: StrictStr
    dependencies: list[StrictStr] = Field(default_factory=list)
    suggested_next_step: StrictStr = Field(min_length=1)


class SimulationResult(StrictModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: StrictStr = Field(min_length=8)
    mode: Literal["demo", "provider"]
    normalized_situation: Situation
    missing_or_uncertain_facts: list[Fact] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    branches: list[ScenarioBranch] = Field(min_length=1)
    comparison: list[DecisionComparison] = Field(min_length=1)
    supported_evidence: list[EvidenceItem] = Field(default_factory=list)
    missing_evidence: list[EvidenceItem] = Field(default_factory=list)
    uncertain_evidence: list[EvidenceItem] = Field(default_factory=list)
    next_steps: list[StrictStr] = Field(min_length=1)
    changed_fact_key: StrictStr | None = None
    changed_from: FactValue = None
    changed_to: FactValue = None
    changed_because: StrictStr | None = None
    graph_changed: StrictBool = False


class SimulationRequest(StrictModel):
    situation: Situation


class CounterfactualRequest(StrictModel):
    situation: Situation
    fact_key: StrictStr = Field(min_length=1)
    new_value: FactValue
