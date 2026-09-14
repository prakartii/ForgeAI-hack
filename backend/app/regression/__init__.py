"""
Regression Subsystem.
CLAUDE.md §19:
Permanent persistence and continuous re-execution of historical failures as regression obligations.
Ensures previously diagnosed behavioral failures never silently recur in candidate agent versions.
"""

from app.regression.engine import register_regression_test, run_regression_suite

__all__ = ["register_regression_test", "run_regression_suite"]
