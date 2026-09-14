from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.enforcement.engine import resolve_enforcement
from app.models.evaluation import RegressionTestModel
from app.regression.engine import run_regression_suite
from app.schemas.evaluation import RegressionTest

router = APIRouter(prefix="/regressions", tags=["Regressions"])


@router.get("", response_model=List[RegressionTest])
def list_regressions(db: Session = Depends(get_db)) -> List[RegressionTestModel]:
    return db.query(RegressionTestModel).order_by(RegressionTestModel.id.desc()).all()


@router.post("/run", response_model=List[RegressionTest])
def run_regressions(candidate_version: str = "v2", db: Session = Depends(get_db)) -> List[RegressionTestModel]:
    """
    Reruns every persisted regression test against `candidate_version`
    using whichever Behavior ABIs are currently compiled and active, and
    updates each test's still_passing status from the real result.
    """
    enforcement = resolve_enforcement(db)
    return run_regression_suite(
        db,
        candidate_version=candidate_version,
        prohibited_fields=enforcement["prohibited_fields"],
        workflow_enforce=enforcement["workflow_enforce"],
    )
