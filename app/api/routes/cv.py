from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.cv import CVGenerateRequest, CVGenerateResponse
from app.services import cv_service

router = APIRouter(prefix="/api/cv", tags=["CV"])


@router.post("/generate", response_model=CVGenerateResponse)
def api_generate_cv(req: CVGenerateRequest):
    try:
        if req.job_id:
            result = cv_service.generate_cv(job_id=req.job_id, template=req.template)
        else:
            result = cv_service.generate_cv_from_file(file_path=req.job_file, template=req.template)
    except KeyError as e:
        raise HTTPException(status_code=404, detail={
            "error_code": "JOB_NOT_FOUND",
            "message": str(e),
            "suggestion": "Check the job_id or run jobfind first.",
        })
    except FileNotFoundError as e:
        raise HTTPException(status_code=422, detail={
            "error_code": "FILE_NOT_FOUND",
            "message": str(e),
        })
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail={
            "error_code": "GENERATION_FAILED",
            "message": str(e),
        })
    return CVGenerateResponse(**result)


@router.get("/{job_id}/download")
def api_download_cv(job_id: str):
    from app.core.config import settings
    output_dir = settings.output_path / "cv"
    matches = list(output_dir.glob(f"*{job_id}*.pdf")) if output_dir.exists() else []

    if not matches:
        pdfs = list(output_dir.glob("*.pdf")) if output_dir.exists() else []
        for pdf in pdfs:
            if _job_id_matches_file(job_id, pdf):
                matches.append(pdf)

    if not matches:
        raise HTTPException(status_code=404, detail={
            "error_code": "CV_NOT_FOUND",
            "message": f"No CV PDF found for job ID '{job_id}'.",
            "suggestion": "Generate a CV first with POST /api/cv/generate.",
        })

    return FileResponse(path=str(matches[0]), media_type="application/pdf", filename=matches[0].name)


def _job_id_matches_file(job_id: str, pdf_path: Path) -> bool:
    try:
        from app.core.csv_manager import get_job_by_id
        job = get_job_by_id(job_id)
        company = job.get("company_name", "").replace(" ", "")
        return company.lower() in pdf_path.stem.lower()
    except KeyError:
        return False
