"""Deterministic counterfactual decision engine for the LAWSEER demo."""

import hashlib
import json
from collections.abc import Mapping

from .knowledge import DEFAULT_ACTIONS
from .models import (
    Action,
    Consequence,
    Constraint,
    DecisionComparison,
    EvidenceItem,
    Fact,
    ScenarioBranch,
    ScenarioStep,
    SimulationResult,
    Situation,
)
from .providers import get_reasoning_provider


def _fact_map(situation: Situation) -> dict[str, Fact]:
    return {fact.key: fact for fact in situation.facts}


def _value(facts: Mapping[str, Fact], key: str, default: object = None) -> object:
    fact = facts.get(key)
    return default if fact is None else fact.value


def _bool(facts: Mapping[str, Fact], key: str, default: bool = False) -> bool:
    value = _value(facts, key, default)
    return value if isinstance(value, bool) else default


def _int(facts: Mapping[str, Fact], key: str, default: int | None = None) -> int | None:
    value = _value(facts, key, default)
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _str(facts: Mapping[str, Fact], key: str, default: str = "") -> str:
    value = _value(facts, key, default)
    return value if isinstance(value, str) else default


def _uncertainty_label(score: int) -> str:
    if score < 35:
        return "lower"
    if score < 60:
        return "moderate"
    return "higher"


def _evidence(
    evidence_id: str,
    label: str,
    status: str,
    why: str,
    strength: int,
    source_hint: str = "Keep a dated copy; confirm against an official source where relevant.",
) -> EvidenceItem:
    return EvidenceItem(
        id=evidence_id,
        label=label,
        status=status,
        why=why,
        strength=strength,
        source_hint=source_hint,
    )


def _build_evidence(facts: Mapping[str, Fact], action_id: str) -> list[EvidenceItem]:
    message_exists = _bool(facts, "departure_request_message_exists")
    agreement_exists = _bool(facts, "written_agreement_exists")
    formal_notice = _bool(facts, "formal_notice_received")
    items = [
        _evidence(
            "departure-message",
            "Requesting message and date",
            "supported" if message_exists else "missing",
            "Shows what was asked, when it was asked, and the communication channel.",
            82 if message_exists else 0,
        ),
        _evidence(
            "written-agreement",
            "Written agreement or record of terms",
            "supported" if agreement_exists else "missing",
            "May help establish the terms the simulator should compare with the request.",
            86 if agreement_exists else 0,
        ),
        _evidence(
            "formal-notice-record",
            "Formal notice record or confirmation of its status",
            "supported" if formal_notice else "uncertain",
            "Changes which procedural path is worth checking next; this demo does not decide validity.",
            78 if formal_notice else 22,
        ),
    ]
    if action_id == "leave_now":
        items.append(
            _evidence(
                "move-out-timeline",
                "Move-out date and handover record",
                "uncertain",
                "Clarifies what happened if the parties later remember the timeline differently.",
                34,
            )
        )
    else:
        items.append(
            _evidence(
                "written-clarification",
                "Written clarification request and any response",
                "missing",
                "Creates a clear record of what was asked before choosing a next action.",
                0,
            )
        )
    return items


def _constraints(facts: Mapping[str, Fact]) -> list[Constraint]:
    agreement_exists = _bool(facts, "written_agreement_exists")
    message_exists = _bool(facts, "departure_request_message_exists")
    formal_notice = _bool(facts, "formal_notice_received")
    timeframe = _int(facts, "requested_departure_days")
    jurisdiction = _str(facts, "jurisdiction")
    return [
        Constraint(
            id="terms-availability",
            title="Terms availability",
            detail=(
                "A written agreement is present in the state, but the demo does not interpret its terms."
                if agreement_exists
                else "No written agreement is recorded, so key terms may be harder to verify."
            ),
            status="clear" if agreement_exists else "uncertain",
            based_on=["written_agreement_exists"],
            confidence=0.84 if agreement_exists else 0.46,
        ),
        Constraint(
            id="communication-record",
            title="Communication record",
            detail=(
                "The departure request has a recorded message in this scenario."
                if message_exists
                else "No written departure request is recorded in this scenario."
            ),
            status="clear" if message_exists else "uncertain",
            based_on=["departure_request_message_exists"],
            confidence=0.86 if message_exists else 0.4,
        ),
        Constraint(
            id="procedural-status",
            title="Procedural status",
            detail=(
                "A formal notice is marked received; its meaning, validity, and required response still need verification."
                if formal_notice
                else "Formal notice is marked not received; whether one is required or pending depends on the jurisdiction and facts."
            ),
            status="relevant" if formal_notice else "uncertain",
            based_on=["formal_notice_received", "jurisdiction"],
            confidence=0.64 if formal_notice else 0.42,
        ),
        Constraint(
            id="time-pressure",
            title="Time pressure",
            detail=(
                f"The requested timeline is {timeframe} days; the simulator treats a short timeline as a coordination dependency, not a legal conclusion."
                if timeframe is not None
                else "The requested timeline is not recorded."
            ),
            status="relevant" if timeframe is not None and timeframe <= 30 else "uncertain",
            based_on=["requested_departure_days"],
            confidence=0.78 if timeframe is not None else 0.35,
        ),
    ]


def _branch(
    action: Action,
    facts: Mapping[str, Fact],
    changed_keys: list[str],
) -> ScenarioBranch:
    message_exists = _bool(facts, "departure_request_message_exists")
    agreement_exists = _bool(facts, "written_agreement_exists")
    formal_notice = _bool(facts, "formal_notice_received")
    timeframe = _int(facts, "requested_departure_days")
    timeframe_label = f"within {timeframe} days" if timeframe is not None else "within the stated short period"
    evidence = _build_evidence(facts, action.id)

    if action.id == "leave_now":
        score = 48
        score += 17 if not agreement_exists else 0
        score += 10 if not message_exists else 0
        score -= 9 if formal_notice else 0
        consequences = [
            Consequence(
                id="quick-exit",
                title="A quick exit may reduce immediate coordination pressure",
                detail=f"The tenant follows the request and aims to leave {timeframe_label}; the practical result still depends on logistics and documented handover.",
                kind="timing",
                confidence=0.72,
                depends_on=["requested_departure_days"],
            ),
            Consequence(
                id="record-before-exit",
                title="The record may be thinner before the decision",
                detail="Leaving first can reduce the opportunity to organize the request, terms, and response in one dated record.",
                kind="evidence",
                confidence=0.7,
                depends_on=["departure_request_message_exists", "written_agreement_exists"],
            ),
            Consequence(
                id="procedural-clarity-leave",
                title=(
                    "The received notice becomes a key reference point"
                    if formal_notice
                    else "The procedural status remains a question to verify"
                ),
                detail=(
                    "The scenario includes a formal notice, but it does not determine whether the notice is sufficient or what response is expected."
                    if formal_notice
                    else "The scenario does not include a formal notice; a later disagreement about process may be harder to reconstruct."
                ),
                kind="process",
                confidence=0.58 if formal_notice else 0.44,
                depends_on=["formal_notice_received", "jurisdiction"],
            ),
        ]
        dependencies = [
            "The actual terms and condition of the written agreement",
            "Whether the request is meant to be a formal notice in this jurisdiction",
            "A dated move-out and handover record",
        ]
        next_step = "Before acting, preserve the request, agreement, and a dated handover record; verify the process with an official or qualified source."
        headline = "Fastest path, least procedural clarification"
        summary = "This branch prioritizes immediate movement while leaving more questions to verify afterward."
    else:
        score = 27
        score += 15 if not agreement_exists else 0
        score += 11 if not message_exists else 0
        score -= 8 if formal_notice else 0
        consequences = [
            Consequence(
                id="clarify-record",
                title="A written clarification trail may form",
                detail=(
                    "The tenant can ask what the request means, what date is being proposed, and which document or process is being relied on."
                ),
                kind="evidence",
                confidence=0.78,
                depends_on=["departure_request_message_exists", "formal_notice_received"],
            ),
            Consequence(
                id="clarify-time",
                title="Time may be used to confirm the next decision point",
                detail="A clarification step can create a short coordination delay; that may help or hurt depending on the requested timeline and response.",
                kind="timing",
                confidence=0.68,
                depends_on=["requested_departure_days"],
            ),
            Consequence(
                id="procedural-clarity-ask",
                title=(
                    "The recorded notice can be compared with the request"
                    if formal_notice
                    else "The response can surface whether a formal notice is intended"
                ),
                detail=(
                    "The scenario includes a formal notice, so the next question is what it says and which response or review route applies."
                    if formal_notice
                    else "The scenario does not include a formal notice, so a written question may make that dependency visible."
                ),
                kind="process",
                confidence=0.67 if formal_notice else 0.54,
                depends_on=["formal_notice_received", "jurisdiction"],
            ),
        ]
        dependencies = [
            "A clear written question and any response",
            "The actual terms and condition of the written agreement",
            "The official process for this jurisdiction",
        ]
        next_step = "Ask for the request, relevant document, and proposed timeline in writing; keep copies and verify the next step with an official or qualified source."
        headline = "More clarity before commitment"
        summary = "This branch prioritizes a written record and makes its procedural dependencies visible before acting."

    steps = [
        ScenarioStep(label="Current state", detail="Tenant is deciding how to respond to a sudden departure request.", tone="state"),
        ScenarioStep(label=action.title, detail=action.description, tone="action"),
        ScenarioStep(label="Possible consequence", detail=consequences[0].detail, tone="possible"),
        ScenarioStep(label="Evidence needed", detail=evidence[0].label, tone="evidence"),
        ScenarioStep(label="Uncertainty", detail=f"{_uncertainty_label(score).capitalize()} uncertainty ({score}/100)", tone="uncertainty"),
    ]
    return ScenarioBranch(
        id=f"branch-{action.id}",
        action=action,
        headline=headline,
        summary=summary,
        steps=steps,
        consequences=consequences,
        evidence_required=evidence,
        uncertainty_score=max(0, min(100, score)),
        uncertainty_label=_uncertainty_label(score),
        dependencies=dependencies,
        changed_fact_keys=changed_keys,
    )


def _normalize(situation: Situation) -> Situation:
    actions = situation.actions or [action.model_copy(deep=True) for action in DEFAULT_ACTIONS]
    return situation.model_copy(deep=True, update={"actions": actions})


def _simulation_id(situation: Situation) -> str:
    payload = json.dumps(situation.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def simulate(
    situation: Situation,
    *,
    changed_fact_key: str | None = None,
    changed_from: object = None,
    changed_to: object = None,
) -> SimulationResult:
    """Run the explicit pipeline: normalize, constrain, branch, propagate, compare."""

    normalized = _normalize(situation)
    provider = get_reasoning_provider()
    facts = _fact_map(normalized)
    changed_keys = [changed_fact_key] if changed_fact_key else []
    missing_or_uncertain: list[Fact] = []
    for key in ("written_agreement_exists", "departure_request_message_exists", "requested_departure_days", "jurisdiction", "formal_notice_received"):
        fact = facts.get(key)
        if fact is None or fact.value is None or fact.confidence < 0.55:
            if fact is not None:
                missing_or_uncertain.append(fact.model_copy(update={"confidence": min(fact.confidence, 0.5)}))
    if not _bool(facts, "written_agreement_exists"):
        missing_or_uncertain.append(
            Fact(key="agreement-content", label="Content of written terms", value=None, source="not supplied", confidence=0.25)
        )
    branches = [_branch(action, facts, changed_keys) for action in normalized.actions]
    if len(branches) < 2:
        raise ValueError("the demo requires at least two actions")
    all_evidence: list[EvidenceItem] = []
    for branch in branches:
        for item in branch.evidence_required:
            if item.id not in {existing.id for existing in all_evidence}:
                all_evidence.append(item)
    comparison = [
        DecisionComparison(
            action_id=branch.action.id,
            action_title=branch.action.title,
            possible_consequences=[consequence.title for consequence in branch.consequences],
            evidence_required=[item.label for item in branch.evidence_required if item.status != "supported"],
            uncertainty=f"{branch.uncertainty_label.capitalize()} ({branch.uncertainty_score}/100)",
            dependencies=branch.dependencies,
            suggested_next_step=(
                "Preserve the request and timeline before committing. " + branch.dependencies[0] + "."
                if branch.action.id == "leave_now"
                else "Put the clarification request in writing, then check the official process."
            ),
        )
        for branch in branches
    ]
    supported = [item for item in all_evidence if item.status == "supported"]
    missing = [item for item in all_evidence if item.status == "missing"]
    uncertain = [item for item in all_evidence if item.status == "uncertain"]
    next_steps = [
        "Keep the original message, attachments, and dates together; do not rely on memory alone.",
        "Compare the request with the written agreement without assuming either one settles the issue.",
        "Verify the relevant process with an official source or qualified professional before an irreversible step.",
    ]
    changed_because = None
    graph_changed = changed_fact_key is not None
    if changed_fact_key:
        changed_because = (
            f"Changing '{next((fact.label for fact in normalized.facts if fact.key == changed_fact_key), changed_fact_key)}' "
            "changes the procedural-status constraint, evidence status, and downstream consequence descriptions."
        )
    return SimulationResult(
        simulation_id=_simulation_id(normalized),
        mode="provider" if provider.mode == "provider" else "demo",
        normalized_situation=normalized,
        missing_or_uncertain_facts=missing_or_uncertain,
        constraints=_constraints(facts),
        branches=branches,
        comparison=comparison,
        supported_evidence=supported,
        missing_evidence=missing,
        uncertain_evidence=uncertain,
        next_steps=next_steps,
        changed_fact_key=changed_fact_key,
        changed_from=changed_from,
        changed_to=changed_to,
        changed_because=changed_because,
        graph_changed=graph_changed,
    )
