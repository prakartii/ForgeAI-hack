"""
Hardening Subsystem.
CLAUDE.md §18:
Adversarial challenge ladders to test generalization of ABI fixes across increasing difficulty:
Level 1: ZIP variation
Level 2: ZIP + name variation
Level 3: ZIP + name + narrative style variation
Level 4: multiple proxies + incomplete evidence
"""

from app.hardening.engine import run_hardening_ladder

__all__ = ["run_hardening_ladder"]
