from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.bom import BomPart
from app.schemas.bom_import import (
    BomDiffPart,
    BomDiffResponse,
    BomDiffSummary,
    BomImportRead,
    BomReplacementCandidate,
    BomRevisionChange,
)
from app.services.bom_importer import get_bom_import, get_import_parts


class BomDiffError(ValueError):
    pass


@dataclass(frozen=True)
class PartSnapshot:
    part_number: str
    description: str | None
    parent_assembly: str | None
    child_assembly: str | None
    revision: str | None


def compare_bom_imports(
    *,
    db: Session,
    user_id: int,
    base_import_id: int,
    target_import_id: int,
) -> BomDiffResponse:
    if base_import_id == target_import_id:
        raise BomDiffError("Select two different BOM imports to compare.")

    base_import = get_bom_import(db=db, import_id=base_import_id, user_id=user_id)
    target_import = get_bom_import(db=db, import_id=target_import_id, user_id=user_id)

    if base_import is None or target_import is None:
        raise BomDiffError("One or both BOM imports were not found.")

    base_parts = _snapshot_parts(get_import_parts(db=db, bom_import_id=base_import.id, user_id=user_id))
    target_parts = _snapshot_parts(get_import_parts(db=db, bom_import_id=target_import.id, user_id=user_id))

    base_numbers = set(base_parts)
    target_numbers = set(target_parts)
    added = sorted(target_numbers - base_numbers)
    removed = sorted(base_numbers - target_numbers)
    common = sorted(base_numbers.intersection(target_numbers))

    revised = [
        _revision_change(base_parts[part_number], target_parts[part_number])
        for part_number in common
        if _part_changed(base_parts[part_number], target_parts[part_number])
    ]
    replacements = _replacement_candidates(
        removed_parts=[base_parts[part_number] for part_number in removed],
        added_parts=[target_parts[part_number] for part_number in added],
    )

    return BomDiffResponse(
        base_import=BomImportRead.model_validate(base_import),
        target_import=BomImportRead.model_validate(target_import),
        summary=BomDiffSummary(
            added_count=len(added),
            removed_count=len(removed),
            revised_count=len(revised),
            replacement_candidate_count=len(replacements),
            unchanged_count=len(common) - len(revised),
        ),
        added_parts=[_diff_part(target_parts[part_number]) for part_number in added],
        removed_parts=[_diff_part(base_parts[part_number]) for part_number in removed],
        revised_parts=revised,
        replacement_candidates=replacements,
    )


def _snapshot_parts(parts: list[BomPart]) -> dict[str, PartSnapshot]:
    snapshots: dict[str, PartSnapshot] = {}
    for part in parts:
        snapshots[part.part_number] = PartSnapshot(
            part_number=part.part_number,
            description=part.description,
            parent_assembly=part.parent_assembly,
            child_assembly=part.child_assembly,
            revision=part.revision,
        )
    return snapshots


def _part_changed(base: PartSnapshot, target: PartSnapshot) -> bool:
    return (
        base.revision != target.revision
        or _clean(base.description) != _clean(target.description)
        or base.parent_assembly != target.parent_assembly
        or base.child_assembly != target.child_assembly
    )


def _revision_change(base: PartSnapshot, target: PartSnapshot) -> BomRevisionChange:
    return BomRevisionChange(
        part_number=base.part_number,
        base_revision=base.revision,
        target_revision=target.revision,
        description_changed=_clean(base.description) != _clean(target.description),
        parent_changed=base.parent_assembly != target.parent_assembly,
        child_changed=base.child_assembly != target.child_assembly,
    )


def _replacement_candidates(
    *,
    removed_parts: list[PartSnapshot],
    added_parts: list[PartSnapshot],
) -> list[BomReplacementCandidate]:
    candidates: list[BomReplacementCandidate] = []
    for removed in removed_parts:
        for added in added_parts:
            score, reason = _replacement_score(removed, added)
            if score >= 0.45:
                candidates.append(
                    BomReplacementCandidate(
                        removed_part=_diff_part(removed),
                        added_part=_diff_part(added),
                        confidence=round(score, 2),
                        reason=reason,
                    )
                )

    return sorted(candidates, key=lambda candidate: candidate.confidence, reverse=True)[:20]


def _replacement_score(removed: PartSnapshot, added: PartSnapshot) -> tuple[float, str]:
    score = 0.0
    reasons: list[str] = []

    if removed.parent_assembly and removed.parent_assembly == added.parent_assembly:
        score += 0.35
        reasons.append("same parent assembly")

    if removed.child_assembly and removed.child_assembly == added.child_assembly:
        score += 0.25
        reasons.append("same child assembly")

    overlap = _description_overlap(removed.description, added.description)
    if overlap >= 0.5:
        score += 0.35
        reasons.append("similar description")
    elif overlap >= 0.25:
        score += 0.2
        reasons.append("partially similar description")

    return min(score, 0.95), ", ".join(reasons) or "related BOM position"


def _description_overlap(base: str | None, target: str | None) -> float:
    base_tokens = _tokens(base)
    target_tokens = _tokens(target)
    if not base_tokens or not target_tokens:
        return 0.0
    return len(base_tokens.intersection(target_tokens)) / len(base_tokens.union(target_tokens))


def _tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    return {
        token
        for token in _clean(value).replace(",", " ").replace("/", " ").split()
        if len(token) > 2
    }


def _diff_part(part: PartSnapshot) -> BomDiffPart:
    return BomDiffPart(
        part_number=part.part_number,
        description=part.description,
        parent_assembly=part.parent_assembly,
        child_assembly=part.child_assembly,
        revision=part.revision,
    )


def _clean(value: str | None) -> str:
    return " ".join((value or "").lower().split())
