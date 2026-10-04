"""Tests para el envío de alertas a Telegram."""

from unittest.mock import MagicMock, patch

import requests


def test_dry_run_no_llama_a_telegram():
    """En modo DRY_RUN no debe llamarse a requests.post."""
    from src.monitor import config, notifier

    original = config.DRY_RUN
    config.DRY_RUN = True
    try:
        with patch("src.monitor.notifier.requests.post") as mock_post:
            resultado = notifier.enviar_alerta_telegram("mensaje de prueba")
        assert resultado is True
        mock_post.assert_not_called()
    finally:
        config.DRY_RUN = original


def test_envio_exitoso_llama_a_requests():
    """Cuando DRY_RUN=false, debe llamarse a requests.post."""
    from src.monitor import config, notifier

    original = config.DRY_RUN
    config.DRY_RUN = False
    try:
        with patch("src.monitor.notifier.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                raise_for_status=lambda: None,
            )
            resultado = notifier.enviar_alerta_telegram("hola")

        assert resultado is True
        mock_post.assert_called_once()

        called_url = mock_post.call_args.args[0]
        assert "sendMessage" in called_url
    finally:
        config.DRY_RUN = original


def test_error_http_devuelve_false():
    """Si Telegram responde con error, debe devolver False sin explotar."""
    from src.monitor import config, notifier

    original = config.DRY_RUN
    config.DRY_RUN = False
    try:
        with patch("src.monitor.notifier.requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("boom")
            resultado = notifier.enviar_alerta_telegram("hola")

        assert resultado is False
    finally:
        config.DRY_RUN = original