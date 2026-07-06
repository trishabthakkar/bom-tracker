from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.upload import UploadedFile
from app.models.user import User
from app.schemas.graph import (
    AffectedNodesResponse,
    DependencyPathsResponse,
    GraphBuildResponse,
    GraphEdgeRead,
    GraphStatisticsResponse,
)
from app.services.bom_parser import BomParserError, parse_bom_file
from app.services.dependency_graph import (
    build_dependency_graph,
    get_affected_children,
    get_affected_parents,
    get_dependency_paths,
    get_graph_edges,
    get_graph_statistics,
)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.post("/build/{upload_id}", response_model=GraphBuildResponse)
def build_graph(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GraphBuildResponse:
    upload, graph = _load_graph(upload_id, db, current_user)

    return GraphBuildResponse(
        upload_id=upload.id,
        filename=upload.original_filename,
        nodes=sorted(str(node) for node in graph.nodes),
        edges=[GraphEdgeRead.model_validate(edge.__dict__) for edge in get_graph_edges(graph)],
    )


@router.get("/{upload_id}/parents/{part_number}", response_model=AffectedNodesResponse)
def read_affected_parents(
    upload_id: int,
    part_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AffectedNodesResponse:
    _, graph = _load_graph(upload_id, db, current_user)

    return AffectedNodesResponse(
        upload_id=upload_id,
        part_number=part_number,
        nodes=get_affected_parents(graph, part_number),
    )


@router.get("/{upload_id}/children/{part_number}", response_model=AffectedNodesResponse)
def read_affected_children(
    upload_id: int,
    part_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AffectedNodesResponse:
    _, graph = _load_graph(upload_id, db, current_user)

    return AffectedNodesResponse(
        upload_id=upload_id,
        part_number=part_number,
        nodes=get_affected_children(graph, part_number),
    )


@router.get("/{upload_id}/paths", response_model=DependencyPathsResponse)
def read_dependency_paths(
    upload_id: int,
    source: str = Query(..., min_length=1),
    target: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DependencyPathsResponse:
    _, graph = _load_graph(upload_id, db, current_user)

    return DependencyPathsResponse(
        upload_id=upload_id,
        source=source,
        target=target,
        paths=get_dependency_paths(graph, source, target),
    )


@router.get("/{upload_id}/stats", response_model=GraphStatisticsResponse)
def read_graph_statistics(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GraphStatisticsResponse:
    _, graph = _load_graph(upload_id, db, current_user)
    statistics = get_graph_statistics(graph)

    return GraphStatisticsResponse(
        upload_id=upload_id,
        node_count=statistics.node_count,
        edge_count=statistics.edge_count,
        root_count=statistics.root_count,
        leaf_count=statistics.leaf_count,
        has_cycles=statistics.has_cycles,
    )


def _load_graph(upload_id: int, db: Session, current_user: User):
    upload = db.get(UploadedFile, upload_id)

    if upload is None or upload.uploader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded BOM file was not found.",
        )

    if upload.file_extension not in {".csv", ".xlsx"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV and XLSX uploads can be converted into dependency graphs.",
        )

    try:
        parsed = parse_bom_file(upload.storage_path)
    except BomParserError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return upload, build_dependency_graph(parsed.rows)
