from loop_maker.storage import SessionStore

def test_memory_store_keeps_session_and_iteration_history():
    store = SessionStore(":memory:")
    store.start_session("s-1", "agent-x", "objective", "BASIC")
    store.record_iteration("s-1", 1, "first output", False, {"tokens": 12}, {"attempt": 1})
    store.record_error("s-1", 1, "B", "needs another attempt")
    store.finish_session("s-1", "CIRCUIT_BROKEN", False, "first output")

    session = store.get_session("s-1")
    assert session is not None
    assert session["status"] == "CIRCUIT_BROKEN"
    assert session["iterations"][0]["usage"] == {"tokens": 12}
    assert session["iterations"][0]["accepted"] is False
    assert session["errors"][0]["code"] == "B"
    store.close()

def test_converged_session_requires_an_accepted_iteration():
    import pytest
    store = SessionStore(":memory:")
    store.start_session("s-2", "agent-x", "objective", "BASIC")
    with pytest.raises(ValueError):
        store.finish_session("s-2", "COMPLETED", True, "output")
