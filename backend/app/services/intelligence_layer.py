import networkx as nx

from app.schemas.eco import ParsedEngineeringChange
from app.schemas.impact import (
    AffectedAssembly,
    DownstreamRecordImpact,
    RiskAssessment,
    StructuredImpactReport,
    SuggestedUpdate,
)
from app.services.dependency_graph import (
    get_affected_children,
    get_affected_parents,
    get_dependency_paths,
)

HIGH_IMPACT_CHANGE_TYPES = {"replacement", "obsolescence", "removal"}
MEDIUM_IMPACT_CHANGE_TYPES = {"revision", "addition"}


class IntelligenceLayer:
    def generate_report(
        self,
        *,
        graph: nx.DiGraph,
        eco: ParsedEngineeringChange,
    ) -> StructuredImpactReport:
        affected_part = _select_affected_part(eco)
        affected_assemblies = _build_affected_assemblies(graph, affected_part)
        downstream_records = _build_downstream_records(eco, affected_assemblies)
        suggested_updates = _build_suggested_updates(eco, affected_assemblies)
        risk = _assess_risk(eco, affected_assemblies, downstream_records)

        return StructuredImpactReport(
            summary=_build_summary(eco, affected_part, risk.level, affected_assemblies),
            eco=eco,
            affected_part=affected_part,
            effective_date=eco.effective_date,
            affected_assemblies=affected_assemblies,
            downstream_records=downstream_records,
            suggested_updates=suggested_updates,
            risk=risk,
        )


def _select_affected_part(eco: ParsedEngineeringChange) -> str | None:
    return eco.old_part or eco.new_part


def _build_affected_assemblies(
    graph: nx.DiGraph,
    affected_part: str | None,
) -> list[AffectedAssembly]:
    if not affected_part or affected_part not in graph:
        return []

    parents = get_affected_parents(graph, affected_part)
    children = get_affected_children(graph, affected_part)
    paths = [
        path
        for parent in parents
        for path in get_dependency_paths(graph, parent, affected_part)
    ]

    return [
        AffectedAssembly(
            part_number=affected_part,
            affected_parents=parents,
            affected_children=children,
            dependency_paths=paths,
        )
    ]


def _build_downstream_records(
    eco: ParsedEngineeringChange,
    affected_assemblies: list[AffectedAssembly],
) -> list[DownstreamRecordImpact]:
    impacted = bool(affected_assemblies)
    severity = "high" if eco.change_type in HIGH_IMPACT_CHANGE_TYPES and impacted else "medium"
    if not impacted:
        severity = "low"

    records = [
        DownstreamRecordImpact(
            record_type="procurement",
            impact="Approved parts, alternates, supplier mappings, and purchase records may require updates.",
            severity=severity if eco.change_type in HIGH_IMPACT_CHANGE_TYPES else "medium",
        ),
        DownstreamRecordImpact(
            record_type="installation_guides",
            impact="Installation steps and part references should be reviewed for changed hardware.",
            severity=severity,
        ),
        DownstreamRecordImpact(
            record_type="commissioning_procedures",
            impact="Validation checks and startup procedures may need revision if assemblies are affected.",
            severity=severity,
        ),
        DownstreamRecordImpact(
            record_type="service_manuals",
            impact="Spare part references and maintenance instructions should be checked.",
            severity=severity,
        ),
    ]

    if eco.change_type == "addition":
        return records[:2]

    return records


def _build_suggested_updates(
    eco: ParsedEngineeringChange,
    affected_assemblies: list[AffectedAssembly],
) -> list[SuggestedUpdate]:
    updates = [
        SuggestedUpdate(
            area="engineering",
            action="Review affected assemblies and confirm the BOM revision baseline.",
            priority="high" if affected_assemblies else "medium",
        ),
        SuggestedUpdate(
            area="procurement",
            action="Update approved part references and supplier mappings for the changed part.",
            priority="high" if eco.change_type in HIGH_IMPACT_CHANGE_TYPES else "medium",
        ),
        SuggestedUpdate(
            area="documentation",
            action="Review installation, commissioning, and service documents for old/new part references.",
            priority="medium",
        ),
    ]

    if eco.effective_date:
        updates.append(
            SuggestedUpdate(
                area="release_management",
                action=f"Schedule downstream updates before effective date {eco.effective_date.isoformat()}.",
                priority="high",
            )
        )

    return updates


def _assess_risk(
    eco: ParsedEngineeringChange,
    affected_assemblies: list[AffectedAssembly],
    downstream_records: list[DownstreamRecordImpact],
) -> RiskAssessment:
    score = 0
    reasons: list[str] = []

    if eco.change_type in HIGH_IMPACT_CHANGE_TYPES:
        score += 45
        reasons.append(f"Change type '{eco.change_type}' can disrupt existing parts or assemblies.")
    elif eco.change_type in MEDIUM_IMPACT_CHANGE_TYPES:
        score += 25
        reasons.append(f"Change type '{eco.change_type}' requires controlled downstream updates.")
    else:
        score += 10
        reasons.append("Change type is unknown or low confidence.")

    if affected_assemblies:
        parent_count = len(affected_assemblies[0].affected_parents)
        child_count = len(affected_assemblies[0].affected_children)
        score += min(30, parent_count * 8 + child_count * 4)
        reasons.append(f"Dependency graph found {parent_count} affected parent assemblies.")
    else:
        reasons.append("No matching part was found in the dependency graph.")

    high_or_medium_records = [
        record for record in downstream_records if record.severity in {"high", "medium"}
    ]
    if high_or_medium_records:
        score += min(20, len(high_or_medium_records) * 5)
        reasons.append(f"{len(high_or_medium_records)} downstream record categories need review.")

    if eco.effective_date:
        score += 5
        reasons.append("Effective date is present and should drive rollout timing.")

    level = "Low"
    if score >= 70:
        level = "High"
    elif score >= 35:
        level = "Medium"

    return RiskAssessment(level=level, score=min(score, 100), reasons=reasons)


def _build_summary(
    eco: ParsedEngineeringChange,
    affected_part: str | None,
    risk_level: str,
    affected_assemblies: list[AffectedAssembly],
) -> str:
    part_text = affected_part or "an unspecified part"
    assembly_count = (
        len(affected_assemblies[0].affected_parents) if affected_assemblies else 0
    )
    change_type = eco.change_type or "engineering change"

    return (
        f"{change_type.title()} for {part_text} has {risk_level.lower()} risk "
        f"with {assembly_count} affected parent assemblies identified."
    )
