"""
Behavior ABI Subsystem.
CLAUDE.md §1 & §16:
The central differentiator: Behavior ABI compiler, schema validation, and specification repository.
Turns diagnosed failures and PRISM evidence into versioned, executable behavioral contracts.
"""

from app.abi.compiler import compile_fairness_abi, compile_workflow_abi

__all__ = ["compile_fairness_abi", "compile_workflow_abi"]
