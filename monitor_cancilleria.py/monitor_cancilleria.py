import os
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Cargar variables desde el archivo .env si existe localmente
load_dotenv()

CEDULA = os.getenv("CEDULA")
CORREO = os.getenv("CORREO")
FECHA_EXPEDICION = os.getenv("FECHA_EXPEDICION")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
URL_INICIO = "https://tramites.cancilleria.gov.co/apostillalegalizacion/solicitud/inicio.aspx"

def enviar_alerta_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")

def verificar_tramite():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=600)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("1. Accediendo a la página inicial...")
            page.goto(URL_INICIO, timeout=60000)

            # --- PANTALLA INICIAL ---
            print("2. Seleccionando 'Documentos electrónicos con firma digital'...")
            primer_select = page.locator("select").nth(0)
            primer_select.wait_for(state="visible", timeout=30000)
            primer_select.select_option(label="Documentos electrónicos con firma digital")

            print("3. Aguardando a que cargue la lista de trámites...")
            page.wait_for_timeout(3000)

            print("4. Seleccionando 'Certificado de Antecedentes Judiciales - Policía Nacional'...")
            segundo_select = page.locator("#contenido_ddlTipoDocumento")
            segundo_select.wait_for(state="attached", timeout=30000)

            option_value = segundo_select.locator("option", has_text="Certificado de Antecedentes Judiciales").get_attribute("value")

            page.evaluate(f"""
                const select = document.querySelector('#contenido_ddlTipoDocumento');
                select.value = '{option_value}';
                select.dispatchEvent(new Event('change', {{ bubbles: true }}));
            """)
            page.wait_for_timeout(3000)

            # --- MANEJO DEL POPUP / VENTANA EMERGENTE ---
            print("4b. Cerrando la ventana de advertencia informativa...")
            try:
                cerrar_btn = page.locator("text='Cerrar X'").or_(page.locator("text='Cerrar'"))
                cerrar_btn.wait_for(state="visible", timeout=5000)
                cerrar_btn.click()
                print("Ventana emergente cerrada exitosamente.")
            except Exception:
                print("No se detectó la ventana emergente o se cerró automáticamente.")

            page.wait_for_timeout(1000)

            # --- ACEPTAR PRIVACIDAD Y CONTINUAR ---
            print("5. Aceptando privacidad y haciendo clic en Continuar...")
            page.evaluate("""
                const chk = document.querySelector('#contenido_cbAcepto') || document.querySelector("input[type='checkbox']");
                if (chk) {
                    chk.checked = true;
                    chk.dispatchEvent(new Event('change', { bubbles: true }));
                    chk.dispatchEvent(new Event('click', { bubbles: true }));
                }
            """)
            page.wait_for_timeout(500)

            btn_continuar = page.locator("input[id*='btnContinuar'], input[value*='Continuar']").first
            btn_continuar.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            page.evaluate("btn => btn.click()", btn_continuar.element_handle())

            # --- PASO 1: DATOS PERSONALES ---
            print("6. Esperando la carga del formulario de Datos Personales...")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)

            inputs_visibles = page.locator("input:not([type='hidden']):not([type='submit']):not([type='button']):not([type='checkbox']):not([type='radio'])")
            
            print(" Llenando número de documento...")
            campo_cedula = inputs_visibles.nth(0)
            campo_cedula.wait_for(state="visible", timeout=20000)
            campo_cedula.scroll_into_view_if_needed()
            campo_cedula.click()
            campo_cedula.fill(CEDULA)

            print(" Llenando correo electrónico...")
            campo_correo = inputs_visibles.nth(1)
            campo_correo.scroll_into_view_if_needed()
            campo_correo.click()
            campo_correo.fill(CORREO)

            print(" Confirmando correo electrónico...")
            campo_confirmar = inputs_visibles.nth(2)
            campo_confirmar.scroll_into_view_if_needed()
            campo_confirmar.click()
            campo_confirmar.fill(CORREO)

            page.wait_for_timeout(1000)

            print(" Avanzando al Paso 2 (Clic en Continuar)...")
            btn_cont_paso1 = page.locator("input[id*='btnContinuar'], input[value*='Continuar']").first
            btn_cont_paso1.scroll_into_view_if_needed()
            page.evaluate("btn => btn.click()", btn_cont_paso1.element_handle())

            # --- PASO 2: CONFIRMAR FINES Y FECHA ---
            print("7. Confirmando fines y fecha de expedición...")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)

            # 1. Marcar la opción "Sí" (Radio Button)
            print(" Seleccionando opción 'Sí'...")
            rbt_si = page.locator("input[type='radio'][value='1'], input[id*='rblFinesMigratorios_0'], input[id*='rbtFines_0'], input[type='radio']").first
            rbt_si.wait_for(state="attached", timeout=20000)
            rbt_si.scroll_into_view_if_needed()
            
            # Forzar la selección del Radio Button 'Sí' y disparar sus eventos
            page.evaluate("""
                el => {
                    el.checked = true;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('click', { bubbles: true }));
                }
            """, rbt_si.element_handle())

            page.wait_for_timeout(1500) # Tiempo para que la vista habilite la casilla 'Acepto'

            # 2. Marcar la casilla "Acepto *" (Checkbox)
            print(" Marcando casilla 'Acepto'...")
            chk_acepto = page.locator("input[type='checkbox']").first
            chk_acepto.wait_for(state="attached", timeout=15000)
            chk_acepto.scroll_into_view_if_needed()
            
            page.evaluate("""
                el => {
                    el.checked = true;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('click', { bubbles: true }));
                }
            """, chk_acepto.element_handle())

            page.wait_for_timeout(1500) # Tiempo para que se muestre la caja de Fecha expedición

            # 3. Llenar la Fecha de Expedición
            print(" Llenando Fecha de expedición cédula...")
            campo_fecha = page.locator("input[id*='txtFechaExpedicion'], input[id*='FechaExpedicion'], input[type='text']").first
            campo_fecha.wait_for(state="visible", timeout=15000)
            campo_fecha.scroll_into_view_if_needed()
            campo_fecha.click()
            campo_fecha.fill(FECHA_EXPEDICION)
            page.wait_for_timeout(500)

            # 4. Avanzar al siguiente paso (Clic en Continuar)
            print(" Avanzando al Paso 3 (Clic en Continuar)...")
            btn_cont_paso2 = page.locator("input[id*='btnContinuar'], input[value*='Continuar']").first
            btn_cont_paso2.scroll_into_view_if_needed()
            page.evaluate("btn => btn.click()", btn_cont_paso2.element_handle())

            # --- PASO 3: DATOS DOCUMENTO (ESPAÑA) ---
            print("8. Seleccionando País de Destino (ESPAÑA)...")
            
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)

            try:
                # Asignación directa vía JS y actualización del componente Chosen
                page.evaluate("""
                    () => {
                        const select = document.querySelector("select[id*='ddlPais'], select[id*='Pais']");
                        if (select) {
                            const option = Array.from(select.options).find(opt => opt.text.toUpperCase().includes("ESPAÑA"));
                            if (option) {
                                select.value = option.value;
                                select.dispatchEvent(new Event('change', { bubbles: true }));
                                if (window.jQuery) {
                                    window.jQuery(select).trigger("chosen:updated");
                                    window.jQuery(select).trigger("change");
                                }
                            }
                        }
                    }
                """)
                page.wait_for_timeout(1000)

                # Respaldo por interacción visual si sigue desplegado
                caja_pais = page.locator(".chosen-single, [id*='ddlPais_chosen']").first
                if caja_pais.is_visible():
                    caja_pais.click(force=True)
                    page.wait_for_timeout(500)
                    page.keyboard.type("España", delay=100)
                    page.wait_for_timeout(500)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(1000)

            except Exception as ex_select:
                print(f"Aviso al seleccionar país: {ex_select}")

            # Clic en el botón Continuar final
            print(" Clic en el botón Continuar final...")
            btn_continuar_final = page.locator("input[id*='btnContinuar'], input[value*='Continuar'], button:has-text('Continuar')").first
            btn_continuar_final.scroll_into_view_if_needed()
            
            # Ejecutamos el clic
            page.evaluate("btn => btn.click()", btn_continuar_final.element_handle())

            print(" Esperando a que el sistema procese la solicitud...")
            # Damos una pausa fija para que ASP.NET inicie y complete la navegación
            page.wait_for_timeout(7000)

            # Extraer el contenido de forma segura controlando la navegación activa
            print(" Evaluando respuesta del sistema...")
            contenido = ""
            for _ in range(5):
                try:
                    contenido = page.content().lower()
                    if contenido:
                        break
                except Exception:
                    page.wait_for_timeout(2000)

            mensajes_error = [
                "no se encuentra disponible",
                "fuera de servicio",
                "intente más tarde",
                "se ha presentado un error",
                "no hay citas disponibles"
            ]

            hay_error = any(msg in contenido for msg in mensajes_error)

            if not hay_error and len(contenido) > 0:
                mensaje_exito = (
                    "🚨 ¡ATENCIÓN! EL TRÁMITE DE ANTECEDENTES PARA ESPAÑA YA ESTÁ FUNCIONAL.\n\n"
                    f"Entra de inmediato a completar el trámite: {URL_INICIO}"
                )
                print("\n>>> ¡SISTEMA FUNCIONAL DETECTADO! <<<")
                enviar_alerta_telegram(mensaje_exito)
                return True
            else:
                print("El sistema sigue fuera de servicio o sin disponibilidad al seleccionar España.")

        except Exception as e:
            print(f"Error durante el recorrido: {e}")

        finally:
            browser.close()

    return False

INTERVALO_SEGUNDOS = 300 

print("=== INICIANDO MONITOR VISIBLE DE CANCILLERÍA ===")
while True:
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando verificación...")
    disponible = verificar_tramite()
    if disponible:
        print("Notificación enviada. Deteniendo script.")
        break
    
    time.sleep(INTERVALO_SEGUNDOS)