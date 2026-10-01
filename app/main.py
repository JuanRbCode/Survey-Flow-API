from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
from app.routes.automation import router
from app.services.db_service import init_db

_playwright_instance = None
browser_instance = None

async def get_global_browser():
    global _playwright_instance, browser_instance
    if browser_instance is None:
        print("🚀 Iniciando navegador global en memoria...")
        _playwright_instance = await async_playwright().start()
        browser_instance = await _playwright_instance.chromium.launch(
            headless=True,  # Cambiar a False si deseas visualizar el navegador localmente
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage", 
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
    return browser_instance

app = FastAPI(
    title="Survey Automation API (Local + DB + Proxy)",
    description="API con soporte para base de datos de personas, rotación de proxies y doble entrada (QR foto / texto directo)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://juanrbcode.github.io/Survey-Flow/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()
    print("📦 Base de datos local de personas inicializada correctamente.")

app.include_router(
    router,
    prefix="/api/automation",
    tags=["Automation"]
)

@app.get("/api/health")
def health_check():
    return {"status": "online"}

@app.get("/")
def root():
    return {"message": "Survey Automation API local activa con éxito"}