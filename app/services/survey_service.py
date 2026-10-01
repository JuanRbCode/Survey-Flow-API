from playwright.async_api import async_playwright
import random
from app.services.db_service import get_persona_data

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
]

def _get_context_options(proxy_config: dict = None):
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

async def process_survey_async(browser, url: str, proxy_config: dict = None):
    context_options = _get_context_options(proxy_config)
    context = await browser.new_context(**context_options)
    page = await context.new_page()

    try:
        # Navegamos y esperamos a que cargue la red por completo para que los elementos dinámicos aparezcan
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Dar un pequeño respiro obligatorio para estabilizar la vista previa de la SPA
        await page.wait_for_timeout(1500)

        # Función interna para verificar si la encuesta está muerta (expirada o ya hecha) antes de hacer nada
        async def check_survey_status(context_label: str):
            page_content = await page.content()
            
            # 1. Detectar si expiró
            if "ya no se encuentra disponible" in page_content or "La encuesta que desea ver ya no se encuentra disponible" in page_content:
                raise Exception("Encuesta expirada")

            # 2. Detectar si ya fue realizada
            already_done_selectors = [
                "[data-testid='thanks-title']",
                ".thanks-page_title__2_3sP",
                "text=Esta encuesta ya fue completada",
                "text=Gracias por participar"
            ]

            for selector in already_done_selectors:
                loc = page.locator(selector)
                if await loc.count() > 0 and await loc.first.is_visible():
                    raise Exception("Encuesta ya realizada")

        # Primera comprobación estricta al entrar
        await check_survey_status("inicial")

        start_btn = page.locator("button[data-testid='link-text-0']")
        try:
            await start_btn.wait_for(state="visible", timeout=6000)
            await start_btn.click()
            await page.wait_for_timeout(1000)
        except Exception:
            fallback_btn = page.locator("button", has_text="Empezar")
            if await fallback_btn.count() > 0 and await fallback_btn.is_visible():
                await fallback_btn.click()
                await page.wait_for_timeout(1000)

        # Segunda comprobación tras hacer clic en empezar
        await check_survey_status("post-empezar")

        # NPS
        nps_score_10 = page.locator("div.score_numeric .sliderLayout_number__2mDvw", has_text="10").first
        if await nps_score_10.count() > 0 and await nps_score_10.is_visible():
            await nps_score_10.click()
            await page.get_by_role("button", name="Siguiente").click()
            await page.wait_for_timeout(500)

        # Textarea
        textarea = page.locator("textarea[data-testid^='comment']")
        if await textarea.count() > 0:
            await page.get_by_role("button", name="Siguiente").click()
            await page.wait_for_timeout(500)

        # Escala Numérica
        score_10 = page.locator(".sliderLayout_number__2mDvw", has_text="10")
        if await score_10.count() > 0:
            await score_10.first.click()
            await page.get_by_role("button", name="Siguiente").click()
            await page.wait_for_timeout(500)

        # Matriz
        rows = page.locator("tr.ant-table-row")
        rows_count = await rows.count()
        if rows_count > 0:
            for i in range(rows_count):
                excelente_cell = rows.nth(i).locator("div[data-testid$='10']")
                if await excelente_cell.count() > 0:
                    await excelente_cell.click()
            await page.get_by_role("button", name="Siguiente").click()
            await page.wait_for_timeout(500)

        # Boolean
        btn_si = page.locator("button.boolean-card", has_text="Sí")
        if await btn_si.count() > 0:
            await btn_si.click()
            await page.wait_for_timeout(500)

        # Formulario de Datos Personales
        persona = get_persona_data()

        try:
            select_doc = page.locator("select[data-testid='form0']")
            await select_doc.wait_for(state="visible", timeout=4000)
            await select_doc.select_option(value="D.N.I.")
        except Exception:
            raise Exception("Encuesta ya realizada")

        await page.locator("input[placeholder='Número de Documento *']").fill(persona["dni"])
        await page.locator("input[placeholder='Número de teléfono *']").fill(persona["telefono"])
        await page.locator("input[placeholder='Nombre *']").fill(persona["nombres"])
        await page.locator("input[placeholder='Apellido *']").fill(persona["apellidos"])
        await page.locator("input[placeholder='Email *']").fill(persona["email"])

        fecha_input = page.locator("input[placeholder='Fecha de nacimiento *']")
        await fecha_input.click()
        await page.wait_for_timeout(300)

        btn_today = page.locator("button.smile-datepicker__day--today")
        if await btn_today.count() > 0:
            await btn_today.click()
            await page.wait_for_timeout(300)

        checkboxes = page.locator("input[type='checkbox']")
        cb_count = await checkboxes.count()
        for i in range(cb_count):
            cb = checkboxes.nth(i)
            if not await cb.is_checked():
                await cb.check(force=True)

        send_btn = page.locator("button[data-testid='send-button']")
        await send_btn.click()
        await page.wait_for_timeout(1200)

        return {"status": "completed"}

    finally:
        await context.close()