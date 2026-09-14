"""
Explicit, deterministic workflow state machine (CLAUDE.md §14).

Required sequence:
    INTAKE -> ADJUDICATION -> EXPLANATION -> VERIFICATION -> CUSTOMER_COMMUNICATION

Forbidden transition: ADJUDICATION -> CUSTOMER_COMMUNICATION (skipping
explanation and verification). This machine is the actual enforcement
mechanism, not a UI-only check: agent orchestration must call
`WorkflowStateMachine.transition` before any customer communication, and
a v2-enforced pipeline raises WorkflowViolation on an illegal transition.
"""
from dataclasses import dataclass, field


REQUIRED_SEQUENCE = [
    "INTAKE",
    "ADJUDICATION",
    "EXPLANATION",
    "VERIFICATION",
    "CUSTOMER_COMMUNICATION",
]

_ALLOWED_TRANSITIONS = {
    REQUIRED_SEQUENCE[i]: REQUIRED_SEQUENCE[i + 1] for i in range(len(REQUIRED_SEQUENCE) - 1)
}


class WorkflowViolation(Exception):
    """Raised when a transition would violate the required workflow sequence."""


@dataclass
class WorkflowState:
    claim_id: str
    current_step: str = "INTAKE"
    explanation_verified: bool = False
    customer_communication_allowed: bool = False
    history: list[dict] = field(default_factory=list)


class WorkflowStateMachine:
    """
    Stateful, per-claim workflow enforcer. `enforce=True` (v2 behavior)
    blocks any transition that skips a required step or that reaches
    CUSTOMER_COMMUNICATION without a verified explanation. `enforce=False`
    (the intentionally controlled v1 weakness, CLAUDE.md §29) allows the
    Adjudication agent to bypass straight to CUSTOMER_COMMUNICATION.
    """

    def __init__(self, claim_id: str, *, enforce: bool = True):
        self.enforce = enforce
        self.state = WorkflowState(claim_id=claim_id)

    def mark_explanation_verified(self) -> None:
        self.state.explanation_verified = True

    def transition(self, to_step: str) -> WorkflowState:
        from_step = self.state.current_step
        expected_next = _ALLOWED_TRANSITIONS.get(from_step)

        # An appeal is a legitimate follow-on stage after customer
        # communication, not part of the linear required sequence itself.
        is_appeal_hop = from_step == "CUSTOMER_COMMUNICATION" and to_step == "APPEAL"
        is_required_sequence_hop = to_step == expected_next or is_appeal_hop
        is_customer_comm_without_verification = (
            to_step == "CUSTOMER_COMMUNICATION"
            and (from_step != "VERIFICATION" or not self.state.explanation_verified)
        )

        if self.enforce:
            if is_customer_comm_without_verification:
                raise WorkflowViolation(
                    f"Blocked transition {from_step} -> CUSTOMER_COMMUNICATION: "
                    "explanation must be generated and verified first."
                )
            if not is_required_sequence_hop:
                raise WorkflowViolation(f"Illegal transition {from_step} -> {to_step}.")

        self.state.history.append({
            "from": from_step,
            "to": to_step,
            "enforced": self.enforce,
            "bypassed_verification": is_customer_comm_without_verification,
        })
        self.state.current_step = to_step
        if to_step == "CUSTOMER_COMMUNICATION":
            # Reaching here with is_customer_comm_without_verification=True is only
            # possible when enforce=False -- the intentionally controlled v1 bypass.
            self.state.customer_communication_allowed = True
        return self.state
