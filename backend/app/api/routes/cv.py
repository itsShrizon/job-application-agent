from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

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


class CVSourceUpdate(BaseModel):
    latex: str


class CVChatRequest(BaseModel):
    latex: str
    message: str


@router.get("/files")
def api_list_cv_files():
    from app.core.config import settings
    output_dir = settings.output_path / "cv"
    if not output_dir.exists():
        return {"files": []}
    files = []
    for tex in sorted(output_dir.glob("*.tex"), key=lambda f: f.stat().st_mtime, reverse=True):
        pdf = tex.with_suffix(".pdf")
        files.append({
            "filename": tex.name,
            "stem": tex.stem,
            "has_pdf": pdf.exists(),
            "modified": tex.stat().st_mtime,
        })
    return {"files": files}


@router.get("/source/{filename}")
def api_get_cv_source(filename: str):
    from app.core.config import settings
    tex_path = settings.output_path / "cv" / filename
    if not tex_path.exists() or tex_path.suffix != ".tex":
        raise HTTPException(status_code=404, detail={"error_code": "CV_SOURCE_NOT_FOUND", "message": f"No .tex file named '{filename}'."})
    return {"filename": filename, "latex": tex_path.read_text(encoding="utf-8")}


@router.put("/source/{filename}")
def api_save_cv_source(filename: str, body: CVSourceUpdate):
    from app.core.config import settings
    tex_path = settings.output_path / "cv" / filename
    if not tex_path.exists() or tex_path.suffix != ".tex":
        raise HTTPException(status_code=404, detail={"error_code": "CV_SOURCE_NOT_FOUND", "message": f"No .tex file named '{filename}'."})
    tex_path.write_text(body.latex, encoding="utf-8")
    return {"saved": True, "filename": filename}


@router.post("/recompile/{filename}")
def api_recompile_cv(filename: str):
    from app.core.config import settings
    from app.core.template_engine import compile_latex
    tex_path = settings.output_path / "cv" / filename
    if not tex_path.exists() or tex_path.suffix != ".tex":
        raise HTTPException(status_code=404, detail={"error_code": "CV_SOURCE_NOT_FOUND", "message": f"No .tex file named '{filename}'."})
    try:
        pdf_path = compile_latex(tex_path)
        return {"pdf_path": str(pdf_path), "filename": pdf_path.name}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail={"error_code": "RECOMPILE_FAILED", "message": str(e)})


@router.post("/chat/{filename}")
def api_cv_chat(filename: str, body: CVChatRequest):
    from app.core.llm_chains import invoke_cv_edit_chain
    try:
        modified_latex = invoke_cv_edit_chain(latex=body.latex, instruction=body.message)
        return {"latex": modified_latex}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error_code": "AI_EDIT_FAILED", "message": str(e)})
