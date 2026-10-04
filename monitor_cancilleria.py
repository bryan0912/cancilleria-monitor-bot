"""Wrapper de compatibilidad.

Permite ejecutar el proyecto con `python monitor_cancilleria.py`
desde la raíz, delegando toda la lógica al paquete `src.monitor`.
"""

from src.monitor.main import main

if __name__ == "__main__":
    main()