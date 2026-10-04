"""Envío de notificaciones a Telegram."""

import requests

from src.monitor import config

log = config.log


def enviar_alerta_telegram(mensaje: str) -> bool:
    """Envía un mensaje al chat de Telegram configurado.

    Returns:
        True si el mensaje se envió (o si DRY_RUN está activo).
        False si hubo un error.
    """
    if config.DRY_RUN:
        log.info(f"[DRY_RUN] Mensaje que se habría enviado:\n{mensaje}")
        return True

    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
    payload = {"chat_id": config.CHAT_ID, "text": mensaje, "parse_mode": "HTML"}

    try:
        r = requests.post(url, data=payload, timeout=15)
        r.raise_for_status()
        log.info("Alerta enviada a Telegram correctamente.")
        return True
    except requests.RequestException as e:
        log.error(f"Error enviando a Telegram: {e}")
        return False