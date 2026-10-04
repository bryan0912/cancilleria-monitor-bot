"""Tests para la validación de variables de entorno."""

import sys
from unittest.mock import patch

import pytest


def test_validar_variables_falla_si_falta_cedula(monkeypatch):
    """Si falta CEDULA, validar_variables debe salir con SystemExit."""
    for var in ["CEDULA", "CORREO", "FECHA_EXPEDICION", "BOT_TOKEN", "CHAT_ID"]:
        monkeypatch.delenv(var, raising=False)

    # Reimportamos el paquete config para que relea las variables
    if "src.monitor.config" in sys.modules:
        del sys.modules["src.monitor.config"]

    # Mockeamos load_dotenv ANTES de importar el módulo
    with patch("dotenv.load_dotenv", return_value=None):
        from src.monitor import config

        # Forzamos a None para simular ausencia total
        config.CEDULA = None
        config.CORREO = None
        config.FECHA_EXPEDICION = None
        config.BOT_TOKEN = None
        config.CHAT_ID = None

        with pytest.raises(SystemExit):
            config.validar_variables()
