from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.qr_service import read_qr
from app.services.survey_service import open_survey, inspect_survey, process_survey_async

router = APIRouter()

def get_browser_instance():
    from app.main import get_global_browser
    return get_global_browser

@router.post("/process-all")
async def process_all_qrs(files: list[UploadFile] = File(...)):
    from app.main import get_global_browser
    browser_instance = await get_global_browser()
    results = []

    # Pool de proxies simulado para la rotación de IPs (puedes añadir más si te dio IPs reales el profesor)
    proxy_pool = [
        None, # Petición limpia por defecto
        # {"server": "http://proxy_ip_1:puerto"},
        # {"server": "http://proxy_ip_2:puerto"}
    ]

    for index, file in enumerate(files):
        contents = await file.read()
        
        url = read_qr(contents)
        if not url:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": "No se encontró un código QR válido."
            })
            continue

        # Asigna un proxy rotativo diferente por cada iteración/encuesta
        current_proxy = proxy_pool[index % len(proxy_pool)]

        try:
            # Se le pasa el proxy_config para cambiar la IP de origen en cada contexto
            survey_res = await process_survey_async(browser_instance, url, proxy_config=current_proxy)
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

@router.post("/qr")
async def read_qr_endpoint(file: UploadFile = File(...)):
    image_bytes = await file.read()
    url = read_qr(image_bytes)

    if not url:
        raise HTTPException(status_code=400, detail="No se encontró un código QR válido.")

    return {"success": True, "url": url}

@router.post("/open-survey")
async def open_survey_endpoint(url: str):
    from app.main import get_global_browser
    browser_instance = await get_global_browser()
    try:
        result = await open_survey(browser_instance, url)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inspect")
async def inspect_survey_endpoint(url: str):
    from app.main import get_global_browser
    browser_instance = await get_global_browser()
    try:
        result = await inspect_survey(browser_instance, url)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))