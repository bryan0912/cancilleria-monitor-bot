"""Configuración y validación de variables de entorno."""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# ---------- Cargar .env desde la raíz del proyecto ----------
# Buscamos el .env en la raíz del repo, no en src/monitor/
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ_PROYECTO / ".env")

# ---------- Variables de entorno ----------
CEDULA = os.getenv("CEDULA")
CORREO = os.getenv("CORREO")
FECHA_EXPEDICION = os.getenv("FECHA_EXPEDICION")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

# ---------- Constantes ----------
URL_INICIO = (
    "https://tramites.cancilleria.gov.co/apostillalegalizacion/solicitud/inicio.aspx"
)

# En CI (GitHub Actions) no hay pantalla, por eso headless=True
HEADLESS = os.getenv("CI", "false").lower() == "true"

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def validar_variables() -> None:
    """Valida que todas las variables requeridas estén presentes.

    Si falta alguna, registra el error y sale con código 1.
    """
    requeridas = {
        "CEDULA": CEDULA,
        "CORREO": CORREO,
        "FECHA_EXPEDICION": FECHA_EXPEDICION,
        "BOT_TOKEN": BOT_TOKEN,
        "CHAT_ID": CHAT_ID,
    }
    faltantes = [k for k, v in requeridas.items() if not v]
    if faltantes:
        log.error(f"Faltan variables de entorno: {', '.join(faltantes)}")
        sys.exit(1)