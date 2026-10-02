import os
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

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
    print("Iniciando verificación en Cancillería...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL_INICIO, wait_until="networkidle")
        print("Página cargada exitosamente.")
        enviar_alerta_telegram("🤖 Monitor Cancillería: Verificación ejecutada exitosamente desde GitHub Actions.")
        browser.close()

if __name__ == "__main__":
    verificar_tramite()
