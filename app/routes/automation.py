import asyncio
from fastapi import APIRouter, UploadFile, File
from app.services.qr_service import read_qr
from app.services.survey_service import _process_survey_sync

router = APIRouter()

# --------------------------------------------------
# Endpoint Maestro (Usado por Angular para envío masivo)
# --------------------------------------------------

@router.post("/process-all")
async def process_all_qrs(files: list[UploadFile] = File(...)):
    results = []

    for file in files:
        contents = await file.read()
        
        # 1. Leer el QR
        url = read_qr(contents)
        if not url:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": "No se encontró un código QR válido."
            })
            continue

        # 2. Rellenar la encuesta en un hilo independiente (To avoid Windows asyncio subprocess issues)
        try:
            survey_res = await asyncio.to_thread(_process_survey_sync, url)
            results.append({
                "filename": file.filename,
                "url": url,
                "success": True,
                "result": survey_res
            })
        except Exception as e:
            error_msg = str(e) if str(e) else repr(e)
            results.append({
                "filename": file.filename,
                "url": url,
                "success": False,
                "error": error_msg
            })

    return {
        "total_processed": len(files),
        "results": results
    }



# --------------------------------------------------
# Endpoints Individuales (Existentes)
# --------------------------------------------------
@router.post("/qr")
async def read_qr_endpoint(file: UploadFile = File(...)):
    image_bytes = await file.read()
    url = read_qr(image_bytes)

    if not url:
        raise HTTPException(
            status_code=400,
            detail="No se encontró un código QR válido."
        )

    return {"success": True, "url": url}


@router.post("/open-survey")
def open_survey_endpoint(url: str):

    try:

        result = open_survey(url)

        return {
            "success": True,
            "result": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/inspect")
def inspect_survey_endpoint(url: str):

    try:

        result = inspect_survey(url)

        return {
            "success": True,
            "result": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/fill-survey")
def fill_survey_endpoint(url: str):
    try:
        result = fill_survey(url)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )