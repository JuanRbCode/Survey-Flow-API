from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import json
from app.services.qr_service import read_qr
from app.services.survey_service import process_survey_async
from app.services.proxy_service import load_proxy_pool
from pydantic import BaseModel
import sqlite3


router = APIRouter()

@router.post("/process-all")
async def process_all_qrs(
    files: List[UploadFile] = File(default=[]),
    scanned_texts: Optional[str] = Form(default=None)
):
    from app.main import get_global_browser
    browser_instance = await get_global_browser()
    results = []
    
    # Cargar el pool de proxies desde el archivo local proxy_list.txt
    proxy_pool = load_proxy_pool()

    # Procesar elementos que provienen de archivos de imagen subidos/fotos de QR
    queue_items = []
    for file in files:
        contents = await file.read()
        url = read_qr(contents)
        if url:
            queue_items.append({"name": file.filename, "url": url})
        else:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": "No se encontró un código QR válido en la imagen."
            })

    # Procesar textos directos enviados por el escáner de la cámara
    if scanned_texts:
        try:
            texts_list = json.loads(scanned_texts)
            for idx, text_url in enumerate(texts_list):
                if text_url:
                    queue_items.append({"name": f"Escáner Cámara #{idx+1}", "url": text_url})
        except Exception:
            pass

    # Ejecutar automatización en paralelo o secuencia controlada rotando proxies
    for index, item in enumerate(queue_items):
        current_proxy = proxy_pool[index % len(proxy_pool)]
        try:
            survey_res = await process_survey_async(browser_instance, item["url"], proxy_config=current_proxy)
            results.append({
                "filename": item["name"],
                "url": item["url"],
                "success": True,
                "result": survey_res
            })
        except Exception as e:
            error_msg = str(e) if str(e) else repr(e)
            results.append({
                "filename": item["name"],
                "url": item["url"],
                "success": False,
                "error": error_msg
            })

    return {
        "total_processed": len(results),
        "results": results
    }



class PersonaCreate(BaseModel):
    nombres: str
    apellidos: str
    email: str
    telefono: str
    dni: str

# 2. Crear la ruta POST para registrar la persona
@router.post("/personas", summary="Registrar nueva persona")
def crear_persona(persona: PersonaCreate):
    try:
        conn = sqlite3.connect("personas.db") # O la ruta donde tengas tu BD
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO personas (nombres, apellidos, email, telefono, dni)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            persona.nombres, 
            persona.apellidos, 
            persona.email, 
            persona.telefono, 
            persona.dni
        ))
        
        conn.commit()
        conn.close()
        
        return {"status": "success", "message": "¡Persona registrada correctamente en la base de datos!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, error=str(e), detail=f"Error al guardar en la base de datos: {str(e)}")