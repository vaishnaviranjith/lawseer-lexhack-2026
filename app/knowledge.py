"""Small transparent knowledge base for the primary LAWSEER demo."""

from .models import Action, Fact, Situation


DEFAULT_ACTIONS = [
    Action(
        id="leave_now",
        title="Leave immediately",
        description="Move out on the requested timeline without first seeking more written detail.",
    ),
    Action(
        id="clarify_first",
        title="Ask for formal clarification",
        description="Request written detail, preserve the record, and confirm the next decision point before acting.",
    ),
]


DEFAULT_FACTS = [
    Fact(
        key="written_agreement_exists",
        label="Written agreement exists",
        value=True,
        source="user-provided demo fact",
        confidence=0.9,
    ),
    Fact(
        key="departure_request_message_exists",
        label="Message requesting departure exists",
        value=True,
        source="user-provided demo fact",
        confidence=0.9,
    ),
    Fact(
        key="requested_departure_days",
        label="Requested departure timeframe",
        value=14,
        source="user-provided demo fact",
        confidence=0.8,
    ),
    Fact(
        key="jurisdiction",
        label="Jurisdiction",
        value="Demo jurisdiction (illustrative only)",
        source="demo setting",
        confidence=0.4,
    ),
    Fact(
        key="formal_notice_received",
        label="Formal notice received",
        value=False,
        source="user-provided demo fact",
        confidence=0.85,
    ),
]


def default_situation() -> Situation:
    """Return a fresh, independent primary demo state."""

    return Situation(
        narrative=(
            "A tenant receives a sudden request from a landlord to leave within a short period. "
            "The tenant is deciding whether to leave now or seek formal clarification first."
        ),
        facts=[fact.model_copy(deep=True) for fact in DEFAULT_FACTS],
        actions=[action.model_copy(deep=True) for action in DEFAULT_ACTIONS],
    )
