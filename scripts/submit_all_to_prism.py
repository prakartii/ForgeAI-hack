"""
Bulk-submits the full v1 claim population to PRISM as real trajectories.

CLAUDE.md's own PRISM guidance says NOT to do this routinely (budget trace
volume; only submit curated demo scenarios + the hardening ladder day to
day) -- this script exists for a deliberate, one-time bulk submission the
user explicitly asked for, not as part of the regular dev loop.

Operates on the SAME database your backend server uses (DATABASE_URL /
default backend/failurefoundry.db), so:
  - Run `python ../scripts/load_demo_data.py` first if you haven't loaded
    the dataset yet.
  - STOP your uvicorn server before running this (Ctrl+C) to avoid two
    processes writing SQLite at once, then restart it after.

Resumable: safe to Ctrl+C and rerun. It skips claims that already have a
v1 AgentRun, and skips runs that already have a prism_session_id, so a
partial run just picks up where it left off rather than re-submitting or
duplicating rows.

Usage:
    cd backend && python ../scripts/submit_all_to_prism.py [--limit N]
"""
import argparse
import sys
import time
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agents.orchestrator import run_claim_pipeline  # noqa: E402
from app.db.session import SessionLocal, init_db  # noqa: E402
from app.models.domain import ClaimModel, PolicyModel  # noqa: E402
from app.models.trace import AgentRunModel, TraceEventModel  # noqa: E402
from app.prism import get_prism_client  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N claims (for a dry run).")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    client = get_prism_client()

    if not client.is_configured:
        print("PRISM is not configured (PRISM_API_KEY / PRISM_PROJECT_ID missing from backend/.env).")
        print("Nothing was submitted -- this script refuses to fabricate trajectory ids.")
        return 1

    claim_ids = [row[0] for row in db.query(ClaimModel.claim_id).order_by(ClaimModel.id.asc()).all()]
    if args.limit:
        claim_ids = claim_ids[: args.limit]
    total = len(claim_ids)
    print(f"PRISM configured: project {client.settings.prism_project_id} @ {client.settings.prism_base_url}")
    print(f"Submitting v1 pipeline runs for {total} claims (resumable -- rerun if interrupted).\n")

    pipelines_run = 0
    runs_submitted = 0
    runs_already_done = 0
    submit_failures = 0
    start = time.time()

    for i, claim_id in enumerate(claim_ids, start=1):
        existing_v1_runs = (
            db.query(AgentRunModel).filter_by(claim_id=claim_id, agent_version="v1").all()
        )
        if not existing_v1_runs:
            claim = db.query(ClaimModel).filter_by(claim_id=claim_id).one()
            policy = db.query(PolicyModel).filter_by(policy_id=claim.policy_id).one()
            run_claim_pipeline(db, claim, policy, agent_version="v1", scenario_id=claim_id)
            pipelines_run += 1
            existing_v1_runs = (
                db.query(AgentRunModel).filter_by(claim_id=claim_id, agent_version="v1").all()
            )

        for run in existing_v1_runs:
            if run.prism_session_id:
                runs_already_done += 1
                continue
            events = db.query(TraceEventModel).filter_by(run_id=run.run_id).all()
            trajectory_id = client.submit_agent_run(run, events)
            if trajectory_id:
                run.prism_session_id = trajectory_id
                db.commit()
                runs_submitted += 1
            else:
                submit_failures += 1

        if i % 50 == 0 or i == total:
            elapsed = time.time() - start
            print(f"[{i}/{total}] claims processed | pipelines run: {pipelines_run} | "
                  f"submitted: {runs_submitted} | already done: {runs_already_done} | "
                  f"submit failures: {submit_failures} | elapsed: {elapsed:.0f}s")

    print("\nDone.")
    print(f"Pipelines executed this run: {pipelines_run}")
    print(f"Trajectories submitted this run: {runs_submitted}")
    print(f"Runs already submitted from a prior pass: {runs_already_done}")
    print(f"Submissions PRISM rejected/failed: {submit_failures}")

    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
