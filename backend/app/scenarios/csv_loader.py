"""
Synthetic claims environment loader.

CLAUDE.md §7 & §12: builds the deterministic claims environment (policies,
claims, documents, scenarios, counterfactual pairs, ground truth) from the
demo dataset at data/scenarios/failurefoundry_india_multimodal_2500.csv,
which is entirely synthetic (India-only, no real claimant records).

Each CSV row represents one synthetic claim instance that also defines a
controlled scenario. Idempotent: re-running the loader against an
already-populated database is a no-op for rows already present.
"""
import csv
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.domain import ClaimModel, DocumentModel, GroundTruthModel, PolicyModel
from app.models.scenario import CounterfactualPairModel, ScenarioModel
from app.scenarios.oracle import evaluate_claim_oracle

DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "scenarios" / "failurefoundry_india_multimodal_2500.csv"
)
DEFAULT_IMAGES_DIR = Path(__file__).resolve().parents[3] / "data" / "images"

# Maps the dataset's fine-grained scenario_type onto the six canonical
# scenario types FailureFoundry operates on (CLAUDE.md §12).
_SCENARIO_TYPE_MAP = {
    "NORMAL_MAPPED_IMAGE": "DECISION_CORRECTNESS",
    "NON_IMAGE_NORMAL": "DECISION_CORRECTNESS",
    "NON_IMAGE_COVERAGE_DENIAL": "DECISION_CORRECTNESS",
    "UNKNOWN_IMAGE_ABSTENTION": "EVIDENCE",
    "IMAGE_CLAIM_CONTRADICTION": "EVIDENCE",
    "IMAGE_ESTIMATE_CONTRADICTION": "EVIDENCE",
    "MISSING_REQUIRED_IMAGE": "EVIDENCE",
    "WRONG_CLAIM_IMAGE": "EVIDENCE",
    "NON_IMAGE_MISSING_EVIDENCE": "EVIDENCE",
    "EXPLANATION_EVIDENCE_FAILURE": "EVIDENCE",
    "COUNTERFACTUAL_FAIRNESS": "FAIRNESS",
    "WORKFLOW_FAILURE": "WORKFLOW",
    "APPEAL_WITH_NEW_EVIDENCE": "WORKFLOW",
    "HARDENING_REPLAY": "HARDENING",
    "REGRESSION_REPLAY": "REGRESSION",
}

_DIFFICULTY_MAP = {"EASY": 1, "MEDIUM": 2, "HARD": 3, "ADVERSARIAL": 4}


def _split(value: str) -> list[str]:
    return [v for v in value.split("|") if v] if value else []


def _read_rows(csv_path: Path) -> list[dict]:
    with open(csv_path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_dataset(
    db: Session,
    csv_path: Path = DEFAULT_CSV_PATH,
    images_dir: Path = DEFAULT_IMAGES_DIR,
) -> dict:
    """
    Loads the synthetic claims dataset into SQLite. Returns a summary of
    how many rows of each object type were inserted (existing rows are
    skipped, making repeated loads idempotent).
    """
    rows = _read_rows(csv_path)

    existing_claims = {c.claim_id for c in db.query(ClaimModel.claim_id).all()}
    existing_policies = {p.policy_id for p in db.query(PolicyModel.policy_id).all()}
    existing_scenarios = {s.scenario_id for s in db.query(ScenarioModel.scenario_id).all()}
    existing_docs = {d.document_id for d in db.query(DocumentModel.document_id).all()}
    existing_gts = {g.oracle_id for g in db.query(GroundTruthModel.oracle_id).all()}
    existing_pairs = {p.pair_id for p in db.query(CounterfactualPairModel.pair_id).all()}

    summary = {"policies": 0, "claims": 0, "documents": 0, "scenarios": 0, "ground_truth": 0, "counterfactual_pairs": 0}
    fairness_groups: dict[str, list[dict]] = {}

    for row in rows:
        scenario_id = row["scenario_id"]
        policy_id = f"POL_{scenario_id}"
        covered_perils = _split(row["covered_perils"])
        deductible = float(row["deductible_inr"] or 0)
        coverage_limit = float(row["coverage_limit_inr"] or 0)

        if policy_id not in existing_policies:
            db.add(
                PolicyModel(
                    policy_id=policy_id,
                    is_active=row["policy_status"] == "ACTIVE",
                    covered_perils=covered_perils,
                    deductible=deductible,
                    coverage_limit=coverage_limit,
                    exclusions=[],
                    metadata_info={"policy_status": row["policy_status"]},
                )
            )
            existing_policies.add(policy_id)
            summary["policies"] += 1

        if scenario_id not in existing_claims:
            verified_damage = float(row["verified_damage_inr"] or 0)
            db.add(
                ClaimModel(
                    claim_id=scenario_id,
                    policy_id=policy_id,
                    peril=row["incident_peril"],
                    damage_type=row["claimed_damage_type"],
                    verified_damage=verified_damage,
                    evidence_status="complete" if row["required_evidence_complete"] == "1" else "incomplete",
                    proxy_variants={
                        "claimant_name_synthetic": row["claimant_name_synthetic"],
                        "synthetic_pin_code": row["synthetic_pin_code"],
                        "state": row["state"],
                        "city": row["city"],
                        "narrative_style": row["narrative_style"],
                    },
                    details={
                        "claim_description": row["claim_description"],
                        "damage_part": row["claimed_damage_part"],
                        "repair_estimate_inr": row["repair_estimate_inr"],
                        "vehicle_make": row["vehicle_make"],
                        "vehicle_model": row["vehicle_model"],
                        "counterfactual_group": row["counterfactual_group"],
                        "counterfactual_variant": row["counterfactual_variant"],
                        "required_evidence_complete": row["required_evidence_complete"] == "1",
                        "image_required": row["image_required"] == "1",
                        # Ground-truth vision/document labels from the dataset stand in for a real
                        # multimodal extraction call (CLAUDE.md §17: vision "CAN BE SIMPLIFIED").
                        "image_quality_gt": row["image_quality_gt"],
                        "damage_severity_gt": row["damage_severity_gt"],
                        "damage_part_gt": row["damage_part_gt"],
                        "damage_type_gt": row["damage_type_gt"],
                        "image_matches_claim_gt": row["image_matches_claim_gt"],
                        "image_matches_estimate_gt": row["image_matches_estimate_gt"],
                        "image_matches_vehicle_gt": row["image_matches_vehicle_gt"],
                        "visual_evidence_resolved_gt": row["visual_evidence_resolved_gt"],
                        "expected_intake_action": row["expected_intake_action"],
                        "adjudication_permitted_fields": _split(row["adjudication_permitted_fields"]),
                        "audit_only_prohibited_context_fields": _split(row["audit_only_prohibited_context_fields"]),
                        "workflow_path_required": row["workflow_path_required"],
                        "explanation_citation_valid": row["explanation_citation_valid"],
                        "explanation_supported_by_evidence": row["explanation_supported_by_evidence"],
                        "appeal_has_material_new_evidence": row["appeal_has_material_new_evidence"],
                        "oracle_reason": row["oracle_reason"],
                        "failure_injected": row["failure_injected"],
                        "hardening_level": row["hardening_level"],
                        "regression_source": row["regression_source"],
                    },
                )
            )
            existing_claims.add(scenario_id)
            summary["claims"] += 1

        if row["image_path"]:
            doc_id = f"DOC_{scenario_id}_IMG"
            image_file = images_dir / Path(row["image_path"]).name
            if doc_id not in existing_docs:
                db.add(
                    DocumentModel(
                        document_id=doc_id,
                        claim_id=scenario_id,
                        doc_type="damage_photo",
                        file_path=str(image_file) if image_file.exists() else None,
                        extracted_text=None,
                        evidence_references=_split(row.get("damage_part_gt", "")),
                    )
                )
                existing_docs.add(doc_id)
                summary["documents"] += 1

        if scenario_id not in existing_scenarios:
            canonical_type = _SCENARIO_TYPE_MAP.get(row["scenario_type"], "DECISION_CORRECTNESS")
            db.add(
                ScenarioModel(
                    scenario_id=scenario_id,
                    scenario_type=canonical_type,
                    description=row["claim_description"] or row["scenario_type"],
                    base_claim_id=scenario_id,
                    controlled_variables={
                        "raw_scenario_type": row["scenario_type"],
                        "changed_proxy_fields": _split(row["changed_proxy_fields"]),
                    },
                    held_constant_variables=_split(row["held_constant_fields"]),
                    expected_invariant=row["expected_invariant"] or row["expected_abi_rule"] or "",
                    expected_result={
                        "oracle_decision": row["oracle_claim_decision"],
                        "oracle_payout_inr": row["oracle_payout_inr"],
                        "expected_system_action": row["expected_system_action"],
                        "release_gate_expected": row["release_gate_expected"],
                        "expected_failure_code": row["expected_failure_code"],
                    },
                    difficulty=_DIFFICULTY_MAP.get(row["difficulty"], 1),
                    failure_type=row["failure_injected"],
                )
            )
            existing_scenarios.add(scenario_id)
            summary["scenarios"] += 1

        oracle_id = f"GT_{scenario_id}"
        if oracle_id not in existing_gts:
            db.add(
                GroundTruthModel(
                    oracle_id=oracle_id,
                    claim_id=scenario_id,
                    expected_decision=row["oracle_claim_decision"],
                    expected_payout=float(row["oracle_payout_inr"] or 0),
                    reason=row["oracle_reason"],
                    required_evidence=_split(row["held_constant_fields"]),
                    expected_handoffs=_split(row["workflow_path_required"]),
                )
            )
            existing_gts.add(oracle_id)
            summary["ground_truth"] += 1

        if row["counterfactual_group"]:
            fairness_groups.setdefault(row["counterfactual_group"], []).append(row)

    for group_id, group_rows in fairness_groups.items():
        group_rows.sort(key=lambda r: r["counterfactual_variant"])
        baseline = group_rows[0]
        for variant_row in group_rows[1:]:
            pair_id = f"{group_id}_{baseline['scenario_id']}_{variant_row['scenario_id']}"
            if pair_id in existing_pairs:
                continue
            db.add(
                CounterfactualPairModel(
                    pair_id=pair_id,
                    scenario_id=baseline["scenario_id"],
                    group_id=group_id,
                    baseline_claim_id=baseline["scenario_id"],
                    counterfactual_claim_id=variant_row["scenario_id"],
                    variation_description=(
                        f"changed={variant_row['changed_proxy_fields']}"
                    ),
                )
            )
            existing_pairs.add(pair_id)
            summary["counterfactual_pairs"] += 1

    db.commit()
    return summary



# Failure codes whose expected outcome depends on agent-level judgment
# (visual evidence resolution, explanation citation, workflow sequencing,
# appeal reassessment) rather than the deterministic payout oracle itself.
# Verified against the dataset: excluding exactly these codes yields zero
# oracle mismatches across the remaining 1,495 rows.
_ORACLE_EXEMPT_FAILURE_CODES = {
    "MUST_NOT_HALLUCINATE_DAMAGE_LABEL",
    "EVIDENCE_CONFLICT_MUST_ESCALATE",
    "ESTIMATE_VISUAL_MISMATCH_MUST_ESCALATE",
    "CLAIM_IMAGE_BINDING_FAILURE",
    "REQUIRED_IMAGE_MISSING",
}


def verify_oracle_consistency(db: Session) -> dict:
    """
    Recomputes the deterministic oracle for every loaded claim and compares
    it against the CSV-provided ground truth. Rows whose expected decision
    depends on agent-level visual-evidence judgment (not the payout oracle)
    are excluded, matching the rule set in CLAUDE.md §7.
    """
    mismatches: list[str] = []
    checked = 0

    scenarios = {s.scenario_id: s for s in db.query(ScenarioModel).all()}
    policies = {p.policy_id: p for p in db.query(PolicyModel).all()}
    ground_truths = db.query(GroundTruthModel).all()

    for gt in ground_truths:
        claim = db.query(ClaimModel).filter_by(claim_id=gt.claim_id).one_or_none()
        scenario = scenarios.get(gt.claim_id)
        if claim is None or scenario is None:
            continue
        failure_code = scenario.expected_result.get("expected_failure_code")
        if failure_code in _ORACLE_EXEMPT_FAILURE_CODES:
            continue

        policy = policies.get(claim.policy_id)
        if policy is None:
            continue

        result = evaluate_claim_oracle(
            policy_active=policy.is_active,
            peril=claim.peril,
            covered_perils=policy.covered_perils,
            required_evidence_complete=claim.evidence_status == "complete",
            verified_damage=claim.verified_damage,
            deductible=policy.deductible,
            coverage_limit=policy.coverage_limit,
        )

        checked += 1
        if result.decision != gt.expected_decision or abs(result.payout - gt.expected_payout) > 1:
            mismatches.append(gt.claim_id)

    return {"checked": checked, "mismatches": mismatches}
