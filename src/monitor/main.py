"""Entrypoint del monitor de Cancillería."""

from src.monitor import config
from src.monitor.scraper import verificar_tramite

log = config.log


def main() -> None:
    """Valida configuración y ejecuta una verificación del trámite."""
    config.validar_variables()
    log.info("Iniciando verificación de Cancillería...")

    disponible = verificar_tramite()

    if disponible:
        log.info("Verificación completada: disponible.")
    else:
        log.info("Verificación completada: no disponible.")


if __name__ == "__main__":
    main()