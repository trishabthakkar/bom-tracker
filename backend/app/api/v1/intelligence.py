from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.upload import UploadedFile
from app.models.user import User
from app.schemas.impact import ImpactReportRequest, StructuredImpactReport
from app.services.bom_parser import BomParserError, parse_bom_file
from app.services.dependency_graph import build_dependency_graph
from app.services.eco_parser import EngineeringChangeParser
from app.services.intelligence_layer import IntelligenceLayer

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.post("/impact-report", response_model=StructuredImpactReport)
def generate_impact_report(
    payload: ImpactReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StructuredImpactReport:
    upload = db.get(UploadedFile, payload.bom_upload_id)

    if upload is None or upload.uploader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded BOM file was not found.",
        )

    if upload.file_extension not in {".csv", ".xlsx"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV and XLSX uploads can be used for impact analysis.",
        )

    try:
        parsed_bom = parse_bom_file(upload.storage_path)
    except BomParserError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    parsed_eco = EngineeringChangeParser().parse_text(payload.eco_text)
    graph = build_dependency_graph(parsed_bom.rows)

    return IntelligenceLayer().generate_report(graph=graph, eco=parsed_eco)
