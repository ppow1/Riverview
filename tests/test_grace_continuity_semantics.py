from uuid import uuid4

from riverview.reasoning.home_runtime import invocation_for_message


def test_conversational_history_is_not_a_prior_governed_decision():
    invocation = invocation_for_message(instruction="Continue", correlation_id=uuid4(), classification="operational", prior_history=("resident: Earlier answer",))
    assert invocation.relevant_prior_decisions == ()
    assert invocation.conversation_context == ("resident: Earlier answer",)


def test_multiple_bounded_turns_remain_conversation_context():
    history = tuple(f"resident: bounded turn {index}" for index in range(3))
    invocation = invocation_for_message(instruction="Continue", correlation_id=uuid4(), classification="operational", prior_history=history)
    assert invocation.conversation_context == history
