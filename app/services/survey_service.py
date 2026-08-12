from playwright.async_api import async_playwright
import random
from faker import Faker

fake = Faker('es')

# Lista de agentes de usuario para simular diferentes dispositivos y clientes reales
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
]

def _get_context_options(proxy_config: dict = None):
    """Genera opciones de contexto aleatorias para evitar la detección por huella de dispositivo"""
    chosen_user_agent = random.choice(USER_AGENTS)
    options = {
        "user_agent": chosen_user_agent,
        "viewport": {"width": random.choice([1280, 1366, 1920, 375]), "height": random.choice([800, 768, 1080, 667])},
        "device_scale_factor": random.choice([1, 2]),
        "is_mobile": "Mobile" in chosen_user_agent or "iPhone" in chosen_user_agent
    }
    if proxy_config:
        options["proxy"] = proxy_config
    return options

async def open_survey(browser, url: str, proxy_config: dict = None):
    context_options = _get_context_options(proxy_config)
    context = await browser.new_context(**context_options)
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded")
        title = await page.title()
        return {
            "title": title,
            "url": url
        }
    finally:
        await context.close()

async def inspect_survey(browser, url: str, proxy_config: dict = None):
    context_options = _get_context_options(proxy_config)
    context = await browser.new_context(**context_options)
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(1500) # Reducido para mayor velocidad

        start_button = page.locator("button[data-testid='link-text-0']")
        if await start_button.count() > 0 and await start_button.is_visible():
            await start_button.click()
            await page.wait_for_timeout(1000)

        fields = page.locator("input, select, textarea, button")
        result = []
        count = await fields.count()

        for i in range(count):
            element = fields.nth(i)
            tag = await element.evaluate("(element) => element.tagName.toLowerCase()")
            result.append({
                "tag": tag,
                "type": await element.get_attribute("type"),
                "name": await element.get_attribute("name"),
                "id": await element.get_attribute("id"),
                "testid": await element.get_attribute("data-testid"),
                "value": await element.get_attribute("value"),
                "placeholder": await element.get_attribute("placeholder"),
                "text": await element.inner_text()
            })

        title = await page.title()
        return {
            "title": title,
            "url": url,
            "fields": result
        }
    finally:
        await context.close()

async def process_survey_async(browser, url: str, proxy_config: dict = None):
    # Creamos un contexto con huella de dispositivo única e independiente
    context_options = _get_context_options(proxy_config)
    context = await browser.new_context(**context_options)
    page = await context.new_page()

    try:
        # 1. Cargar la página de forma rápida con domcontentloaded
        # --- PRUEBA DE IP (Opcional solo para verificar) ---
        ip_page = await context.new_page()
        await ip_page.goto("https://api.ipify.org?format=json")
        print("IP actual del contexto:", await ip_page.content())
        await ip_page.close() # Cerramos la pestaña de la IP
        # --------------------------------------------------

        await page.goto(url, wait_until="domcontentloaded")
        

        # 2. VERIFICACIÓN TEMPRANA
        already_done_selectors = [
            "[data-testid='thanks-title']",
            ".thanks-page_title__2_3sP",
            "h1:has-text('ya no se encuentra disponible')",
            "text=Esta encuesta ya fue completada",
            "text=Gracias por participar"
        ]

        for selector in already_done_selectors:
            loc = page.locator(selector)
            if await loc.count() > 0 and await loc.first.is_visible():
                raise Exception("Encuesta ya realizada o QR caducado")

        # Paso 0: Botón "Empezar"
        # Paso 0: Botón "Empezar" usando su data-testid exacto
        start_btn = page.locator("button[data-testid='link-text-0']")
        try:
            await start_btn.wait_for(state="visible", timeout=5000)
            await start_btn.click()
            await page.wait_for_timeout(800)
        except Exception:
            # Plan B por si el testid varía, buscando por texto directamente
            fallback_btn = page.locator("button", has_text="Empezar")
            if await fallback_btn.count() > 0 and await fallback_btn.is_visible():
                await fallback_btn.click()
                await page.wait_for_timeout(800)

        # Re-verificación
        for selector in already_done_selectors:
            loc = page.locator(selector)
            if await loc.count() > 0 and await loc.first.is_visible():
                raise Exception("Encuesta ya realizada o QR caducado")

        # Paso 0.5: Pregunta NPS (10)
        nps_score_10 = page.locator("div.score_numeric .sliderLayout_number__2mDvw", has_text="10").first
        if await nps_score_10.count() > 0 and await nps_score_10.is_visible():
            await nps_score_10.click()
            await page.get_by_role("button", name="Siguiente").click()
            await page.wait_for_timeout(500)

        # Paso 1: Textarea
        textarea = page.locator("textarea[data-testid^='comment']")
        if await textarea.count() > 0:
            await page.get_by_role("button", name="Siguiente").click()
            await page.wait_for_timeout(500)

        # Paso 2: Escala Numérica
        score_10 = page.locator(".sliderLayout_number__2mDvw", has_text="10")
        if await score_10.count() > 0:
            await score_10.first.click()
            await page.get_by_role("button", name="Siguiente").click()
            await page.wait_for_timeout(500)

        # Paso 3: Matriz de Preguntas
        rows = page.locator("tr.ant-table-row")
        rows_count = await rows.count()
        if rows_count > 0:
            for i in range(rows_count):
                excelente_cell = rows.nth(i).locator("div[data-testid$='10']")
                if await excelente_cell.count() > 0:
                    await excelente_cell.click()
            
            await page.get_by_role("button", name="Siguiente").click()
            await page.wait_for_timeout(500)

        # Paso 4: Pregunta Boolean ("Sí")
        btn_si = page.locator("button.boolean-card", has_text="Sí")
        if await btn_si.count() > 0:
            await btn_si.click()
            await page.wait_for_timeout(500)

        # Paso 5: Formulario de Datos Personales
        try:
            select_doc = page.locator("select[data-testid='form0']")
            await select_doc.wait_for(state="visible", timeout=3000)
            await select_doc.select_option(value="D.N.I.")
        except Exception:
            raise Exception("Encuesta ya realizada o formulario no disponible")

        await page.locator("input[placeholder='Número de Documento *']").fill(str(random.randint(10000000, 99999999)))
        await page.locator("input[placeholder='Número de teléfono *']").fill(f"9{random.randint(10000000, 99999999)}")
        await page.locator("input[placeholder='Nombre *']").fill(fake.first_name())
        await page.locator("input[placeholder='Apellido *']").fill(fake.last_name())
        await page.locator("input[placeholder='Email *']").fill(fake.email())

        fecha_input = page.locator("input[placeholder='Fecha de nacimiento *']")
        await fecha_input.click()
        await page.wait_for_timeout(200)

        btn_today = page.locator("button.smile-datepicker__day--today")
        if await btn_today.count() > 0:
            await btn_today.click()
            await page.wait_for_timeout(200)

        checkboxes = page.locator("input[type='checkbox']")
        cb_count = await checkboxes.count()
        for i in range(cb_count):
            cb = checkboxes.nth(i)
            if not await cb.is_checked():
                await cb.check(force=True)

        # Paso 6: Enviar
        send_btn = page.locator("button[data-testid='send-button']")
        await send_btn.click()
        await page.wait_for_timeout(1000)

        return {"status": "completed"}

    finally:
        await context.close()