"""Tests para la validación de variables de entorno."""

import sys
from unittest.mock import patch

import pytest


def test_validar_variables_falla_si_falta_cedula(monkeypatch):
    """Si falta CEDULA, el script debe salir con SystemExit."""

    # Borramos las variables del entorno
    for var in ["CEDULA", "CORREO", "FECHA_EXPEDICION", "BOT_TOKEN", "CHAT_ID"]:
        monkeypatch.delenv(var, raising=False)

    # Mockeamos load_dotenv ANTES de importar el módulo,
    # parcheando la referencia que el propio módulo usará.
    # Truco: parcheamos "dotenv.load_dotenv" antes de que el módulo lo importe.
    with patch("dotenv.load_dotenv", return_value=None):
        if "monitor_cancilleria" in sys.modules:
            del sys.modules["monitor_cancilleria"]

        import monitor_cancilleria

        with pytest.raises(SystemExit):
            monitor_cancilleria.validar_variables()
