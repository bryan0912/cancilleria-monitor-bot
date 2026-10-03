import os
import sys
import time
import logging


import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ---------- Configuración ----------
load_dotenv()

CEDULA = os.getenv("CEDULA")
CORREO = os.getenv("CORREO")
FECHA_EXPEDICION = os.getenv("FECHA_EXPEDICION")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

URL_INICIO = "https://tramites.cancilleria.gov.co/apostillalegalizacion/solicitud/inicio.aspx"

# Si GitHub Actions detecta que estamos en CI, headless=True
HEADLESS = os.getenv("CI", "false").lower() == "true"

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------- Validación de variables ----------
def validar_variables():
    faltantes = [k for k, v in {
        "CEDULA": CEDULA,
        "CORREO": CORREO,
        "FECHA_EXPEDICION": FECHA_EXPEDICION,
        "BOT_TOKEN": BOT_TOKEN,
        "CHAT_ID": CHAT_ID,
    }.items() if not v]
    if faltantes:
        log.error(f"Faltan variables de entorno: {', '.join(faltantes)}")
        sys.exit(1)


# ---------- Telegram ----------
def enviar_alerta_telegram(mensaje: str) -> bool:
    if DRY_RUN:
        log.info(f"[DRY_RUN] Mensaje que se habría enviado:\n{mensaje}")
        return True

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=15)
        r.raise_for_status()
        log.info("Alerta enviada a Telegram correctamente.")
        return True
    except requests.RequestException as e:
        log.error(f"Error enviando a Telegram: {e}")
        return False


# ---------- Scraper ----------
def verificar_tramite() -> bool:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=0 if HEADLESS else 300)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        page.set_default_timeout(30000)

        try:
            log.info("1. Accediendo a la página inicial...")
            page.goto(URL_INICIO, timeout=60000)

            log.info("2. Seleccionando 'Documentos electrónicos con firma digital'...")
            primer_select = page.locator("select").nth(0)
            primer_select.wait_for(state="visible")
            primer_select.select_option(label="Documentos electrónicos con firma digital")

            log.info("3. Esperando lista de trámites...")
            page.wait_for_timeout(3000)

            log.info("4. Seleccionando 'Certificado de Antecedentes Judiciales'...")
            segundo_select = page.locator("#contenido_ddlTipoDocumento")
            segundo_select.wait_for(state="attached")
            option_value = segundo_select.locator(
                "option", has_text="Certificado de Antecedentes Judiciales"
            ).get_attribute("value")

            page.evaluate(
                """(val) => {
                    const select = document.querySelector('#contenido_ddlTipoDocumento');
                    select.value = val;
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                }""",
                option_value,
            )
            page.wait_for_timeout(3000)

            log.info("4b. Cerrando ventana emergente si aparece...")
            try:
                cerrar_btn = page.locator("text='Cerrar X'").or_(page.locator("text='Cerrar'"))
                cerrar_btn.wait_for(state="visible", timeout=5000)
                cerrar_btn.click()
            except PWTimeout:
                log.info("No se detectó popup.")

            page.wait_for_timeout(1000)

            log.info("5. Aceptando privacidad y continuando...")
            page.evaluate(
                """() => {
                    const chk = document.querySelector('#contenido_cbAcepto')
                        || document.querySelector("input[type='checkbox']");
                    if (chk) {
                        chk.checked = true;
                        chk.dispatchEvent(new Event('change', { bubbles: true }));
                        chk.dispatchEvent(new Event('click', { bubbles: true }));
                    }
                }"""
            )
            page.wait_for_timeout(500)

            btn_continuar = page.locator(
                "input[id*='btnContinuar'], input[value*='Continuar']"
            ).first
            btn_continuar.scroll_into_view_if_needed()
            page.evaluate("btn => btn.click()", btn_continuar.element_handle())

            # --- PASO 1 ---
            log.info("6. Formulario de Datos Personales...")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)

            inputs = page.locator(
                "input:not([type='hidden']):not([type='submit'])"
                ":not([type='button']):not([type='checkbox']):not([type='radio'])"
            )

            campo_cedula = inputs.nth(0)
            campo_cedula.wait_for(state="visible")
            campo_cedula.scroll_into_view_if_needed()
            campo_cedula.click()
            campo_cedula.fill(CEDULA)

            campo_correo = inputs.nth(1)
            campo_correo.scroll_into_view_if_needed()
            campo_correo.click()
            campo_correo.fill(CORREO)

            campo_confirmar = inputs.nth(2)
            campo_confirmar.scroll_into_view_if_needed()
            campo_confirmar.click()
            campo_confirmar.fill(CORREO)

            page.wait_for_timeout(1000)
            log.info("Avanzando al Paso 2...")
            btn1 = page.locator(
                "input[id*='btnContinuar'], input[value*='Continuar']"
            ).first
            btn1.scroll_into_view_if_needed()
            page.evaluate("btn => btn.click()", btn1.element_handle())

            # --- PASO 2 ---
            log.info("7. Fines y fecha de expedición...")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)

            rbt_si = page.locator(
                "input[type='radio'][value='1'], "
                "input[id*='rblFinesMigratorios_0'], "
                "input[id*='rbtFines_0'], input[type='radio']"
            ).first
            rbt_si.wait_for(state="attached")
            rbt_si.scroll_into_view_if_needed()
            page.evaluate(
                """el => {
                    el.checked = true;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('click', { bubbles: true }));
                }""",
                rbt_si.element_handle(),
            )
            page.wait_for_timeout(1500)

            chk_acepto = page.locator("input[type='checkbox']").first
            chk_acepto.wait_for(state="attached")
            chk_acepto.scroll_into_view_if_needed()
            page.evaluate(
                """el => {
                    el.checked = true;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('click', { bubbles: true }));
                }""",
                chk_acepto.element_handle(),
            )
            page.wait_for_timeout(1500)

            campo_fecha = page.locator(
                "input[id*='txtFechaExpedicion'], "
                "input[id*='FechaExpedicion'], input[type='text']"
            ).first
            campo_fecha.wait_for(state="visible")
            campo_fecha.scroll_into_view_if_needed()
            campo_fecha.click()
            campo_fecha.fill(FECHA_EXPEDICION)
            page.wait_for_timeout(500)

            log.info("Avanzando al Paso 3...")
            btn2 = page.locator(
                "input[id*='btnContinuar'], input[value*='Continuar']"
            ).first
            btn2.scroll_into_view_if_needed()
            page.evaluate("btn => btn.click()", btn2.element_handle())

            # --- PASO 3 ---
            log.info("8. Seleccionando país de destino (ESPAÑA)...")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)

            try:
                page.evaluate(
                    """() => {
                        const select = document.querySelector("select[id*='ddlPais'], select[id*='Pais']");
                        if (select) {
                            const option = Array.from(select.options)
                                .find(opt => opt.text.toUpperCase().includes("ESPAÑA"));
                            if (option) {
                                select.value = option.value;
                                select.dispatchEvent(new Event('change', { bubbles: true }));
                                if (window.jQuery) {
                                    window.jQuery(select).trigger("chosen:updated");
                                    window.jQuery(select).trigger("change");
                                }
                            }
                        }
                    }"""
                )
                page.wait_for_timeout(1000)

                caja_pais = page.locator(".chosen-single, [id*='ddlPais_chosen']").first
                if caja_pais.is_visible():
                    caja_pais.click(force=True)
                    page.wait_for_timeout(500)
                    page.keyboard.type("España", delay=100)
                    page.wait_for_timeout(500)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(1000)
            except Exception as ex:
                log.warning(f"Aviso al seleccionar país: {ex}")

            log.info("Clic en Continuar final...")
            btn_final = page.locator(
                "input[id*='btnContinuar'], input[value*='Continuar'], "
                "button:has-text('Continuar')"
            ).first
            btn_final.scroll_into_view_if_needed()
            page.evaluate("btn => btn.click()", btn_final.element_handle())

            log.info("Esperando respuesta del sistema...")
            page.wait_for_timeout(7000)

                       
            # ---------- Evaluación ----------
            texto = ""
            for _ in range(5):
                try:
                    texto = page.inner_text("body").lower()
                    if texto:
                        break
                except Exception:
                    page.wait_for_timeout(2000)

            mensajes_error = [
                "no se encuentra disponible",
                "fuera de servicio",
                "intente más tarde",
                "se ha presentado un error",
                "no hay citas disponibles",
            ]

            

            # --- Evaluación del resultado ---
            hay_error = any(msg in texto for msg in mensajes_error)

            # Palabras que SOLO aparecen cuando el sitio avanzó a la pantalla de pago
            # (confirmadas con el debug del sitio real)
            señales_exito = ["forma de pago", "crear solicitud", "datos documento"]
            exito = any(s in texto for s in señales_exito) and not hay_error

            if exito:
                mensaje = (
                    "✅ <b>TRÁMITE DISPONIBLE</b>\n\n"
                    "El certificado de antecedentes para España está abierto "
                    "y listo para continuar con el pago.\n"
                    f"Entra: {URL_INICIO}"
                )
                log.info(">>> DISPONIBLE <<<")
            else:
                mensaje = (
                    "❌ <b>TRÁMITE NO DISPONIBLE</b>\n\n"
                    "El sistema sigue fuera de servicio o sin disponibilidad "
                    "para España. Intenta más tarde.\n"
                    f"URL: {URL_INICIO}"
                )
                log.info(">>> NO DISPONIBLE <<<")

            # Siempre enviamos mensaje a Telegram (éxito o no)
            enviar_alerta_telegram(mensaje)
            return exito

        except Exception as e:
            log.exception(f"Error durante el recorrido: {e}")
            return False
        finally:
            try:
                browser.close()
            except Exception:
                pass


# ---------- Entrypoint ----------
if __name__ == "__main__":
    validar_variables()
    log.info("Iniciando verificación de Cancillería...")
    if verificar_tramite():
        log.info("Verificación completada: disponible.")
    else:
        log.info("Verificación completada: no disponible.")