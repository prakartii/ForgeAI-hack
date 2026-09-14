from sqlalchemy import inspect
from app.db.session import engine, init_db, SessionLocal


def test_database_initialization():
    """
    Test that init_db creates all required tables in SQLite.
    Verifies domain, trace, scenario, failure, ABI, and evaluation tables.
    """
    init_db()
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    expected_tables = [
        "policies",
        "claims",
        "documents",
        "evidence",
        "workflow_states",
        "ground_truth",
        "agent_runs",
        "trace_events",
        "scenarios",
        "counterfactual_pairs",
        "failures",
        "mutations",
        "behavior_abis",
        "abi_rules",
        "regression_tests",
        "evaluation_results",
        "release_gate_results",
    ]

    for table in expected_tables:
        assert table in table_names, f"Expected table '{table}' not found in database"


def test_session_lifecycle():
    """
    Test that SessionLocal can open and close cleanly.
    """
    session = SessionLocal()
    try:
        assert session.is_active
    finally:
        session.close()
