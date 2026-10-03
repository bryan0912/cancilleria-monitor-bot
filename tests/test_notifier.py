"""Tests para el envío de alertas a Telegram."""

import sys
from unittest.mock import MagicMock, patch

import requests


def _cargar_modulo(monkeypatch, dry_run: bool = False):
    """Configura envs válidas y re-importa el módulo."""
    monkeypatch.setenv("CEDULA", "1234567890")
    monkeypatch.setenv("CORREO", "test@example.com")
    monkeypatch.setenv("FECHA_EXPEDICION", "01/01/2020")
    monkeypatch.setenv("BOT_TOKEN", "fake-token")
    monkeypatch.setenv("CHAT_ID", "123456")
    monkeypatch.setenv("DRY_RUN", "true" if dry_run else "false")

    if "monitor_cancilleria" in sys.modules:
        del sys.modules["monitor_cancilleria"]

    import monitor_cancilleria

    return monitor_cancilleria


def test_dry_run_no_llama_a_telegram(monkeypatch):
    """En modo DRY_RUN no debe llamarse a requests.post."""
    modulo = _cargar_modulo(monkeypatch, dry_run=True)

    with patch("monitor_cancilleria.requests.post") as mock_post:
        resultado = modulo.enviar_alerta_telegram("mensaje de prueba")

    assert resultado is True
    mock_post.assert_not_called()


def test_envio_exitoso_llama_a_requests(monkeypatch):
    """Cuando DRY_RUN=false, debe llamarse a requests.post."""
    modulo = _cargar_modulo(monkeypatch, dry_run=False)

    with patch("monitor_cancilleria.requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            raise_for_status=lambda: None,
        )
        resultado = modulo.enviar_alerta_telegram("hola")

    assert resultado is True
    mock_post.assert_called_once()
    # Verificamos que se llamó con el token correcto en la URL
    called_url = mock_post.call_args.args[0]
    assert "fake-token" in called_url
    assert "sendMessage" in called_url


def test_error_http_devuelve_false(monkeypatch):
    """Si Telegram responde con error, debe devolver False sin explotar."""
    modulo = _cargar_modulo(monkeypatch, dry_run=False)

    with patch("monitor_cancilleria.requests.post") as mock_post:
        mock_post.side_effect = requests.RequestException("boom")
        resultado = modulo.enviar_alerta_telegram("hola")

    assert resultado is False
