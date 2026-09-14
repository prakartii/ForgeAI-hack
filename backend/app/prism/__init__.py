"""
PRISM Integration Subsystem (Isolated Layer).
CLAUDE.md §2, §21 & §31:
Architectural Boundary:
PRISM = observes, evaluates, diagnoses, proves.
FailureFoundry = compiles, enforces, hardens, regression-tests, gates.

This module houses the client adapter for the official PRISM SDK (blockconvey-monitor)
and HTTP ingestion. It must remain strictly decoupled from FailureFoundry core business logic.
"""

from app.prism.client import PrismClient, get_prism_client

__all__ = ["PrismClient", "get_prism_client"]
