from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.abi.compiler import compile_fairness_abi, compile_workflow_abi
from app.db.session import get_db
from app.models.abi import ABIRuleModel, BehaviorABIModel
from app.schemas.abi import BehaviorABI

router = APIRouter(prefix="/abis", tags=["Behavior ABI"])


@router.get("", response_model=List[BehaviorABI])
def list_abis(db: Session = Depends(get_db)) -> List[BehaviorABIModel]:
    """
    Returns compiled Behavior ABIs. Compiles the fairness and workflow
    specs from /abis on first call (idempotent) so the endpoint reflects
    real, persisted, executable ABIs rather than static YAML text.
    """
    compile_fairness_abi(db)
    compile_workflow_abi(db)
    return db.query(BehaviorABIModel).filter_by(is_active=True).all()


@router.get("/{abi_version}/rules", response_model=List[Dict[str, Any]])
def get_abi_rules(abi_version: str, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    rules = db.query(ABIRuleModel).filter_by(abi_version=abi_version).all()
    return [
        {
            "rule_id": r.rule_id,
            "rule_type": r.rule_type,
            "clause": r.clause,
            "executable_action": r.executable_action,
            "severity": r.severity,
        }
        for r in rules
    ]
