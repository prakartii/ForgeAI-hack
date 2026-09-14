"""
Loads the synthetic FairClaim demo dataset into the configured database.

Usage:
    cd backend && python ../scripts/load_demo_data.py
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal, init_db  # noqa: E402
from app.scenarios import load_dataset, verify_oracle_consistency  # noqa: E402


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        summary = load_dataset(db)
        print("Loaded:", summary)

        oracle_check = verify_oracle_consistency(db)
        print(f"Oracle consistency: {oracle_check['checked']} checked, "
              f"{len(oracle_check['mismatches'])} mismatches")
        if oracle_check["mismatches"]:
            print("Mismatched claim ids (first 10):", oracle_check["mismatches"][:10])
    finally:
        db.close()


if __name__ == "__main__":
    main()
