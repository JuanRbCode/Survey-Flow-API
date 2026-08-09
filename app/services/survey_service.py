from playwright.async_api import async_playwright
import random
from faker import Faker

fake = Faker('es')

async def open_survey(browser, url: str):
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded")
        title = await page.title()
        return {
            "title": title,
            "url": url
        }
    finally:
        await page.close()

async def inspect_survey(browser, url: str):
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(1500) # Reducido para mayor velocidad

        start_button = page.get_by_role("button", name="Empezar")
        if await start_button.count() > 0:
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
        await page.close()

async def process_survey_async(browser, url: str):
    # Usamos el navegador global pasado por parámetro
    page = await browser.new_page()

    try:
        # 1. Cargar la página de forma rápida con domcontentloaded
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
        start_btn = page.get_by_role("button", name="Empezar")
        if await start_btn.count() > 0 and await start_btn.is_visible():
            await start_btn.click()
            await page.wait_for_timeout(500)

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
        await page.close()