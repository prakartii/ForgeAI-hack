import os
import yaml
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter

router = APIRouter(prefix="/abis", tags=["Behavior ABI"])


@router.get("", response_model=List[Dict[str, Any]])
def list_abis() -> List[Dict[str, Any]]:
    """
    Returns available Behavior ABI definitions loaded from specification files.
    """
    abis = []
    # Search for foundational YAML specs in the repository's abis directory
    abis_dir = Path(__file__).resolve().parent.parent.parent.parent / "abis"
    if abis_dir.exists():
        for yaml_file in abis_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        abis.append({
                            "source_file": yaml_file.name,
                            "abi_version": data.get("abi_version", yaml_file.stem),
                            "description": data.get("description", ""),
                            "prohibited": data.get("prohibited", []),
                            "permitted": data.get("permitted", []),
                            "invariants": data.get("invariants", []),
                        })
            except Exception:
                continue
    return abis
