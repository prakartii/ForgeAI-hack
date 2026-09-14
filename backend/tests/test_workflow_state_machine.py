import pytest

from app.workflow.state_machine import WorkflowStateMachine, WorkflowViolation


def test_enforced_machine_follows_required_sequence():
    wf = WorkflowStateMachine("CLAIM_1", enforce=True)
    wf.transition("ADJUDICATION")
    wf.transition("EXPLANATION")
    wf.transition("VERIFICATION")
    wf.mark_explanation_verified()
    state = wf.transition("CUSTOMER_COMMUNICATION")
    assert state.current_step == "CUSTOMER_COMMUNICATION"
    assert state.customer_communication_allowed is True


def test_enforced_machine_blocks_adjudication_to_customer_communication_bypass():
    wf = WorkflowStateMachine("CLAIM_2", enforce=True)
    wf.transition("ADJUDICATION")
    with pytest.raises(WorkflowViolation):
        wf.transition("CUSTOMER_COMMUNICATION")


def test_enforced_machine_blocks_communication_without_verified_explanation():
    wf = WorkflowStateMachine("CLAIM_3", enforce=True)
    wf.transition("ADJUDICATION")
    wf.transition("EXPLANATION")
    wf.transition("VERIFICATION")
    # explanation_verified was never set
    with pytest.raises(WorkflowViolation):
        wf.transition("CUSTOMER_COMMUNICATION")


def test_unenforced_machine_allows_the_controlled_v1_bypass():
    wf = WorkflowStateMachine("CLAIM_4", enforce=False)
    wf.transition("ADJUDICATION")
    state = wf.transition("CUSTOMER_COMMUNICATION")
    assert state.customer_communication_allowed is True
    assert state.history[-1]["bypassed_verification"] is True


def test_appeal_is_allowed_after_customer_communication():
    wf = WorkflowStateMachine("CLAIM_5", enforce=True)
    wf.transition("ADJUDICATION")
    wf.transition("EXPLANATION")
    wf.transition("VERIFICATION")
    wf.mark_explanation_verified()
    wf.transition("CUSTOMER_COMMUNICATION")
    state = wf.transition("APPEAL")
    assert state.current_step == "APPEAL"
