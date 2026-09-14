"""
Submits a curated set of the worst fairness/workflow failures to PRISM as
trajectories -- a small, high-signal target set to point a paid
Evaluators Hub evaluator or root-cause engine run at, instead of burning
credits/quota across the full 2,500-claim population.

Selects FAILURE_TYPES failures (default: FAIRNESS, WORKFLOW), most
recent first, that already carry a run_id (CLAUDE.md sec9's trace
correlation -- a failure without a run_id has no execution to submit;
run a scan on the Failures page first if you see "0 candidates").
Skips any whose run already has a prism_session_id.

Usage:
    cd backend && python ../scripts/submit_curated_failures_to_prism.py [--limit N] [--types FAIRNESS,WORKFLOW]
"""
import argparse
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal, init_db  # noqa: E402
from app.models.failure import FailureModel  # noqa: E402
from app.models.trace import AgentRunModel, TraceEventModel  # noqa: E402
from app.prism import get_prism_client  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=20, help="Max number of failures to submit (default 20).")
    parser.add_argument("--types", type=str, default="FAIRNESS,WORKFLOW", help="Comma-separated failure_type values.")
    args = parser.parse_args()
    failure_types = [t.strip().upper() for t in args.types.split(",") if t.strip()]

    init_db()
    db = SessionLocal()
    client = get_prism_client()

    if not client.is_configured:
        print("PRISM is not configured (PRISM_API_KEY / PRISM_PROJECT_ID missing from backend/.env).")
        print("Nothing was submitted -- this script refuses to fabricate trajectory ids.")
        return 1

    candidates = (
        db.query(FailureModel)
        .filter(FailureModel.failure_type.in_(failure_types))
        .filter(FailureModel.run_id.isnot(None))
        .order_by(FailureModel.id.desc())
        .limit(args.limit * 3)  # over-fetch since some will already be submitted
        .all()
    )

    if not candidates:
        print(f"0 candidates found among failure types {failure_types} with a recorded run_id.")
        print("Run a failure scan on the Failures page (or via /api/failures/scan) first.")
        return 1

    print(f"PRISM configured: project {client.settings.prism_project_id} @ {client.settings.prism_base_url}")
    print(f"Found {len(candidates)} candidate failures (types={failure_types}); submitting up to {args.limit}.\n")

    submitted = 0
    already_done = 0
    failed = 0
    results = []

    for failure in candidates:
        if submitted >= args.limit:
            break

        run = db.query(AgentRunModel).filter_by(run_id=failure.run_id).one_or_none()
        if run is None:
            continue

        if run.prism_session_id:
            already_done += 1
            results.append((failure, run.prism_session_id, "already submitted"))
            continue

        events = db.query(TraceEventModel).filter_by(run_id=run.run_id).all()
        trajectory_id = client.submit_agent_run(run, events)
        if trajectory_id:
            run.prism_session_id = trajectory_id
            db.commit()
            submitted += 1
            results.append((failure, trajectory_id, "submitted"))
            print(f"  [{failure.failure_type}] {failure.failure_id} (claim/scenario {failure.scenario_id}) "
                  f"-> trajectory {trajectory_id}")
        else:
            failed += 1
            print(f"  [{failure.failure_type}] {failure.failure_id}: submission failed (see stderr for the SDK's warning)")

    print(f"\nDone. Submitted: {submitted} | already done: {already_done} | failed: {failed}")
    print("\nCurated trajectory IDs (point an Evaluators Hub evaluator or root-cause engine run at these):")
    for failure, trajectory_id, status in results:
        print(f"  {trajectory_id}  <- {failure.failure_type} {failure.failure_id} ({status})")

    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
