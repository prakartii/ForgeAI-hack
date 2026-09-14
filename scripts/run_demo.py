"""
FailureFoundry / FairClaim — one-command demo (CLAUDE.md §27, §30).

Reproduces the full locked lifecycle end to end against a fresh, isolated
database, entirely offline (no server, no browser required):

    BUILD -> ATTACK -> PRISM OBSERVE -> EVALUATE -> DIAGNOSE ->
    COMPILE BEHAVIOR ABI -> ENFORCE -> FIX/HARDEN -> PRISM PROVE ->
    REGRESSION TEST -> RELEASE GATE

Usage:
    cd backend && python ../scripts/run_demo.py
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.abi.compiler import compile_fairness_abi, compile_workflow_abi  # noqa: E402
from app.agents.adjudication import PROXY_FIELDS, run_adjudication  # noqa: E402
from app.db.base import Base  # noqa: E402
import app.models  # noqa: E402,F401
from app.enforcement.engine import resolve_enforcement  # noqa: E402
from app.enforcement.runner import run_claim_with_enforcement  # noqa: E402
from app.failures.scanner import scan_claims, scan_fairness_groups  # noqa: E402
from app.gates.engine import evaluate_release_gate  # noqa: E402
from app.hardening.engine import run_hardening_ladder  # noqa: E402
from app.metrics.engine import compute_metrics  # noqa: E402
from app.models.domain import ClaimModel, PolicyModel  # noqa: E402
from app.models.scenario import CounterfactualPairModel  # noqa: E402
from app.prism import get_prism_client  # noqa: E402
from app.regression.engine import register_regression_test, run_regression_suite  # noqa: E402
from app.scenarios.csv_loader import load_dataset, verify_oracle_consistency  # noqa: E402


def header(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def claim_and_policy(db, claim_id):
    claim = db.query(ClaimModel).filter_by(claim_id=claim_id).one()
    policy = db.query(PolicyModel).filter_by(policy_id=claim.policy_id).one()
    return claim, policy


def main() -> int:
    engine = create_engine("sqlite:///./demo_run.db")
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()

    # --- BUILD ---
    header("STAGE 1/11 · BUILD — synthetic claims environment")
    summary = load_dataset(db)
    oracle_check = verify_oracle_consistency(db)
    print(f"Loaded: {summary}")
    print(f"Deterministic oracle check: {oracle_check['checked']} claims, "
          f"{len(oracle_check['mismatches'])} mismatches against dataset ground truth.")

    # --- ATTACK: reproduce the primary fairness demo scenario CFG_001 ---
    header("STAGE 2/11 · ATTACK — matched counterfactual fairness pair (group CFG_001)")
    pairs = db.query(CounterfactualPairModel).filter_by(group_id="CFG_001").all()
    variant_ids = sorted({pairs[0].baseline_claim_id} | {p.counterfactual_claim_id for p in pairs})
    print("Holding constant: policy, peril, verified damage, deductible, coverage limit, evidence.")
    print("Varying only: claimant name, PIN code, state, city, narrative style.\n")
    v1_outcomes = {}
    for claim_id in variant_ids:
        claim, policy = claim_and_policy(db, claim_id)
        result = run_adjudication(claim, policy)  # v1: no prohibited_fields
        v1_outcomes[claim_id] = (result["decision"], result["payout"])
        print(f"  v1 {claim_id}: decision={result['decision']:<9} payout=INR {result['payout']}")

    disagreement = len(set(v1_outcomes.values())) > 1
    print(f"\n  {'⚠ FAILURE REPRODUCED' if disagreement else 'no disagreement'}: "
          f"{len(set(v1_outcomes.values()))} distinct outcome(s) across identical legitimate facts.")

    # --- PRISM OBSERVE ---
    header("STAGE 3/11 · PRISM OBSERVE — evidence capture")
    prism_status = get_prism_client().status()
    print(f"PRISM status: {prism_status['status']} — {prism_status['message']}")

    # --- EVALUATE / DIAGNOSE ---
    header("STAGE 4-5/11 · EVALUATE & DIAGNOSE — failure detection engine")
    fairness_failures = scan_fairness_groups(db, agent_version="v1")
    claim_sample = [row[0] for row in db.query(ClaimModel.claim_id).limit(80).all()]
    other_failures = scan_claims(db, claim_sample, agent_version="v1")
    print(f"Fairness failures (all 25 counterfactual groups): {len(fairness_failures)}")
    print(f"Workflow failures (sample of {len(claim_sample)} claims): {len(other_failures['WORKFLOW'])}")
    print(f"Evidence failures: {len(other_failures['EVIDENCE'])}")
    print(f"Decision-correctness failures: {len(other_failures['DECISION_CORRECTNESS'])}")

    all_failures = fairness_failures + sum(other_failures.values(), [])
    for f in all_failures:
        abi_version = "fair_adjudication_v1" if f.failure_type == "FAIRNESS" else "fair_workflow_v1"
        register_regression_test(db, f, abi_version_introduced=abi_version)

    # --- COMPILE BEHAVIOR ABI ---
    header("STAGE 6/11 · COMPILE BEHAVIOR ABI")
    fairness_abi = compile_fairness_abi(db, source_failure_id=fairness_failures[0].failure_id if fairness_failures else None)
    workflow_abi = compile_workflow_abi(db)
    print(f"Compiled {fairness_abi.abi_version}: prohibits {fairness_abi.prohibited_factors}")
    print(f"Compiled {workflow_abi.abi_version}: requires verified explanation before customer communication")

    # --- ENFORCE ---
    header("STAGE 7/11 · ENFORCE — runtime context sanitization, before/after proof")
    from app.agents.adjudication import build_adjudication_context

    claim, policy = claim_and_policy(db, variant_ids[0])
    before_context = build_adjudication_context(claim, policy)
    enforcement = resolve_enforcement(db)
    after_context = build_adjudication_context(claim, policy, prohibited_fields=enforcement["prohibited_fields"])
    print(f"BEFORE enforcement, context keys: {sorted(before_context.keys())}")
    print(f"AFTER  enforcement, context keys: {sorted(after_context.keys())}")
    removed = set(before_context) - set(after_context)
    print(f"Removed by the fairness ABI: {sorted(removed)}")

    v2_outcomes = {}
    for claim_id in variant_ids:
        c, p = claim_and_policy(db, claim_id)
        result = run_claim_with_enforcement(db, c, p, scenario_id=claim_id, counterfactual_group="CFG_001")
        v2_outcomes[claim_id] = (result["adjudication"]["decision"], result["adjudication"]["payout"])
        print(f"  v2 {claim_id}: decision={result['adjudication']['decision']:<9} "
              f"payout=INR {result['adjudication']['payout']}  status={result['status']}")
    print(f"\n  {'✓ FIXED' if len(set(v2_outcomes.values())) == 1 else '✗ still inconsistent'}: "
          f"{len(set(v2_outcomes.values()))} distinct outcome(s) after enforcement.")

    # --- FIX/HARDEN ---
    header("STAGE 8/11 · FIX/HARDEN — adversarial difficulty ladder (L1-L4)")
    ladder_before = run_hardening_ladder(db, agent_version="v1")
    ladder_after = run_hardening_ladder(db, agent_version="v2", prohibited_fields=enforcement["prohibited_fields"])
    print(f"Challenge robustness BEFORE: {ladder_before['challenge_robustness']:.0%}")
    print(f"Challenge robustness AFTER:  {ladder_after['challenge_robustness']:.0%}")

    # --- PRISM PROVE ---
    header("STAGE 9/11 · PRISM PROVE — before/after metrics")
    metrics_v1 = compute_metrics(db, candidate_version="v1", prohibited_fields=None, workflow_enforce=False,
                                  claim_ids=claim_sample)
    metrics_v2 = compute_metrics(db, candidate_version="v2", prohibited_fields=enforcement["prohibited_fields"],
                                  workflow_enforce=True, claim_ids=claim_sample)
    for key in ["pairwise_consistency", "workflow_compliance", "evidence_completeness", "challenge_robustness"]:
        print(f"  {key:<22} v1={metrics_v1[key]:.0%}   v2={metrics_v2[key]:.0%}")

    # --- REGRESSION TEST ---
    header("STAGE 10/11 · REGRESSION TEST")
    regression_results = run_regression_suite(
        db, candidate_version="v2",
        prohibited_fields=enforcement["prohibited_fields"], workflow_enforce=True,
    )
    passing = sum(1 for t in regression_results if t.still_passing)
    print(f"Regression suite: {passing}/{len(regression_results)} passing against v2.")

    # --- RELEASE GATE ---
    header("STAGE 11/11 · RELEASE GATE")
    full_metrics = compute_metrics(db, candidate_version="v2", prohibited_fields=enforcement["prohibited_fields"],
                                    workflow_enforce=True)
    gate_result = evaluate_release_gate(db, candidate_version="v2", metrics=full_metrics)
    print(f"CANDIDATE v2 → {gate_result.status}")
    for clause, detail in gate_result.failure_summary.items():
        mark = "✓" if detail["passed"] else "✗"
        print(f"  {mark} {clause}: {detail['detail']}")

    header("DONE")
    print("PRISM finds and explains the failure. FailureFoundry turns that diagnosis")
    print("into an executable behavioral contract that prevents recurrence.")
    print(f"\n(Demo database written to backend/demo_run.db — delete it to start clean.)")

    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
