"""
Trace Subsystem.
CLAUDE.md §9 & §10:
Single common trace wrapper used by every agent and tool call.
Envelope formatting, correlation linking (PRISM session <-> run <-> failure <-> ABI), and causal graph collection.
"""

from app.traces.wrapper import TraceRecorder, new_id

__all__ = ["TraceRecorder", "new_id"]
