from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
from app.routes.automation import router

# Variables globales para el navegador compartido
_playwright_instance = None
browser_instance = None
async def get_global_browser():
    """Inicializa el navegador global una sola vez de forma perezosa (Lazy Singleton)"""
    global _playwright_instance, browser_instance
    if browser_instance is None:
        print("🚀 Iniciando navegador global en memoria...")
        _playwright_instance = await async_playwright().start()
        browser_instance = await _playwright_instance.chromium.launch(
            headless=False,  # Ponlo en False temporalmente para que veas cómo abre
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage", 
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled", # <-- ESTO ES CLAVE PARA OCULTAR QUE ES UN BOT
                "--start-maximized"
            ]
        )
    return browser_instance

app = FastAPI(
    title="Survey Automation API",
    description="API optimizada con navegador global",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200", 
        "http://127.0.0.1:4200", 
        "https://juanrbcode.github.io/Survey-Flow/",
        "https://juanrbcode.github.io/Survey-Flow",
        "https://juanrbcode.github.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    router,
    prefix="/api/automation",
    tags=["Automation"]
)

@app.get("/")
def root():
    return {"message": "Survey Automation API con navegador global activa"}