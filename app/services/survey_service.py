from playwright.async_api import async_playwright
import random
from faker import Faker

fake = Faker('es')

def open_survey(url: str):

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded"
        )

        title = page.title()

        browser.close()

        return {
            "title": title,
            "url": url
        }

from playwright.sync_api import sync_playwright


def inspect_survey(url: str):

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded"
        )

        # Esperamos a que la aplicación termine de renderizar
        page.wait_for_timeout(3000)

        # ==========================================
        # PANTALLA INICIAL
        # ==========================================

        start_button = page.get_by_role(
            "button",
            name="Empezar"
        )

        if start_button.count() > 0:

            start_button.click()

            # Esperamos a que aparezca la siguiente pantalla
            page.wait_for_timeout(2000)

        # ==========================================
        # INSPECCIONAR ELEMENTOS
        # ==========================================

        fields = page.locator(
            "input, select, textarea, button"
        )

        result = []

        for i in range(fields.count()):

            element = fields.nth(i)

            tag = element.evaluate(
                "(element) => element.tagName.toLowerCase()"
            )

            result.append({
                "tag": tag,
                "type": element.get_attribute("type"),
                "name": element.get_attribute("name"),
                "id": element.get_attribute("id"),
                "testid": element.get_attribute("data-testid"),
                "value": element.get_attribute("value"),
                "placeholder": element.get_attribute("placeholder"),
                "text": element.inner_text()
            })

        title = page.title()

        browser.close()

        return {
            "title": title,
            "url": url,
            "fields": result
        }

def _process_survey_sync(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. Cargar la página
            page.goto(url, wait_until="networkidle")

            # 2. VERIFICACIÓN TEMPRANA Y MÚLTIPLE DE ENCUESTA REALIZADA
            # Se revisan posibles selectores del mensaje de encuesta finalizada o caducada
            already_done_selectors = [
                "[data-testid='thanks-title']",
                ".thanks-page_title__2_3sP",
                "h1:has-text('ya no se encuentra disponible')",
                "text=Esta encuesta ya fue completada",
                "text=Gracias por participar"
            ]

            for selector in already_done_selectors:
                loc = page.locator(selector)
                if loc.count() > 0 and loc.first.is_visible():
                    raise Exception("Encuesta ya realizada o QR caducado")

            # --------------------------------------------------
            # Paso 0: Botón "Empezar" (Si existe)
            # --------------------------------------------------
            start_btn = page.get_by_role("button", name="Empezar")
            if start_btn.count() > 0 and start_btn.is_visible():
                start_btn.click()
                page.wait_for_timeout(1000)

            # Re-verificación tras hacer clic en Empezar
            for selector in already_done_selectors:
                loc = page.locator(selector)
                if loc.count() > 0 and loc.first.is_visible():
                    raise Exception("Encuesta ya realizada o QR caducado")

            # --------------------------------------------------
            # Paso 0.5: Pregunta NPS (Recomendar Tambo+ - Opción 10)
            # --------------------------------------------------
            nps_score_10 = page.locator("div.score_numeric .sliderLayout_number__2mDvw", has_text="10").first
            if nps_score_10.count() > 0 and nps_score_10.is_visible():
                nps_score_10.click()
                page.get_by_role("button", name="Siguiente").click()
                page.wait_for_timeout(1000)

            # --------------------------------------------------
            # Paso 1: Textarea (comentario opcional) + Siguiente
            # --------------------------------------------------
            textarea = page.locator("textarea[data-testid^='comment']")
            if textarea.count() > 0:
                page.get_by_role("button", name="Siguiente").click()
                page.wait_for_timeout(1000)

            # --------------------------------------------------
            # Paso 2: Escala Numérica 0-10 (Amabilidad del Personal)
            # --------------------------------------------------
            score_10 = page.locator(".sliderLayout_number__2mDvw", has_text="10")
            if score_10.count() > 0:
                score_10.first.click()
                page.get_by_role("button", name="Siguiente").click()
                page.wait_for_timeout(1000)

            # --------------------------------------------------
            # Paso 3: Matriz de Preguntas (Seleccionar "Excelente")
            # --------------------------------------------------
            rows = page.locator("tr.ant-table-row")
            rows_count = rows.count()
            if rows_count > 0:
                for i in range(rows_count):
                    excelente_cell = rows.nth(i).locator("div[data-testid$='10']")
                    if excelente_cell.count() > 0:
                        excelente_cell.click()
                
                page.get_by_role("button", name="Siguiente").click()
                page.wait_for_timeout(1000)

            # --------------------------------------------------
            # Paso 4: Pregunta Boolean ("Sí" para participar del sorteo)
            # --------------------------------------------------
            btn_si = page.locator("button.boolean-card", has_text="Sí")
            if btn_si.count() > 0:
                btn_si.click()
                page.wait_for_timeout(1000)

            # --------------------------------------------------
            # Paso 5: Formulario de Datos Personales
            # --------------------------------------------------
            # Si el selector no existe en 3s, lanzamos excepción legible en lugar de esperar 10s
            try:
                select_doc = page.wait_for_selector("select[data-testid='form0']", timeout=3000)
                select_doc.select_option(value="D.N.I.")
            except Exception:
                raise Exception("Encuesta ya realizada o formulario no disponible")

            page.locator("input[placeholder='Número de Documento *']").fill(str(random.randint(10000000, 99999999)))
            page.locator("input[placeholder='Número de teléfono *']").fill(f"9{random.randint(10000000, 99999999)}")
            page.locator("input[placeholder='Nombre *']").fill(fake.first_name())
            page.locator("input[placeholder='Apellido *']").fill(fake.last_name())
            page.locator("input[placeholder='Email *']").fill(fake.email())

            fecha_input = page.locator("input[placeholder='Fecha de nacimiento *']")
            fecha_input.click()
            page.wait_for_timeout(300)

            btn_today = page.locator("button.smile-datepicker__day--today")
            if btn_today.count() > 0:
                btn_today.click()
                page.wait_for_timeout(300)

            checkboxes = page.locator("input[type='checkbox']")
            cb_count = checkboxes.count()
            for i in range(cb_count):
                cb = checkboxes.nth(i)
                if not cb.is_checked():
                    cb.check(force=True)

            # --------------------------------------------------
            # Paso 6: Botón Final de Enviar
            # --------------------------------------------------
            send_btn = page.locator("button[data-testid='send-button']")
            send_btn.click()
            page.wait_for_timeout(2000)

            return {"status": "completed"}

        finally:
            browser.close()